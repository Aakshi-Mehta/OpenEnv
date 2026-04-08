# ───────────────────── DATASET ─────────────────────
# This dataset contains 15 detailed accessibility scenarios (5 per difficulty).
# Each task has multiple deep HTML elements and requires 1 or more specific fixes.
TASKS = {
    "easy": {
        "task_easy": {
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
        "task_medium": {
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
        "task_hard": {
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
