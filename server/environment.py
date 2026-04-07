import random
from bs4 import BeautifulSoup
from openenv.core.env_server import Environment
from models import A11yAction, A11yObservation, A11yState

# ───────────────────── DATASET ─────────────────────
# This dataset contains 15 detailed accessibility scenarios (5 per difficulty).
# Each task has multiple deep HTML elements and requires 1 or more specific fixes.
TASKS = {
    "easy": {
        "easy_1_checkout": {
            "description": "A visually impaired user reported that they cannot figure out how to buy their items. The screen reader just announces 'button'. Fix the navigation bar.",
            "html": '\n            <div class="container">\n                <header>\n                    <nav class="top-nav">\n                        <div class="logo">ShopApp</div>\n                        <div class="actions">\n                            <button id="checkout-btn" class="nav-btn">\n                                <img id="cart-icon" src="cart.png" />\n                            </button>\n                        </div>\n                    </nav>\n                </header>\n                <main><h2>Welcome to ShopApp</h2></main>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "checkout-btn",
                    "attribute": "aria-label",
                    "group": "checkout_label",
                    "weight": 1.0,
                },
                {
                    "element_id": "cart-icon",
                    "attribute": "alt",
                    "group": "checkout_label",
                    "weight": 1.0,
                },
            ],
        },
        "easy_2_gallery": {
            "description": "Image gallery missing alt attributes.",
            "html": '\n            <div class="gallery">\n                <h2>Product Photos</h2>\n                <div class="grid">\n                    <img id="img-front" src="front.jpg" />\n                    <img id="img-back" src="back.jpg" />\n                </div>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "img-front",
                    "attribute": "alt",
                    "group": "front-image",
                    "weight": 0.5,
                },
                {
                    "element_id": "img-back",
                    "attribute": "alt",
                    "group": "back-image",
                    "weight": 0.5,
                },
            ],
        },
        "easy_3_form": {
            "description": "Form input missing associated label or aria-label.",
            "html": '\n            <form id="newsletter-form">\n                <h3>Subscribe</h3>\n                <div class="input-group">\n                    <span class="icon">[Mail Icon]</span>\n                    <input id="email-input" type="email" placeholder="Enter email" />\n                    <button id="submit-btn">Subscribe</button>\n                </div>\n            </form>\n            ',
            "expected_fixes": [
                {
                    "element_id": "email-input",
                    "attribute": "aria-label",
                    "group": "email-label",
                    "weight": 1.0,
                },
                {
                    "element_id": "email-input",
                    "attribute": "aria-labelledby",
                    "group": "email-label",
                    "weight": 1.0,
                },
                {
                    "element_id": "email-input",
                    "attribute": "title",
                    "group": "email-label",
                    "weight": 1.0,
                },
            ],
        },
        "easy_4_social": {
            "description": "Social post button missing aria-label.",
            "html": '\n            <article class="post">\n                <div class="content">Beautiful sunset!</div>\n                <div class="actions">\n                    <button id="like-btn">[Like]</button>\n                    <button id="share-btn">[Share]</button>\n                </div>\n            </article>\n            ',
            "expected_fixes": [
                {
                    "element_id": "like-btn",
                    "attribute": "aria-label",
                    "weight": 0.5,
                },
                {
                    "element_id": "share-btn",
                    "attribute": "aria-label",
                    "weight": 0.5,
                },
            ],
        },
        "easy_5_banner": {
            "description": "Decorative banner missing alt or aria-hidden.",
            "html": '\n            <div class="hero-section">\n                <img id="deco-banner" src="waves.png" />\n                <h1>Super Sale</h1>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "deco-banner",
                    "attribute": "aria-hidden",
                    "value": "true",
                    "group": "hide-decorative",
                    "weight": 1.0,
                },
                {
                    "element_id": "deco-banner",
                    "attribute": "alt",
                    "value": "",
                    "group": "hide-decorative",
                    "weight": 1.0,
                },
                {
                    "element_id": "deco-banner",
                    "attribute": "role",
                    "value": "presentation",
                    "group": "hide-decorative",
                    "weight": 1.0,
                },
            ],
        },
    },
    "medium": {
        "medium_1_modal": {
            "description": "User Bug Report: When the settings menu opens, screen reader users get confused. The reader does not announce that a popup has opened, users can accidentally navigate the background dashboard while the modal is open, and the button to close it is just announced as 'X'. Please fix this UI to be fully accessible.",
            "html": '\n            <div id="app-root">\n                <div id="background-content">\n                    <h1>Dashboard</h1>\n                    <button id="settings-btn">Settings</button>\n                </div>\n                <div class="overlay"></div>\n                <div id="settings-modal" class="modal">\n                    <h2>Settings</h2>\n                    <button id="close-modal-btn">X</button>\n                </div>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "settings-modal",
                    "attribute": "role",
                    "value": "dialog",
                    "weight": 0.34,
                },
                {
                    "element_id": "background-content",
                    "attribute": "aria-hidden",
                    "value": "true",
                    "group": "hide-bg",
                    "weight": 0.33,
                },
                {
                    "element_id": "background-content",
                    "attribute": "inert",
                    "value": "",
                    "group": "hide-bg",
                    "weight": 0.33,
                },
                {
                    "element_id": "close-modal-btn",
                    "attribute": "aria-label",
                    "group": "close-label",
                    "weight": 0.33,
                },
                {
                    "element_id": "close-modal-btn",
                    "attribute": "title",
                    "group": "close-label",
                    "weight": 0.33,
                },
            ],
        },
        "medium_2_dropdown": {
            "description": "User Bug Report: Screen reader users cannot tell if the Menu button is open or closed. Additionally, when they navigate inside the menu, it is read as a plain text list rather than an interactive dropdown menu.",
            "html": '\n            <div class="dropdown">\n                <button id="menu-toggle">Menu</button>\n                <ul id="menu-list">\n                    <li id="item-1">Profile</li>\n                    <li id="item-2">Logout</li>\n                </ul>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "menu-toggle",
                    "attribute": "aria-expanded",
                    "weight": 0.4,
                },
                {
                    "element_id": "menu-list",
                    "attribute": "role",
                    "value": "menu",
                    "weight": 0.2,
                },
                {
                    "element_id": "item-1",
                    "attribute": "role",
                    "value": "menuitem",
                    "weight": 0.2,
                },
                {
                    "element_id": "item-2",
                    "attribute": "role",
                    "value": "menuitem",
                    "weight": 0.2,
                },
            ],
        },
        "medium_3_tabs": {
            "description": "The interface contains a tabbed navigation component, but assistive technologies may not correctly interpret its structure or current state. Users relying on screen readers might struggle to understand which tab is active or how the content is organized.",
            "html": '\n            <div class="tabs-component">\n                <div id="tab-header">\n                    <button id="tab-1" class="active">Details</button>\n                    <button id="tab-2">Reviews</button>\n                </div>\n                <div id="panel-1">Product details here...</div>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "tab-header",
                    "attribute": "role",
                    "value": "tablist",
                    "weight": 0.20,
                },
                {
                    "element_id": "tab-1",
                    "attribute": "role",
                    "value": "tab",
                    "weight": 0.15,
                },
                {
                    "element_id": "tab-2",
                    "attribute": "role",
                    "value": "tab",
                    "weight": 0.15,
                },
                {
                    "element_id": "tab-1",
                    "attribute": "aria-selected",
                    "value": "true",
                    "weight": 0.20,
                },
                {
                    "element_id": "tab-1",
                    "attribute": "aria-controls",
                    "value": "panel-1",
                    "weight": 0.15,
                },
                {
                    "element_id": "panel-1",
                    "attribute": "role",
                    "value": "tabpanel",
                    "weight": 0.15,
                },
            ],
        },
        "medium_4_sidebar": {
            "description": "User Bug Report: The sidebar navigation menu is closed and visually off-screen, but when I use my keyboard's Tab key, my focus disappears into invisible links. Screen readers are also reading the hidden menu out loud. Please ensure the closed sidebar is completely ignored by all assistive tools.",
            "html": '\n            <div class="layout">\n                <main>\n                    <button id="open-nav">Open Nav</button>\n                </main>\n                <aside id="sidebar" style="transform: translateX(-100%);">\n                    <ul>\n                        <li><a id="nav-link-1" href="#home">Home</a></li>\n                    </ul>\n                </aside>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "sidebar",
                    "attribute": "inert",
                    "value": "",
                    "group": "hide-screen-reader",
                    "weight": 0.5,
                },
                {
                    "element_id": "sidebar",
                    "attribute": "aria-hidden",
                    "value": "true",
                    "group": "hide-screen-reader",
                    "weight": 0.5,
                },
                {
                    "element_id": "sidebar",
                    "attribute": "inert",
                    "value": "",
                    "group": "hide-keyboard",
                    "weight": 0.5,
                },
                {
                    "element_id": "nav-link-1",
                    "attribute": "tabindex",
                    "value": "-1",
                    "group": "hide-keyboard",
                    "weight": 0.5,
                },
            ],
        },
        "medium_5_validation": {
            "description": "User Bug Report: When I try to sign up and the username is taken, my screen reader tells me the input is 'invalid', but it doesn't read the actual error message out loud. I have no idea what I did wrong unless I manually tab away from the input and search the rest of the page for text.",
            "html": '\n            <form id="signup-form">\n                <label for="username">Username</label>\n                <input id="username" type="text" aria-invalid="true" />\n                <span id="username-error" class="error-text">Username taken.</span>\n                <button id="submit">Signup</button>\n            </form>\n            ',
            "expected_fixes": [
                {
                    "element_id": "username",
                    "attribute": "aria-describedby",
                    "value": "username-error",
                    "group": "error-association",
                    "weight": 0.6,
                },
                {
                    "element_id": "username",
                    "attribute": "aria-errormessage",
                    "value": "username-error",
                    "group": "error-association",
                    "weight": 0.6,
                },
                {
                    "element_id": "username-error",
                    "attribute": "role",
                    "value": "alert",
                    "group": "error-announcement",
                    "weight": 0.4,
                },
                {
                    "element_id": "username-error",
                    "attribute": "aria-live",
                    "value": "assertive",
                    "group": "error-announcement",
                    "weight": 0.4,
                },
                {
                    "element_id": "username-error",
                    "attribute": "aria-live",
                    "value": "polite",
                    "group": "error-announcement",
                    "weight": 0.4,
                },
            ],
        },
    },
    "hard": {
        "hard_1_cart": {
            "description": "An interface updates information dynamically after a user action, but assistive technologies may not be aware of these updates. Users relying on screen readers might miss important changes happening on the page.",
            "html": '\n            <div class="shop">\n                <div id="cart-status">\n                    <span id="cart-count">0 items</span>\n                </div>\n                <div class="product">\n                    <h2>Shoes</h2>\n                    <button id="add-btn">Add to Cart</button>\n                </div>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "cart-status",
                    "attribute": "aria-live",
                    "value": "polite",
                    "weight": 0.7,
                },
                {
                    "element_id": "add-btn",
                    "attribute": "aria-label",
                    "value": "Add item to cart",
                    "group": "button_label",
                    "weight": 0.3,
                },
                {
                    "element_id": "add-btn",
                    "attribute": "aria-label",
                    "value": "Add to cart",
                    "group": "button_label",
                    "weight": 0.3,
                },
            ],
            "requires_interaction": True,
            "dynamic_behavior": {"click_events": {"add-btn": "update_cart_text"}},
        },
        "hard_2_toast": {
            "description": "A temporary notification appears after a user action, but users relying on assistive technologies may not be informed when the message becomes visible or what it contains.",
            "html": '\n            <div class="app">\n                <button id="save-btn">Save Content</button>\n                <div id="toast-container"></div>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "toast-container",
                    "attribute": "aria-live",
                    "value": "polite",
                    "weight": 0.5,
                },
                {
                    "element_id": "toast-container",
                    "attribute": "role",
                    "value": "status",
                    "weight": 0.5,
                },
            ],
            "requires_interaction": True,
            "dynamic_behavior": {"click_events": {"save-btn": "show_toast"}},
        },
        "hard_3_multistep": {
            "description": "A multi-step process updates progress visually, but users relying on assistive technologies may not receive accurate information about the current progress or changes between steps.",
            "html": '\n            <div class="wizard">\n                <div id="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100"></div>\n                <div class="step-content">Step 1 of 3</div>\n                <button id="next-btn">Next</button>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "progress-bar",
                    "attribute": "aria-valuenow",
                    "weight": 0.6,
                },
                {
                    "element_id": "next-btn",
                    "attribute": "aria-controls",
                    "value": "progress-bar",
                    "weight": 0.4,
                },
            ],
            "requires_interaction": True,
            "dynamic_behavior": {"click_events": {"next-btn": "advance_step"}},
        },
        "hard_4_search": {
            "description": "A search interface provides dynamic suggestions or results, but assistive technologies may not correctly interpret the relationship between the input and the displayed results or detect when new results appear.",
            "html": '\n            <div class="search-widget">\n                <input id="search-input" type="text" placeholder="Search..." />\n                <button id="search-btn">Go</button>\n                <ul id="search-results" style="display:none;">\n                </ul>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "search-input",
                    "attribute": "aria-autocomplete",
                    "value": "list",
                    "weight": 0.3,
                },
                {
                    "element_id": "search-input",
                    "attribute": "aria-controls",
                    "value": "search-results",
                    "weight": 0.3,
                },
                {
                    "element_id": "search-results",
                    "attribute": "aria-live",
                    "value": "polite",
                    "weight": 0.4,
                },
            ],
            "requires_interaction": True,
            "dynamic_behavior": {"click_events": {"search-btn": "show_results"}},
        },
        "hard_5_slider": {
            "description": "A custom interactive control allows users to adjust a value visually, but it may not be properly exposed to assistive technologies, making it difficult for users to understand or interact with it.",
            "html": '\n            <div class="volume-control">\n                <label id="vol-label">Volume</label>\n                <div id="vol-slider" class="track">\n                    <div id="vol-thumb" class="thumb" style="left: 50%;"></div>\n                </div>\n            </div>\n            ',
            "expected_fixes": [
                {
                    "element_id": "vol-slider",
                    "attribute": "role",
                    "value": "slider",
                    "weight": 0.25,
                },
                {
                    "element_id": "vol-slider",
                    "attribute": "tabindex",
                    "value": "0",
                    "weight": 0.25,
                },
                {
                    "element_id": "vol-slider",
                    "attribute": "aria-valuenow",
                    "weight": 0.25,
                },
                {
                    "element_id": "vol-slider",
                    "attribute": "aria-labelledby",
                    "value": "vol-label",
                    "weight": 0.25,
                },
            ],
        },
    },
}


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
        self.DISCOVERY_REWARD = 0.2
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
        newly_discovered = self._detect_discovered_issue(element_id)
        if newly_discovered:
            # Update reward with discovery bonus
            self.reward = self._calculate_reward()
            discovery_msg = (
                f" [ISSUE FOUND! +{self.DISCOVERY_REWARD:.1f} discovery reward]"
            )
        else:
            discovery_msg = ""

        return self._result(f"Screen Reader says: '{output}'{discovery_msg}")

    # -------- DETECT ISSUE DISCOVERY --------
    def _detect_discovered_issue(self, element_id):
        """
        Check if element has an undiscovered accessibility issue.
        Returns True if a new issue was freshly discovered.
        Discovery bonus (0.2) is only awarded if base_score is 0 (no fixes applied yet).
        Base score is calculated using grouping and weight logic.
        """
        expected_fixes = self.current_task_meta.get("expected_fixes", [])

        if not expected_fixes:
            return False

        # Calculate current base score using grouping/weight logic
        base_score = self._calculate_base_score()

        # Only award discovery if base_score is 0 (no fixes applied yet)
        if base_score > 0:
            return False

        # Check if this element has an issue
        for fix in expected_fixes:
            if fix["element_id"] == element_id:
                fix_key = f"{element_id}_{fix['attribute']}"
                # If issue exists but not yet discovered
                if fix_key not in self.discovered_issues:
                    self.discovered_issues.add(fix_key)
                    return True

        return False

    # -------- CALCULATE BASE SCORE (Grouping + Weight Logic) --------
    def _calculate_base_score(self):
        """
        Calculate base score using grouping and weight logic:
        - Ungrouped fixes: each has a weight
        - Grouped fixes: completing ANY fix in a group counts as completing that group
        - total_weight = ungrouped_weight + sum(group_weights)
        - completed_weight = ungrouped_completed + sum(group_completed_weights)
        - base_score = completed_weight / total_weight
        """
        expected_fixes = self.current_task_meta.get("expected_fixes", [])

        if not expected_fixes:
            return 0.0

        # Build group->fixes map and collect all groups/ungrouped fixes
        groups = {}
        ungrouped_weight = 0.0

        for fix in expected_fixes:
            weight = fix.get("weight", 0.0)
            group_id = fix.get("group", None)

            if group_id:
                if group_id not in groups:
                    groups[group_id] = {"weight": weight, "fixes": []}
                groups[group_id]["fixes"].append(fix)
            else:
                ungrouped_weight += weight

        # Calculate total possible weight
        total_weight = ungrouped_weight + sum(g["weight"] for g in groups.values())

        if total_weight == 0:
            return 0.0

        # Calculate completed weight
        completed_weight = 0.0

        # Check ungrouped fixes
        for fix in expected_fixes:
            if fix.get("group") is None:
                if self._is_fix_applied(fix):
                    completed_weight += fix.get("weight", 1.0)

        # Check grouped fixes (need only one per group)
        for group_id, group_data in groups.items():
            for fix in group_data["fixes"]:
                if self._is_fix_applied(fix):
                    completed_weight += group_data["weight"]
                    break  # Only count once per group

        return completed_weight / total_weight

    # -------- CALCULATE REWARD --------
    def _calculate_reward(self):
        """
        Calculate reward:
        - Base: using grouping and weight logic (see _calculate_base_score)
        - Bonus: +0.2 for discovering an issue ONLY if base_score is 0 (no fixes applied yet)

        Once any fix is applied, base_score becomes > 0 and discovery bonus is no longer available.
        """
        base_score = self._calculate_base_score()

        # Add discovery bonus only if base_score is 0 (no fixes applied yet)
        if base_score == 0 and len(self.discovered_issues) > 0:
            discovery_bonus = self.DISCOVERY_REWARD
            return discovery_bonus

        return base_score

    def _is_fix_applied(self, expected_fix):
        """Check if a specific fix has been applied."""
        fix_key = f"{expected_fix['element_id']}_{expected_fix['attribute']}"
        if fix_key not in self.fixes_applied:
            return False

        # If value is specified, verify it's stored correctly
        if "value" in expected_fix:
            el = self.dom.find(id=expected_fix["element_id"])
            if el:
                actual_value = el.get(expected_fix["attribute"], "")
                expected_value = expected_fix["value"]
                return expected_value.lower() == str(actual_value).lower()

        return True

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
        self.reward = self._calculate_reward()
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
