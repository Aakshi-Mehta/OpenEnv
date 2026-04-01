from client import A11yClient
from models import A11yAction

tasks = ["easy", "medium", "hard"]

with A11yClient(base_url="http://localhost:8000").sync() as env:

    for task in tasks:
        env.reset(task=task)

        if task == "easy":
            env.step(A11yAction(action_type="SCREEN_READER", element_id="checkout-btn"))
            result = env.step(A11yAction(
                action_type="MODIFY",
                element_id="checkout-btn",
                attribute="aria-label",
                value="Checkout"
            ))

        elif task == "medium":
            env.step(A11yAction(action_type="TAB"))
            result = env.step(A11yAction(
                action_type="MODIFY",
                element_id="background",
                attribute="aria-hidden",
                value="true"
            ))

        elif task == "hard":
            env.step(A11yAction(
                action_type="MODIFY",
                element_id="cart",
                attribute="aria-live",
                value="polite"
            ))
            result = env.step(A11yAction(
                action_type="CLICK",
                element_id="add-btn"
            ))

        print(f"{task.upper()} SCORE:", result.reward)