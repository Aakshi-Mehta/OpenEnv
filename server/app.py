# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from openenv.core.env_server.http_server import create_app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import A11yAction, A11yObservation
from server.environment import A11yEngineerEnv

app = create_app(
    A11yEngineerEnv,
    A11yAction,
    A11yObservation,
    env_name="accessibility-engineer",
    max_concurrent_envs=1
)

def main():
    """
    Entry point for direct execution via uv run or python -m.
    """
    import uvicorn
    import argparse
    import sys

    # Default ports
    host = "0.0.0.0"
    port = 8000

    # Safely parse args if run from CLI
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser()
        parser.add_argument("--port", type=int, default=8000)
        args, _ = parser.parse_known_args()
        port = args.port

    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    main()