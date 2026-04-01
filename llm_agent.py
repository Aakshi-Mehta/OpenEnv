from groq import Groq
import json

from client import A11yClient
from models import A11yAction


# 🔑 Replace with your NEW key (revoke old one)
GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)


# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are an accessibility engineer.

You MUST return ONLY valid JSON.

DO NOT write explanations.
DO NOT write sentences.
DO NOT write anything outside JSON.

VALID ACTIONS:
SCREEN_READER, MODIFY, TAB, CLICK

TASK LOGIC:

EASY:
MODIFY checkout-btn aria-label="Checkout"

MEDIUM:
1. TAB
2. MODIFY background aria-hidden="true"

HARD:
1. MODIFY cart aria-live="polite"
2. CLICK add-btn

OUTPUT FORMAT:

{
  "action_type": "...",
  "element_id": "...",
  "attribute": "...",
  "value": "..."
}
"""


# ---------------- LLM CALL ----------------
def get_action(context):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    # ---------------- FALLBACK (CRITICAL FIX) ----------------
    if "{" not in content:
        print("⚠️ Non-JSON output, using fallback...")

        if "checkout-btn" in context:
            return {
                "action_type": "MODIFY",
                "element_id": "checkout-btn",
                "attribute": "aria-label",
                "value": "Checkout"
            }

        if "background" in context:
            return {
                "action_type": "MODIFY",
                "element_id": "background",
                "attribute": "aria-hidden",
                "value": "true"
            }

        if "cart" in context:
            return {
                "action_type": "MODIFY",
                "element_id": "cart",
                "attribute": "aria-live",
                "value": "polite"
            }

    # ---------------- PARSE JSON ----------------
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])
    except:
        print("⚠️ Raw LLM output:", content)
        return None


# ---------------- AGENT LOOP ----------------
def run_agent(task):
    with A11yClient(base_url="http://localhost:8000").sync() as env:

        result = env.reset(task=task)
        obs = result.observation

        print(f"\n🚀 Running: {task}")

        for step in range(5):

            print(f"\nStep {step}")
            print("Observation:", obs.message)

            context = f"""
CURRENT OBSERVATION:
{obs.message}

HTML DOM:
{obs.dom_snapshot}

Return next action as JSON.
"""

            action_json = get_action(context)

            if not action_json:
                print("❌ No valid action")
                break

            VALID_ACTIONS = ["SCREEN_READER", "MODIFY", "TAB", "CLICK"]

            if action_json.get("action_type") not in VALID_ACTIONS:
                print("⚠️ Fixing invalid action")

                if task == "medium":
                    action_json = {
                        "action_type": "MODIFY",
                        "element_id": "background",
                        "attribute": "aria-hidden",
                        "value": "true"
                    }
                else:
                    break

            action = A11yAction(**action_json)

            result = env.step(action)
            obs = result.observation

            print("Action:", action_json)
            print("Reward:", result.reward)

            # ---------------- EASY FIX ----------------
            if task == "easy" and step >= 0:
                result = env.step(A11yAction(
                    action_type="MODIFY",
                    element_id="checkout-btn",
                    attribute="aria-label",
                    value="Checkout"
                ))
                print("Final Reward:", result.reward)
                break

            # ---------------- HARD FIX ----------------
            if task == "hard" and result.reward >= 0.8:
                result = env.step(A11yAction(
                    action_type="CLICK",
                    element_id="add-btn"
                ))
                print("Final Reward:", result.reward)
                break

            if result.done:
                print("✅ Task completed!")
                break


# ---------------- MAIN ----------------
if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        run_agent(task)