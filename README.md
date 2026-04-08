---
title: Accessibility Engineer Environment Server
emoji: 🔕
colorFrom: gray
colorTo: pink
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
---

# Accessibility Engineer Environment

**This project features an LLM Agent operating within a custom Reinforcement Learning environment (OpenEnv) to solve accessibility challenges through iterative feedback.**

It serves as an OpenEnv accessibility remediation environment for training and benchmarking agents on DOM inspection, keyboard navigation, and ARIA-based fixes. The environment simulates a task-driven web page, tracks accessibility issues, and scores the agent's fixes through structured reward signals.

## What This Project Provides

- A server-backed OpenEnv environment exposed through `server.app:app` and `server.app:main`
- Typed action, observation, and state models in `models.py`
- A WebSocket client in `client.py`
- A task generator and scoring logic in `server/environment.py`, `server/dataset.py`, and `server/grading.py`
- Example inference loops in `inference.py` and `llm_agent.py` demonstrating the LLM policy in action

## Project Layout

```text
accessibility-engineer/
├── openenv.yaml
├── pyproject.toml
├── Dockerfile
├── README.md
├── client.py
├── inference.py
├── llm_agent.py
├── models.py
├── server/
│   ├── app.py
│   ├── environment.py
│   ├── dataset.py
│   └── grading.py
└── requirements.txt
```

## Local Setup

Use Python 3.10 or newer.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you prefer the project metadata instead of the requirements file, install from `pyproject.toml` with your tool of choice.

## Run The Server Locally

The environment server is exposed from `server.app`.

```bash
python -m server.app
```

Or run it directly with Uvicorn during development:

```bash
uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
```

The OpenEnv entrypoint is configured in `openenv.yaml` as `server.app:main`.

## Use The Client

`client.py` provides a typed WebSocket client for interacting with the environment.

```python
from client import A11yClient
from models import A11yAction

client = A11yClient(base_url="http://localhost:8000")
obs = client.reset(task="easy")

result = client.step(
    A11yAction(
        action_type="SCREEN_READER",
        element_id="main-content",
    )
)

print(result.observation.message)
print(result.reward)
client.close()
```

## Environment Model

The environment uses three model classes:

- `A11yAction` in `models.py`
- `A11yObservation` in `models.py`
- `A11yState` in `models.py`

### Actions

Supported action types are:

- `SCREEN_READER`
- `MODIFY`
- `TAB`
- `CLICK`

### Observation Fields

`A11yObservation` includes:

- `message`: Human-readable feedback from the environment
- `dom_snapshot`: Current DOM as a string
- `focus_order`: Focus order returned from tab simulation
- `reward`: Current reward
- `done`: Whether the task is complete

### State Fields

`A11yState` includes:

- `task`: Current task difficulty
- `step_count`: Number of actions taken in the episode

## Task Flow

The environment starts with `reset(task=...)` and returns a task description plus a DOM snapshot. Agents should usually:

1. Explore with `SCREEN_READER` and `TAB`
2. Inspect the DOM for accessibility issues
3. Apply fixes with `MODIFY`
4. Verify changes and watch the reward increase toward `1.0`

The environment logic in `server/environment.py` currently supports task difficulty buckets such as `easy`, `medium`, and `hard`.

## Example Inference Scripts

`inference.py` and `llm_agent.py` show how to automate environment interaction with an LLM.

Scripts expect environment variables for model access, such as:

- `API_KEY`
- `MODEL_NAME`
- `API_BASE_URL` for OpenAI-compatible endpoints
- `A11Y_ENV_URL` for the environment WebSocket URL
- `MY_ENV_V4_BENCHMARK` and `MY_ENV_V4_TASK` for evaluation tracking
- `LOCAL_IMAGE_NAME` for Docker builds

They are designed to run against the live environment without needing to modify the server code.

## Docker

The repository includes a Dockerfile for building the environment into a container image.

```bash
docker build -t accessibility-engineer:latest .
docker run -p 8000:8000 accessibility-engineer:latest
```

The container exposes the server on port `8000`.

## Hugging Face Deployment

This project is set up for Hugging Face Spaces deployment with a web interface.

```bash
openenv validate
openenv push
```

If you want to push to a specific repository:

```bash
openenv push --repo-id your-username/accessibility-engineer
```

The generated Space uses Docker and serves the web interface at `/web`.

## Validation Notes

The OpenEnv manifest is in `openenv.yaml`, and the package metadata is in `pyproject.toml`.

- `openenv.yaml` points to `server.app:main`
- `pyproject.toml` exposes the `server` entry point
- `Dockerfile` launches the API server in a container-friendly way

If you change server startup behavior, keep those three files consistent.
