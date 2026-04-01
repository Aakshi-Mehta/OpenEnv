from typing import Optional, List
from openenv.core.env_server import Action, Observation, State


class A11yAction(Action):
    action_type: str
    element_id: Optional[str] = None
    attribute: Optional[str] = None
    value: Optional[str] = None


class A11yObservation(Observation):
    message: str
    dom_snapshot: Optional[str] = None
    focus_order: Optional[List[str]] = None


class A11yState(State):
    task: str
    step_count: int