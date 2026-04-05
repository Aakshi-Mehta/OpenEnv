"""
Feedback-Driven Iterative Reasoning Agent for Accessibility Engineering.

This agent uses an LLM to autonomously explore, diagnose, and fix
accessibility issues in a simulated DOM environment. It learns from
environment reward signals and adapts its strategy step-by-step.

Key design principles:
  - NO hardcoded element IDs, task logic, or manual fixes
  - Exploration-first: SCREEN_READER / TAB before MODIFY
  - Reward-based learning: tracks reward deltas to guide strategy
  - Full action memory: avoids repeating failed actions
  - Rich context: DOM, observations, history, and reward trends
"""

import os
import json
import time
import re
import math
from groq import Groq
from dotenv import load_dotenv
from client import A11yClient
from models import A11yAction, A11yObservation

load_dotenv()  # Load variables from .env if it exists


# ───────────────────── API CLIENT ─────────────────────
# Use environment variable; fall back to None for security
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY, max_retries=0)
MODEL = "llama-3.1-8b-instant"


# ───────────────────── SYSTEM PROMPT ─────────────────────
SYSTEM_PROMPT = """\
You are an expert accessibility engineer agent interacting with a live DOM \
environment. Your goal is to achieve a PERFECT accessibility score (reward = 1.0) \
by finding and fixing ALL accessibility issues.

═══ STRATEGY ═══
1. EXPLORE FIRST — Before modifying anything, use SCREEN_READER on elements and \
TAB through the page to understand the current accessibility state.
2. DIAGNOSE — Analyze the DOM for common violations:
   • Missing aria-label / alt text on interactive or image elements
   • Missing aria-hidden on decorative / background containers
   • Missing aria-live on dynamically-updated regions
   • Keyboard traps (elements that shouldn't be focusable)
   • Missing roles on interactive elements
3. FIX — Use MODIFY to add the correct ARIA attributes. Fix ALL issues, not just one.
4. VERIFY — After fixing, use SCREEN_READER / TAB to confirm the fix worked. \
Check if reward increased.
5. ADAPT — If reward did NOT increase after an action, that action was unhelpful. \
Try a DIFFERENT approach. Never repeat an action that did not improve the score.

═══ REWARD INTERPRETATION ═══
• reward = 0.0  → No progress yet. Explore more.
• 0.0 < reward < 1.0 → Partial progress. Some issues fixed, others remain. \
Keep going.
• reward = 1.0  → All issues fixed. Task complete!
• reward INCREASED after your last action → Good strategy, continue.
• reward UNCHANGED after your last action → That action didn't help. Try different.
• reward DECREASED → Your action made things worse. Undo or try another approach.

═══ AVAILABLE ACTIONS ═══
1. SCREEN_READER — Read an element with a screen reader to check its a11y state.
   {"action_type": "SCREEN_READER", "element_id": "<id>"}
2. TAB — Simulate Tab key to discover the focus/tab order of elements.
   {"action_type": "TAB"}
3. MODIFY — Set an attribute on a DOM element to fix an a11y issue.
   {"action_type": "MODIFY", "element_id": "<id>", "attribute": "<attr>", "value": "<val>"}
4. CLICK — Click an element (useful for verifying dynamic behavior).
   {"action_type": "CLICK", "element_id": "<id>"}

═══ OUTPUT FORMAT ═══
Return ONLY a single valid JSON object. No explanations, no markdown, no text \
outside the JSON. You MUST include a "thought" key first. Your thought must contain step-by-step reasoning: 1. Evaluate last action/reward, 2. Diagnose remaining issues in DOM, 3. Formulate fix.

═══ FEW-SHOT EXAMPLE ═══
User: (DOM shows a menu-toggle button and a menu-list)
Assistant: {
  "thought": "1. Reward is 0.0. 2. The menu button 'menu-toggle' lacks aria-expanded and the list 'menu-list' lacks role='menu'. 3. I will add aria-expanded='false' to the toggle first.",
  "action_type": "MODIFY",
  "element_id": "menu-toggle",
  "attribute": "aria-expanded",
  "value": "false"
}

Example:
{
  "thought": "1. Last action didn't help. 2. Image 'logo' lacks alt text. 3. I will read it using SCREEN_READER to verify.",
  "action_type": "SCREEN_READER", 
  "element_id": "logo"
}
"""


