"""
Inference Script Example
===================================
Uses the OpenAI Client to interface with the Groq API (or any OpenAI-compatible API).
Runs through all accessibility tasks, producing reproducible baseline scores.

Requires variables:
    API_BASE_URL (defaults to Groq's OpenAI-compatible endpoint)
    MODEL_NAME
    API_KEY 
    MY_ENV_V4_BENCHMARK
"""

import os
import json
import sys
import textwrap
import asyncio
from typing import List, Optional
from dotenv import load_dotenv

from openai import OpenAI, OpenAIError

from server.environment import A11yEngineerEnv, A11yAction

load_dotenv()  # Load environment variables from .env file

# --- Environment Configurations ---
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama-3.1-8b-instant")
API_KEY = os.environ.get("API_KEY")

BENCHMARK = os.environ.get("MY_ENV_V4_BENCHMARK", "a11yengineer")
MAX_STEPS = 15
TEMPERATURE = 0.3
SUCCESS_SCORE_THRESHOLD = 0.9  # Perfect score required for A11y task success

# ───────────────────── SYSTEM PROMPT ─────────────────────
SYSTEM_PROMPT = textwrap.dedent("""\
You are an expert accessibility engineer agent interacting with a live DOM \
environment. Your goal is to achieve a PERFECT accessibility score (reward = 1.0) \
by finding and fixing ALL accessibility issues.

═══ STRATEGY ═══
1. EXPLORE FIRST — Before modifying anything, use SCREEN_READER on elements and \
TAB through the page to understand the current accessibility state.
2. DIAGNOSE — Analyze the DOM for common violations:
   • Hidden content traps — Visually hidden or off-screen elements that are still \
focusable or readable (Fix: Use 'inert', 'aria-hidden=\"true\"', or 'tabindex=\"-1\"').
   • Missing aria-label / alt text on interactive or image elements
   • Missing aria-live on dynamically-updated regions
   • Keyboard traps (elements that shouldn't be focusable)
   • Missing roles on interactive elements
   • Disconnected dynamic widgets — Search inputs, comboboxes, or toggle buttons 
     that control another element must use 'aria-controls' to point to the ID of 
     the controlled element, and 'aria-expanded' to indicate its state.
3. FIX — Use MODIFY to add the correct ARIA attributes. Fix ALL issues, not just one. \
For boolean attributes like 'inert' or 'disabled', set the value to an empty string \"\".
4. VERIFY — After fixing, use SCREEN_READER / TAB to confirm the fix worked. \
Check if reward increased.
5. ADAPT — If the reward did NOT increase, your diagnosis was wrong. STOP trying to \
'improve' that element with labels or roles. Instead, consider if the element should \
be HIDDEN entirely or if you are missing a structural connection (like aria-describedby). \
Never repeat an action that did not improve the score.

═══ REWARD INTERPRETATION ═══
• reward = 0.0  → No progress yet. Explore more.
• Discovery Reward (+0.2) → You found a bug's location, but haven't FIXED it yet.
• Partial Reward (e.g., 0.5) → EXCELLENT! You fixed PART of a complex issue. 
  DO NOT UNDO your last action. Leave it alone and figure out the missing half 
  (e.g., if you hid an element from screen readers, you might still need to hide 
  its children from keyboard focus using tabindex="-1", or vice versa).
• reward = 1.0  → All issues fixed. Task complete!
• reward DECREASED → Your action made things worse (or you undid a correct fix). Undo it!

═══ AVAILABLE ACTIONS ═══
1. SCREEN_READER — Read an element with a screen reader to check its a11y state.
   {"action_type": "SCREEN_READER", "element_id": "<id>"}
2. TAB — Simulate Tab key to discover the focus/tab order of elements.
   {"action_type": "TAB"}
3. MODIFY — Set an attribute on a DOM element to fix an a11y issue. Use value: \"\" for boolean attributes.
   {"action_type": "MODIFY", "element_id": "<id>", "attribute": "<attr>", "value": "<val>"}
4. CLICK — Click an element (useful for verifying dynamic behavior).
   {"action_type": "CLICK", "element_id": "<id>"}

═══ OUTPUT FORMAT ═══
Return ONLY a single valid JSON object. No explanations, no markdown, no text \
outside the JSON. You MUST include a "thought" key first. Your thought must contain \
step-by-step reasoning: 1. Evaluate last action/reward, 2. Diagnose remaining issues in DOM, 3. Formulate fix.

═══ FEW-SHOT EXAMPLES ═══
User: (DOM shows a menu-toggle button and a menu-list)
Assistant: {
  "thought": "1. Reward is 0.0. 2. The menu button 'menu-toggle' lacks aria-expanded and the list 'menu-list' lacks role='menu'. 3. I will add aria-expanded='false' to the toggle first.",
  "action_type": "MODIFY",
  "element_id": "menu-toggle",
  "attribute": "aria-expanded",
  "value": "false"
}

User: (DOM shows a closed, visually off-screen sidebar)
Assistant: {
  "thought": "1. TAB shows focus moves to 'nav-link-1', but the description says the sidebar is closed. 2. Visually hidden elements must not be focusable or readable. 3. I will apply the boolean attribute 'inert' to the 'sidebar' container to hide it from all assistive tech.",
  "action_type": "MODIFY",
  "element_id": "sidebar",
  "attribute": "inert",
  "value": ""
}
"""
).strip()

