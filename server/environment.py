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
            "description": "Checkout button missing aria-label, icon missing alt.",
            "html": "\n            <div class=\"container\">\n                <header>\n                    <nav class=\"top-nav\">\n                        <div class=\"logo\">ShopApp</div>\n                        <div class=\"actions\">\n                            <button id=\"checkout-btn\" class=\"nav-btn\">\n                                <img id=\"cart-icon\" src=\"cart.png\" />\n                            </button>\n                        </div>\n                    </nav>\n                </header>\n                <main><h2>Welcome to ShopApp</h2></main>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "checkout-btn",
                    "attribute": "aria-label"
                },
                {
                    "element_id": "cart-icon",
                    "attribute": "alt"
                }
            ]
        },
        "easy_2_gallery": {
            "description": "Image gallery missing alt attributes.",
            "html": "\n            <div class=\"gallery\">\n                <h2>Product Photos</h2>\n                <div class=\"grid\">\n                    <img id=\"img-front\" src=\"front.jpg\" />\n                    <img id=\"img-back\" src=\"back.jpg\" />\n                </div>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "img-front",
                    "attribute": "alt"
                },
                {
                    "element_id": "img-back",
                    "attribute": "alt"
                }
            ]
        },
        "easy_3_form": {
            "description": "Form input missing associated label or aria-label.",
            "html": "\n            <form id=\"newsletter-form\">\n                <h3>Subscribe</h3>\n                <div class=\"input-group\">\n                    <span class=\"icon\">[Mail Icon]</span>\n                    <input id=\"email-input\" type=\"email\" placeholder=\"Enter email\" />\n                    <button id=\"submit-btn\">Subscribe</button>\n                </div>\n            </form>\n            ",
            "expected_fixes": [
                {
                    "element_id": "email-input",
                    "attribute": "aria-label"
                }
            ]
        },
        "easy_4_social": {
            "description": "Social post button missing aria-label.",
            "html": "\n            <article class=\"post\">\n                <div class=\"content\">Beautiful sunset!</div>\n                <div class=\"actions\">\n                    <button id=\"like-btn\">[Like]</button>\n                    <button id=\"share-btn\">[Share]</button>\n                </div>\n            </article>\n            ",
            "expected_fixes": [
                {
                    "element_id": "like-btn",
                    "attribute": "aria-label"
                },
                {
                    "element_id": "share-btn",
                    "attribute": "aria-label"
                }
            ]
        },
        "easy_5_banner": {
            "description": "Decorative banner missing aria-hidden.",
            "html": "\n            <div class=\"hero-section\">\n                <img id=\"deco-banner\" src=\"waves.png\" />\n                <h1>Super Sale</h1>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "deco-banner",
                    "attribute": "aria-hidden",
                    "value": "true"
                }
            ]
        }
    },
    "medium": {
        "medium_1_modal": {
            "description": "Modal missing role and background not hidden.",
            "html": "\n            <div id=\"app-root\">\n                <div id=\"background-content\">\n                    <h1>Dashboard</h1>\n                    <button id=\"settings-btn\">Settings</button>\n                </div>\n                <div class=\"overlay\"></div>\n                <div id=\"settings-modal\" class=\"modal\">\n                    <h2>Settings</h2>\n                    <button id=\"close-modal-btn\">X</button>\n                </div>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "settings-modal",
                    "attribute": "role",
                    "value": "dialog"
                },
                {
                    "element_id": "background-content",
                    "attribute": "aria-hidden",
                    "value": "true"
                },
                {
                    "element_id": "close-modal-btn",
                    "attribute": "aria-label"
                }
            ]
        },
        "medium_2_dropdown": {
            "description": "Dropdown missing menu roles and aria-expanded.",
            "html": "\n            <div class=\"dropdown\">\n                <button id=\"menu-toggle\">Menu</button>\n                <ul id=\"menu-list\">\n                    <li id=\"item-1\">Profile</li>\n                    <li id=\"item-2\">Logout</li>\n                </ul>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "menu-toggle",
                    "attribute": "aria-expanded"
                },
                {
                    "element_id": "menu-list",
                    "attribute": "role",
                    "value": "menu"
                }
            ]
        },
        "medium_3_tabs": {
            "description": "Tablist missing roles and state.",
            "html": "\n            <div class=\"tabs-component\">\n                <div id=\"tab-header\">\n                    <button id=\"tab-1\" class=\"active\">Details</button>\n                    <button id=\"tab-2\">Reviews</button>\n                </div>\n                <div id=\"panel-1\">Product details here...</div>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "tab-header",
                    "attribute": "role",
                    "value": "tablist"
                },
                {
                    "element_id": "tab-1",
                    "attribute": "role",
                    "value": "tab"
                },
                {
                    "element_id": "tab-1",
                    "attribute": "aria-selected",
                    "value": "true"
                }
            ]
        },
        "medium_4_sidebar": {
            "description": "Hidden sidebar still receives focus.",
            "html": "\n            <div class=\"layout\">\n                <main>\n                    <button id=\"open-nav\">Open Nav</button>\n                </main>\n                <aside id=\"sidebar\" style=\"display: none;\">\n                    <ul>\n                        <li><a id=\"nav-link-1\" href=\"#home\">Home</a></li>\n                    </ul>\n                </aside>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "sidebar",
                    "attribute": "aria-hidden",
                    "value": "true"
                },
                {
                    "element_id": "nav-link-1",
                    "attribute": "tabindex",
                    "value": "-1"
                }
            ]
        },
        "medium_5_validation": {
            "description": "Error message not associated with input.",
            "html": "\n            <form id=\"signup-form\">\n                <label for=\"username\">Username</label>\n                <input id=\"username\" type=\"text\" aria-invalid=\"true\" />\n                <span id=\"username-error\" class=\"error-text\">Username taken.</span>\n                <button id=\"submit\">Signup</button>\n            </form>\n            ",
            "expected_fixes": [
                {
                    "element_id": "username",
                    "attribute": "aria-describedby",
                    "value": "username-error"
                }
            ]
        }
    },
    "hard": {
        "hard_1_cart": {
            "description": "Dynamic cart update missing aria-live.",
            "html": "\n            <div class=\"shop\">\n                <div id=\"cart-status\">\n                    <span id=\"cart-count\">0 items</span>\n                </div>\n                <div class=\"product\">\n                    <h2>Shoes</h2>\n                    <button id=\"add-btn\">Add to Cart</button>\n                </div>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "cart-status",
                    "attribute": "aria-live"
                }
            ],
            "dynamic_behavior": {
                "click_events": {
                    "add-btn": "update_cart_text"
                }
            }
        },
        "hard_2_toast": {
            "description": "Dynamic toast notification missing status role.",
            "html": "\n            <div class=\"app\">\n                <button id=\"save-btn\">Save Content</button>\n                <div id=\"toast-container\"></div>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "toast-container",
                    "attribute": "aria-live"
                },
                {
                    "element_id": "toast-container",
                    "attribute": "role",
                    "value": "status"
                }
            ],
            "dynamic_behavior": {
                "click_events": {
                    "save-btn": "show_toast"
                }
            }
        },
        "hard_3_multistep": {
            "description": "Multi-step form progress missing aria-valuenow.",
            "html": "\n            <div class=\"wizard\">\n                <div id=\"progress-bar\" role=\"progressbar\" aria-valuemin=\"0\" aria-valuemax=\"100\"></div>\n                <div class=\"step-content\">Step 1 of 3</div>\n                <button id=\"next-btn\">Next</button>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "progress-bar",
                    "attribute": "aria-valuenow"
                },
                {
                    "element_id": "next-btn",
                    "attribute": "aria-controls"
                }
            ],
            "dynamic_behavior": {
                "click_events": {
                    "next-btn": "advance_step"
                }
            }
        },
        "hard_4_search": {
            "description": "Typeahead search missing aria-autocomplete and ARIA connections.",
            "html": "\n            <div class=\"search-widget\">\n                <input id=\"search-input\" type=\"text\" placeholder=\"Search...\" />\n                <button id=\"search-btn\">Go</button>\n                <ul id=\"search-results\" style=\"display:none;\">\n                </ul>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "search-input",
                    "attribute": "aria-autocomplete"
                },
                {
                    "element_id": "search-input",
                    "attribute": "aria-controls",
                    "value": "search-results"
                },
                {
                    "element_id": "search-results",
                    "attribute": "aria-live"
                }
            ],
            "dynamic_behavior": {
                "click_events": {
                    "search-btn": "show_results"
                }
            }
        },
        "hard_5_slider": {
            "description": "Custom slider component missing ARIA attributes and keyboard focusablity.",
            "html": "\n            <div class=\"volume-control\">\n                <label id=\"vol-label\">Volume</label>\n                <div id=\"vol-slider\" class=\"track\">\n                    <div id=\"vol-thumb\" class=\"thumb\" style=\"left: 50%;\"></div>\n                </div>\n            </div>\n            ",
            "expected_fixes": [
                {
                    "element_id": "vol-slider",
                    "attribute": "role",
                    "value": "slider"
                },
                {
                    "element_id": "vol-slider",
                    "attribute": "tabindex",
                    "value": "0"
                },
                {
                    "element_id": "vol-slider",
                    "attribute": "aria-valuenow"
                },
                {
                    "element_id": "vol-slider",
                    "attribute": "aria-labelledby",
                    "value": "vol-label"
                }
            ]
        }
    }
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

    # ---------------- RESET ----------------
    def reset(self, seed=None, episode_id=None, task="easy", **kwargs):
        self.task_difficulty = task
        self.reward = 0.0
        self.done = False
        self.step_count = 0
        self.fixes_applied = set()

        if task not in TASKS:
            task = "easy"

        # If episode_id is specifically given, try to load it
        available_tasks = TASKS[task]
        
        if episode_id and episode_id in available_tasks:
            self.task_id = episode_id
        else:
            # Randomly pick a task within difficulty
            self.task_id = random.choice(list(available_tasks.keys()))

        self.current_task_meta = available_tasks[self.task_id]
        self.dom = BeautifulSoup(self.current_task_meta["html"], "html.parser")

        return A11yObservation(
            message=f"Task started: {self.task_id}. {self.current_task_meta['description']}",
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
            task=self.task_difficulty,
            step_count=self.step_count
        )

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

        return self._result(f"Screen Reader says: '{output}'")

    # ---------------- MODIFY ----------------
    def _modify(self, action):
        el = self.dom.find(id=action.element_id)

        if not el:
            return self._result("Element not found")

        el[action.attribute] = action.value
        
        # Grading Logic: Compare against expected fixes
        expected_fixes = self.current_task_meta["expected_fixes"]
        
        for expected in expected_fixes:
            # Match element and attribute
            if expected["element_id"] == action.element_id and expected["attribute"] == action.attribute:
                # If a specific value is required, enforce it (case-insensitive)
                if "value" in expected:
                    # Allow fuzzy math if they provided true vs True
                    if expected["value"].lower() != str(action.value).lower():
                        continue
                
                # Mark this specific fix as applied
                fix_key = f"{action.element_id}_{action.attribute}"
                self.fixes_applied.add(fix_key)

        # Calculate partial/full reward
        total_fixes_needed = len(expected_fixes)
        if total_fixes_needed > 0:
            self.reward = len(self.fixes_applied) / total_fixes_needed
        
        if self.reward >= 1.0:
            self.done = True

        return self._result("Modified successfully.")

    # ---------------- TAB ----------------
    def _tab(self):
        # Extract purely interactive elements to simulate simple DOM focus flow
        elements = self.dom.find_all(["button", "a", "input", "textarea", "select"])
        
        # Additionally, catch anything with a tabindex explicitly set
        for el in self.dom.find_all(True):
            if "tabindex" in el.attrs and el not in elements:
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
            done=self.done
        )
