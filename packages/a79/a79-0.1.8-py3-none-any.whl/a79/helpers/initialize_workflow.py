import json
import socket
from datetime import datetime

from common_py.context import ContextWrapper


class WorkflowInitializer:
    def __init__(self):
        pass

    @staticmethod
    def initialize() -> None:
        # Import here to avoid circular dependency
        from external.a79.src.a79.client import A79Client

        api_client = A79Client()

        user = api_client.raw_request(method="GET", url="/api/v1/user/me", json={})

        # NOTE: The context is needed because we are executing nodes via library
        # calls which require a context while making db updates.
        # This will be reworked once we move to e2b and run the nodes via the API.
        ContextWrapper.init_from_json(
            json.dumps({"org_id": user["org_id"], "user_id": user["auth0_user_id"]})
        )

        # Generate timestamp string in format: YYYYMMDD_HHMMSS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hostname = socket.gethostname()

        base_name = f"sdk-run-{hostname}-{timestamp}"

        folder_response = api_client.raw_request(
            method="POST", url="/api/v1/folder", json={"name": base_name}
        )
        print(folder_response, flush=True)