VALID_ACTIONS = {"SCREEN_READER", "MODIFY", "TAB", "CLICK"}

TASKS = [
    "task_easy",
    "task_medium",
    "task_hard"
]


# ───────────────────── LOGGING UTILS ─────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


# ───────────────────── AGENT LOGIC ─────────────────────
def build_context(
    step: int, max_steps: int, obs_msg: str, dom: str, reward: float, 
    prev_reward: float, history: list, focus: Optional[list]
) -> str:
    reward_delta = reward - prev_reward
    if not history:
        trend = "No actions taken yet. Start by exploring the DOM."
    elif reward_delta > 0:
        trend = f"✅ LAST action INCREASED reward by +{reward_delta:.2f}. Continue this."
    elif reward_delta < 0:
        trend = f"⚠️ LAST action DECREASED reward by {reward_delta:.2f}. Harmful, try different approach."
    else:
        trend = f"Last action did NOT change reward (still {reward:.2f})."

    hist_str = "\n".join([
        f"  Step {entry['step']}: {json.dumps(entry['action'])} → \"{entry['result']}\" (reward: {entry['reward_after']:.2f})"
        for entry in history[-3:]  # Include only last 3 to avoid token bloat
    ]) if history else "  (none yet)"

    if len(dom) > 1500:
        dom = dom[:1500] + "\n... (DOM TRUNCATED)"

    return textwrap.dedent(f"""\
        ═══ STEP {step} of {max_steps} ═══
        OBSERVATION: {obs_msg}
        CURRENT REWARD: {reward:.2f} / 1.0
        REWARD TREND: {trend}

        DOM SNAPSHOT:
        {dom}
        FOCUS ORDER: {json.dumps(focus or [])}

        ACTION HISTORY (Last 3):
        {hist_str}

        Decide the NEXT best action based on the above. Return ONLY valid JSON.
        """).strip()


def get_action(client: OpenAI, context: str, retry: int = 0) -> tuple[dict, Optional[str]]:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=TEMPERATURE + (retry * 0.2),
            max_tokens=300,
        )
        content = (response.choices[0].message.content or "").strip()
        start, end = content.find("{"), content.rfind("}") + 1
        
        if start == -1 or end <= start:
            raise ValueError("No JSON object found in response.")
            
        parsed = json.loads(content[start:end])
        if "action_type" not in parsed or parsed["action_type"] not in VALID_ACTIONS:
            raise ValueError(f"Invalid or missing action_type. Must be one of {VALID_ACTIONS}")
            
        return parsed, None
    except Exception as e:
        if retry < 1:
            err_hint = f"\n\n[SYSTEM ERROR: {e}. Please return ONLY valid JSON with a valid action_type.]"
            return get_action(client, context + err_hint, retry=retry + 1)
        # Fallback action on final failure
        fallback = {"action_type": "SCREEN_READER", "element_id": "body", "thought": "Fallback due to parse error"}
        return fallback, str(e)


# ───────────────────── MAIN PIPELINE ─────────────────────
def main() -> None:
    # Initialize Open AI client pointed to Groq (or fallback API endpoint)
    try:
        client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    except OpenAIError as e:
        print(f"\nFailed to initialize the LLM client: {e}")
        print("Please make sure your API_KEY is set correctly in your terminal.")
        sys.exit(1)  
    except Exception as e:
        print(f"\nAn unexpected error occurred during client setup: {e}")
        sys.exit(1)

    env = A11yEngineerEnv()
    for task in TASKS:


        log_start(task=task, env=BENCHMARK, model=MODEL_NAME)

        difficulty = task.split("_")[1]
        obs = env.reset(episode_id=task, task=difficulty)
        
        history = []
        rewards = []
        steps_taken = 0
        score = 0.0
        success = False
        prev_reward = 0.0
        last_action_error = None
        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break

            context = build_context(
                step=step,
                max_steps=MAX_STEPS,
                obs_msg=obs.message,
                dom=obs.dom_snapshot,
                reward=obs.reward,
                prev_reward=prev_reward,
                history=history,
                focus=obs.focus_order,
            )

            action_dict, last_action_error = get_action(client, context)
            
            # Format action for Environment and Logging
            action_obj = A11yAction(
                action_type=action_dict.get("action_type", "SCREEN_READER"),
                element_id=action_dict.get("element_id"),
                attribute=action_dict.get("attribute"),
                value=action_dict.get("value")
            )
        
            # Remove "thought" purely for logging brevity, keeping the operative keys
            log_action_dict = {k: v for k, v in action_dict.items() if k != "thought" and v is not None}
            action_str = json.dumps(log_action_dict)

            # Step the environment
            obs = env.step(action_obj)
            reward = obs.reward
            done = obs.done

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=last_action_error)

            history.append({
                "step": step,
                "action": log_action_dict,
                "result": obs.message,
                "reward_after": reward
            })
        
            prev_reward = reward

            if done:
                break

        score = max(0.1, min(float(env.reward), 0.9))  # Clamp to [0.1, 0.9]
        success = score >= SUCCESS_SCORE_THRESHOLD

        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    main()