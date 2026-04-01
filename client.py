from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult

from models import A11yAction, A11yObservation, A11yState


class A11yClient(EnvClient[A11yAction, A11yObservation, A11yState]):

    def _step_payload(self, action):
        return action.model_dump()

    def _parse_result(self, payload):
        obs = payload["observation"]

        return StepResult(
            observation=A11yObservation(**obs),
            reward=payload.get("reward"),
            done=payload.get("done")
        )

    def _parse_state(self, payload):
        return A11yState(**payload)