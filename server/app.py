from openenv.core.env_server import create_fastapi_app
from server.environment import A11yEngineerEnv
from models import A11yAction, A11yObservation

app = create_fastapi_app(
    A11yEngineerEnv,
    A11yAction,
    A11yObservation
)