# ───────────────────── CONTEXT BUILDER ─────────────────────
def build_context(
    step: int,
    max_steps: int,
    observation_message: str,
    dom_snapshot: str,
    reward: float,
    prev_reward: float,
    action_history: list,
    focus_order: list | None = None,
) -> str:
    """
    Build a rich context string for the LLM including DOM state,
    reward progression, action history, and strategic hints.
    """
    reward_delta = reward - prev_reward

    # ── Reward trend analysis ──
    if len(action_history) == 0:
        reward_trend = "No actions taken yet. Start by exploring the DOM."
    elif reward_delta > 0:
        reward_trend = (
            f"✅ Your LAST action INCREASED the reward by +{reward_delta:.2f}. "
            f"Good strategy — continue this approach or build on it."
        )
    elif reward_delta < 0:
        reward_trend = (
            f"⚠️ Your LAST action DECREASED the reward by {reward_delta:.2f}. "
            f"That action was harmful. Try a different approach."
        )
    else:
        if reward == 0.0:
            reward_trend = (
                "Your last action did NOT change the reward (still 0.0). "
                "It was not helpful. Try a completely different action or target."
            )
        else:
            reward_trend = (
                f"Your last action did NOT change the reward (still {reward:.2f}). "
                f"There are still unfixed issues. Try a different fix."
            )

    # ── Phase hint ──
    if step < 3 and reward == 0.0:
        phase = (
            "PHASE: EXPLORATION — You should use SCREEN_READER and TAB to "
            "discover the accessibility state before making modifications."
        )
    elif reward > 0.0 and reward < 1.0:
        phase = (
            "PHASE: TARGETED FIXING — You've made partial progress. "
            "Analyze what's still broken and apply the right fix."
        )
    else:
        phase = (
            "PHASE: ACTIVE PROBLEM-SOLVING — Explore or modify as needed "
            "to increase the reward."
        )

    # ── Action history summary (TRUNCATED TO AVOID TOKEN LIMITS) ──
    if action_history:
        history_lines = []
        recent_history = action_history[-1:]
        for entry in recent_history:
            delta_str = f"+{entry['reward_delta']:.2f}" if entry["reward_delta"] >= 0 else f"{entry['reward_delta']:.2f}"
            history_lines.append(
                f"  Step {entry['step']}: {json.dumps(entry['action'])} "
                f"→ \"{entry['result_message']}\" | reward: {entry['reward_before']:.2f} → {entry['reward_after']:.2f} ({delta_str})"
            )
        history_block = "\n".join(history_lines)
    else:
        history_block = "  (none yet)"

    # ── Focus order info ──
    focus_info = ""
    if focus_order:
        focus_info = f"\nFOCUS ORDER (from TAB): {json.dumps(focus_order)}\n"

    # ── Urgency signal ──
    steps_remaining = max_steps - step
    urgency = ""
    if steps_remaining <= 3:
        urgency = (
            f"\n⚡ URGENT: Only {steps_remaining} steps remaining! "
            f"Focus on the most impactful MODIFY action.\n"
        )

    # ── DOM truncation ──
    if len(dom_snapshot) > 1500:
        dom_snapshot = dom_snapshot[:1500] + "\n... (DOM TRUNCATED TO SAVE TOKENS)"

    context = f"""\
═══ STEP {step + 1} of {max_steps} ═══
{phase}

OBSERVATION: {observation_message}

CURRENT REWARD: {reward:.2f} / 1.0
REWARD TREND: {reward_trend}

DOM SNAPSHOT:
{dom_snapshot}
{focus_info}{urgency}
ACTION HISTORY:
{history_block}

Based on the DOM, observation, reward feedback, and your action history, \
decide the NEXT best action. Return ONLY valid JSON.
"""
    return context


# ───────────────────── LLM ACTION SELECTOR ─────────────────────
VALID_ACTIONS = {"SCREEN_READER", "MODIFY", "TAB", "CLICK"}


