import random
from bs4 import BeautifulSoup
from openenv.core.env_server import Environment
from models import A11yAction, A11yObservation, A11yState
from .dataset import TASKS
from .grading import Grader


class A11yEngineerEnv(Environment):

    def __init__(self):
        self.task_difficulty = "easy"
        self.task_id = None
        self.current_task_meta = None
        self.dom = None
        self.reward = 0.0
        self.done = False
        self.step_count = 0
        self.fixes_applied = set()
        self.discovered_issues = set()  # Track which issues have been discovered
        self.grader = Grader()
        self.DISCOVERY_REWARD = self.grader.DISCOVERY_REWARD
        self.FIX_REWARD = 0.8

    # ---------------- RESET ----------------
    def reset(self, seed=None, episode_id=None, task="easy", **kwargs):
        self.task_difficulty = task
        self.reward = 0.0
        self.done = False
        self.step_count = 0
        self.fixes_applied = set()
        self.discovered_issues = set()

        if task not in TASKS:
            task = "easy"

        # If episode_id is specifically given, try to load it
        available_tasks = TASKS[task]

        if episode_id and episode_id in available_tasks:
            self.task_id = episode_id
        else:
            # Default to the first task within difficulty
            self.task_id = random.choice(list(available_tasks.keys()))

        self.current_task_meta = available_tasks[self.task_id]
        self.dom = BeautifulSoup(self.current_task_meta["html"], "html.parser")

        return A11yObservation(
            message=f"Task started: {self.task_id}. {self.current_task_meta['description']}",
            dom_snapshot=str(self.dom),
            focus_order=[],
            done=False,
            reward=0.0,
        )

    # ---------------- STEP ----------------
    def step(self, action: A11yAction):
        self.step_count += 1

        if action.action_type == "SCREEN_READER":
            return self._screen_reader(action.element_id)

        elif action.action_type == "MODIFY":
            return self._modify(action)

        elif action.action_type == "TAB":
            return self._tab()

        elif action.action_type == "CLICK":
            return self._click(action.element_id)

        return self._result("Invalid action")

    # ---------------- STATE ----------------
    @property
    def state(self):
        return A11yState(task=self.task_difficulty, step_count=self.step_count)

    # ---------------- SCREEN_READER ----------------
    def _screen_reader(self, element_id):
        el = self.dom.find(id=element_id)

        if not el:
            return self._result("Element not found")

        # Simulate generic screen reader output
        output = el.text.strip()

        if el.name == "img":
            output = el.get("alt", "Unlabelled image")
        elif el.name == "input":
            output = el.get("placeholder", "Input field")
            # If there's an aria-label, that takes precedence
            if "aria-label" in el.attrs:
                output = el["aria-label"]
        elif not output and "aria-label" in el.attrs:
            output = el["aria-label"]

        if not output:
            output = "Unlabelled element / Empty content"

        # Check if this element has a discovery-worthy issue (only if no fixes applied yet)
        newly_discovered = self.grader.detect_discovered_issue(
            element_id, self.current_task_meta, self.fixes_applied, self.discovered_issues, self.dom
        )
        if newly_discovered:
            # Update reward with discovery bonus
            self.reward = self.grader.calculate_reward(
                self.current_task_meta, self.fixes_applied, self.discovered_issues, self.dom
            )
            discovery_msg = (
                f" [ISSUE FOUND! +{self.DISCOVERY_REWARD:.1f} discovery reward]"
            )
        else:
            discovery_msg = ""

        return self._result(f"Screen Reader says: '{output}'{discovery_msg}")



    # ---------------- MODIFY ----------------
    def _modify(self, action):
        el = self.dom.find(id=action.element_id)

        if not el:
            return self._result("Element not found")

        # ONLY delete if the agent explicitly passes None
        if action.value is None:
            if action.attribute in el.attrs:
                del el[action.attribute]
        else:
            # If the agent sends "", it successfully sets el["inert"] = "" or el["alt"] = ""
            el[action.attribute] = str(action.value)

        prev_reward = self.reward

        # Grading Logic: Compare against expected fixes
        expected_fixes = self.current_task_meta.get("expected_fixes", [])

        fix_was_correct = False
        for expected in expected_fixes:
            # Match element and attribute
            if (
                expected["element_id"] == action.element_id
                and expected["attribute"] == action.attribute
            ):
                # If a specific value is required, enforce it (case-insensitive)
                if "value" in expected:
                    # Allow fuzzy match if they provided true vs True
                    if expected["value"].lower() != str(action.value).lower():
                        continue

                # Mark this specific fix as applied
                fix_key = f"{action.element_id}_{action.attribute}"
                self.fixes_applied.add(fix_key)
                fix_was_correct = True

        # Calculate reward using completed_fixes / total_fixes logic
        self.reward = self.grader.calculate_reward(
            self.current_task_meta, self.fixes_applied, self.discovered_issues, self.dom
        )
        reward_delta = self.reward - prev_reward

        result_msg = "Modified successfully."
        if fix_was_correct and reward_delta > 0:
            result_msg += f" [FIX APPLIED! +{reward_delta:.2f} reward]"

        if self.reward >= 1.0:
            self.done = True
            result_msg += " [TASK COMPLETE!]"

        return self._result(result_msg)

    # ---------------- TAB ----------------
    def _tab(self):
        elements = []
        # Find all tags in DOM order
        for el in self.dom.find_all(True):
            # If an element or ANY of its parents are inert, it is completely skipped.
            is_inert = False
            for parent in [el] + el.find_parents():
                if "inert" in parent.attrs:
                    is_inert = True
                    break
            if is_inert:
                continue
            tabindex = el.get("tabindex")
        
            # 1. If explicitly removed from tab order, skip it entirely
            if tabindex == "-1":
                continue
            
            # 2. Add inherently interactive elements, or elements with tabindex="0"
            if el.name in ["button", "a", "input", "textarea", "select"] or tabindex == "0":
                elements.append(el)

        order = [el.get("id", "no-id") for el in elements]
        return self._result("Tab simulated", order)
    

    # ---------------- CLICK ----------------
    def _click(self, element_id):
        el = self.dom.find(id=element_id)
        if not el:
            return self._result("Element not found for click")

        message = "Clicked."

        # Dynamic Behaviors specifically for HARD tasks
        dynamic = self.current_task_meta.get("dynamic_behavior", {})
        events = dynamic.get("click_events", {})

        if element_id in events:
            behavior = events[element_id]

            if behavior == "update_cart_text":
                cart = self.dom.find(id="cart-count")
                if cart:
                    cart.string = "1 items"
                    message = "Clicked. Cart dynamic UI updated."

            elif behavior == "show_toast":
                toast = self.dom.find(id="toast-container")
                if toast:
                    toast.string = "Settings saved successfully!"
                    toast["style"] = "display: block;"
                    message = "Clicked. Dynamic toast notification appeared."

            elif behavior == "advance_step":
                bar = self.dom.find(id="progress-bar")
                if bar:
                    bar["style"] = "width: 50%;"
                    step_content = self.dom.find(class_="step-content")
                    if step_content:
                        step_content.string = "Step 2 of 3"
                    message = "Clicked. Advanced to next step."

            elif behavior == "show_results":
                results = self.dom.find(id="search-results")
                if results:
                    results["style"] = "display: block;"
                    new_item = self.dom.new_tag("li")
                    new_item.string = "Result 1"
                    results.append(new_item)
                    message = "Clicked. Search results appeared dynamically."

        # If a hard task requires both modifications AND a dynamic interaction to be verified via reward...
        # Wait, grading is purely structural in `_modify` now.
        # But this _click allows the agent to SEE dynamic DOM changes.

        return self._result(message)

    # ---------------- RESULT FORMATTING ----------------
    def _result(self, message, focus=None):
        return A11yObservation(
            message=message,
            dom_snapshot=str(self.dom),
            focus_order=focus,
            reward=self.reward,
            done=self.done,
        )
