from bs4 import BeautifulSoup
from openenv.core.env_server import Environment
from models import A11yAction, A11yObservation, A11yState


class A11yEngineerEnv(Environment):

    def __init__(self):
        self.task = "easy"
        self.dom = None
        self.reward = 0.0
        self.done = False
        self.step_count = 0

    # ---------------- RESET ----------------
    def reset(self, seed=None, episode_id=None, task="easy", **kwargs):
        self.task = task
        self.reward = 0.0
        self.done = False
        self.step_count = 0

        if task == "easy":
            html = '<div id="checkout-btn"><img src="icon.png"/></div>'

        elif task == "medium":
            html = """
            <div id="background">
                <button id="bg-btn">Hidden Button</button>
            </div>
            <div id="modal">
                <button id="close-btn">Close</button>
                <button id="accept-btn">Accept</button>
            </div>
            """

        elif task == "hard":
            html = """
            <div id="cart">Cart: 0</div>
            <button id="add-btn">Add to Cart</button>
            """

        self.dom = BeautifulSoup(html, "html.parser")

        return A11yObservation(
            message=f"{task} task started",
            dom_snapshot=str(self.dom),
            focus_order=[],
            done=False,
            reward=0.0
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
        return A11yState(
            task=self.task,
            step_count=self.step_count
        )

    # ---------------- EASY ----------------
    def _screen_reader(self, element_id):
        el = self.dom.find(id=element_id)

        if not el:
            return self._result("Element not found")

        if el.name == "img":
            output = el.get("alt", "unlabelled image")
        else:
            output = el.text or "unlabelled element"

        if self.task == "easy" and output == "unlabelled image":
            self.reward = max(self.reward, 0.5)

        return self._result(output)

    # ---------------- MODIFY ----------------
    def _modify(self, action):
        el = self.dom.find(id=action.element_id)

        if not el:
            return self._result("Element not found")

        el[action.attribute] = action.value

        # EASY grader
        if self.task == "easy":
            if action.attribute == "aria-label" and action.value.lower() == "checkout":
                self.reward = 1.0
                self.done = True

        # MEDIUM grader
        if self.task == "medium":
            if action.attribute == "aria-hidden" and action.value == "true":
                self.reward = 1.0
                self.done = True

        # HARD grader
        if self.task == "hard":
            if action.attribute == "aria-live":
                self.reward = max(self.reward, 0.8)

        return self._result("Modified")

    # ---------------- TAB ----------------
    def _tab(self):
        elements = self.dom.find_all(["button", "div"])
        order = [el.get("id") for el in elements]

        if self.task == "medium":
            if "bg-btn" in order:
                self.reward = max(self.reward, 0.3)

        return self._result("Tab simulated", order)

    # ---------------- CLICK ----------------
    def _click(self, element_id):
        if self.task == "hard" and element_id == "add-btn":
            cart = self.dom.find(id="cart")
            cart.string = "Cart: 1"

            if cart.get("aria-live"):
                self.reward = 1.0
                self.done = True

        return self._result("Clicked")

    # ---------------- RESULT ----------------
    def _result(self, message, focus=None):
        return A11yObservation(
            message=message,
            dom_snapshot=str(self.dom),
            focus_order=focus,
            reward=self.reward,
            done=self.done
        )