def get_action(context: str, retry: int = 0) -> dict:
    """
    Call the LLM to decide the next action. Includes retry with error
    context and safe exploratory fallback.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=0.3 + (retry * 0.2),  # Increase temp on retry for diversity
        )

        content = response.choices[0].message.content.strip()

        # ── Extract JSON from response ──
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end <= start:
            raise ValueError(f"No JSON object found in LLM output: {content[:100]}")

        parsed = json.loads(content[start:end])

        # ── Validate action type ──
        if "thought" not in parsed:
            raise ValueError("Your JSON must include a 'thought' key explaining your reasoning.")
        if parsed.get("action_type") not in VALID_ACTIONS:
            raise ValueError(f"Invalid action_type: {parsed.get('action_type')}")

        return parsed

    except Exception as e:
        error_str = str(e).lower()
        if "rate limit" in error_str or "429" in error_str:
            wait_time = 5.0
            match = re.search(r"try again in (?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", error_str)
            if match:
                m = int(match.group(1)) if match.group(1) else 0
                s = float(match.group(2)) if match.group(2) else 0.0
                wait_time = m * 60 + s
            
            # Add a small buffer to ensure the rate limit window has fully passed
            wait_time = math.ceil(wait_time) + 1
            
            print(f"  ⏳ Rate limit hit. Required wait time: {wait_time}s. Pausing...")
            try:
                for i in range(wait_time, 0, -1):
                    print(f"     Resuming in {i}s...", end="\r")
                    time.sleep(1)
                print("                               ") # Clear line
                # Retry immediately, without incrementing the parsing `retry` counter
                return get_action(context, retry=retry)
            except KeyboardInterrupt:
                print("\n  🛑 User aborted rate limit sleep!")
                raise

        print(f"  ⚠️  Parse error (attempt {retry + 1}): {e}")

        if retry < 1:
            # Retry once with a hint about the error
            error_hint = (
                f"\n\n[SYSTEM: Your previous response could not be parsed. "
                f"Error: {e}. Please return ONLY a valid JSON object with "
                f"action_type as one of: {list(VALID_ACTIONS)}]\n"
            )
            return get_action(context + error_hint, retry=retry + 1)
        else:
            # Final fallback: safe exploratory action (never MODIFY blindly)
            print("  ⚠️  Falling back to safe exploratory action (TAB)")
            return {"action_type": "TAB"}


# ───────────────────── DUPLICATE DETECTION ─────────────────────
def is_duplicate_action(action: dict, action_history: list) -> bool:
    """Check if this exact action was already taken."""
    for entry in action_history:
        if entry["action"] == action:
            return True
    return False


# ───────────────────── AGENT LOOP ─────────────────────
def run_agent(task: str, max_steps: int = 25):
    """
    Run the feedback-driven reasoning agent on a single task.

    The agent follows an explore → diagnose → fix → verify cycle,
    adapting its strategy based on reward signals from the environment.
    """
    time.sleep(2.0)  # Ensure previous session is fully cleared
    with A11yClient(base_url="http://localhost:8000").sync() as env:

        result = env.reset(task=task)
        obs = result.observation
        reward = result.reward or 0.0
        prev_reward = 0.0

        # ── Memory: full action history with outcomes ──
        action_history = []

        # ── Score progression log (for learning visibility) ──
        score_log = [reward]

        print(f"\n{'=' * 60}")
        print(f"🚀 TASK: {task}")
        print(f"{'=' * 60}")
        print(f"  Initial observation: {obs.message}")
        print(f"  Initial reward: {reward:.2f}")
        print(f"  DOM: {obs.dom_snapshot[:120]}...")

        for step in range(max_steps):
            print(f"\n{'─' * 50}")
            print(f"  📍 Step {step + 1}/{max_steps}", end="")

            # Determine phase for logging
            if step < 3 and reward == 0.0:
                print("  [EXPLORATION PHASE]")
            elif reward > 0.0 and reward < 1.0:
                print("  [TARGETED FIXING]")
            else:
                print("  [ACTIVE SOLVING]")

            # ── Build rich context for LLM ──
            context = build_context(
                step=step,
                max_steps=max_steps,
                observation_message=obs.message,
                dom_snapshot=obs.dom_snapshot or "(no DOM available)",
                reward=reward,
                prev_reward=prev_reward,
                action_history=action_history,
                focus_order=obs.focus_order,
            )

            # ── Get LLM decision ──
            action_json = get_action(context)

            if not action_json:
                print("  ❌ No valid action produced. Stopping.")
                break

            if "thought" in action_json:
                print(f"  🧠 Thought: {action_json['thought']}")
                
            filtered_action = {k: v for k, v in action_json.items() if k != "thought"}

            # ── Duplicate detection ──
            if is_duplicate_action(filtered_action, action_history):
                print(f"  ⚠️  Duplicate action detected: {filtered_action}")
                print(f"  → Skipping LLM API retry, dropping soft-penalty observation natively...")
                # Inject a soft penalty without consuming an API call!
                obs = A11yObservation(
                    message="[SYSTEM WARNING] You just repeated exactly the same action. This wastes time. Choose a DIFFERENT target.",
                    dom_snapshot=obs.dom_snapshot or "(no DOM available)",
                    focus_order=obs.focus_order,
                    reward=reward,
                    done=False
                )
                action_history.append({
                    "step": step,
                    "action": filtered_action,
                    "result_message": obs.message,
                    "reward_before": reward,
                    "reward_after": reward,
                    "reward_delta": 0.0,
                })
                score_log.append(reward)
                continue

            print(f"  🎯 Action: {json.dumps(filtered_action)}")

            # ── Execute action ──
            try:
                action = A11yAction(**filtered_action)
                result = env.step(action)
            except Exception as e:
                print(f"  ❌ Action execution failed: {e}")
                # Record failure and continue
                action_history.append({
                    "step": step,
                    "action": action_json,
                    "result_message": f"EXECUTION ERROR: {e}",
                    "reward_before": reward,
                    "reward_after": reward,
                    "reward_delta": 0.0,
                })
                continue

            # ── Update state ──
            prev_reward = reward
            obs = result.observation
            reward = result.reward or 0.0
            reward_delta = reward - prev_reward

            # ── Record in action history ──
            action_history.append({
                "step": step,
                "action": action_json,
                "result_message": obs.message,
                "reward_before": prev_reward,
                "reward_after": reward,
                "reward_delta": reward_delta,
            })

            # ── Score progression ──
            score_log.append(reward)

            # ── Detailed step logging ──
            delta_str = f"+{reward_delta:.2f}" if reward_delta >= 0 else f"{reward_delta:.2f}"
            print(f"  📝 Result: \"{obs.message}\"")
            print(f"  📊 Reward: {prev_reward:.2f} → {reward:.2f} ({delta_str})")

            if reward_delta > 0:
                print(f"  ✅ IMPROVEMENT! Reward increased by {reward_delta:.2f}")
            elif reward_delta == 0 and reward < 1.0:
                print(f"  ⏸️  No improvement. Strategy change needed.")

            # ── Termination check ──
            if reward >= 1.0:
                print(f"\n  🎉 TASK COMPLETED! Perfect score achieved!")
                break

            if result.done:
                print(f"\n  ✅ Task marked done by environment.")
                break
        else:
            print(f"\n  ❌ Max steps ({max_steps}) reached without completing the task.")

        # ── Task summary with score progression ──
        print(f"\n{'=' * 60}")
        print(f"📈 SCORE PROGRESSION for '{task}': {' → '.join(f'{s:.2f}' for s in score_log)}")
        print(f"   Final reward: {reward:.2f} | Steps used: {len(action_history)}/{max_steps}")
        print(f"{'=' * 60}")

    return reward


# ───────────────────── MAIN ─────────────────────
if __name__ == "__main__":
    results = {}
    try:
        for task in ["easy", "medium", "hard"]:
            final_reward = run_agent(task)
            results[task] = final_reward
    except KeyboardInterrupt:
        print("\n\n  🛑 MASTER RUN ABORTED BY USER (Rate Limit Sleep Interrupted)")

    # ── Final summary across all tasks ──
    print(f"\n\n{'═' * 60}")
    print(f"📋 FINAL RESULTS SUMMARY")
    print(f"{'═' * 60}")
    if results:
        for task, score in results.items():
            status = "✅" if score >= 1.0 else "❌"
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            print(f"  {status} {task:8s}  [{bar}]  {score:.2f}")
        avg = sum(results.values()) / len(results)
        print(f"\n  Average score: {avg:.2f}")
    else:
        print("  No tasks completed.")
    print(f"{'═' * 60}")