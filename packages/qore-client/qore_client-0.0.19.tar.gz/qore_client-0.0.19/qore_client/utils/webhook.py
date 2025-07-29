from typing import Literal

from qore_client.utils.workflow import extract_logs


class WebhookOperations:
    """Webhook operation utilities for QoreClient"""

    def __init__(self, request_method):
        """
        Initialize with the request method from the parent client
        """
        self._request = request_method

    def execute_webhook(
        self, webhook_id: str, format: Literal["raw", "logs"] = "logs", **kwargs
    ) -> dict | list[str]:
        """Webhook을 실행합니다."""

        json = {"params": kwargs}
        response = self._request("POST", f"/webhook/{webhook_id}", json=json)

        if format == "logs":
            return extract_logs(response)
        elif format == "raw":
            return response
