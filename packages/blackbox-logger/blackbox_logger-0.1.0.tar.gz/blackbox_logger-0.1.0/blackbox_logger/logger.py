import json
import logging
from .masking import mask_sensitive_data

logger = logging.getLogger("blackbox_logger")

class HTTPLogger:
    def __init__(self, get_user=None, get_client_ip=None):
        """
        :param get_user: Optional function to extract user info from request headers
        :param get_client_ip: Optional function to extract client IP from request
        """
        self.get_user = get_user or (lambda headers: "Unknown")
        self.get_client_ip = get_client_ip or (lambda request: request.client.host if hasattr(request, 'client') else 'Unknown')

    def log_request(self, method, path, headers, body, request):
        user = self.get_user(headers)
        user_agent = headers.get("User-Agent", "Unknown")
        client_ip = self.get_client_ip(request)

        try:
            parsed_body = json.loads(body)
            masked_body = mask_sensitive_data(parsed_body)
        except Exception:
            masked_body = body.decode("utf-8", errors="ignore") if isinstance(body, bytes) else body

        logger.info(
            f"[REQUEST] {method} {path} | User: {user} | IP: {client_ip} | "
            f"User-Agent: {user_agent} | Payload: {masked_body}"
        )

    def log_response(self, method, path, headers, response_body, status_code, request):
        user = self.get_user(headers)
        user_agent = headers.get("User-Agent", "Unknown")
        client_ip = self.get_client_ip(request)

        try:
            parsed_response = json.loads(response_body)
        except Exception:
            parsed_response = response_body.decode("utf-8", errors="ignore") if isinstance(response_body, bytes) else response_body

        logger.info(
            f"[RESPONSE] {method} {path} | User: {user} | IP: {client_ip} | "
            f"User-Agent: {user_agent} | Status: {status_code} | Response: {parsed_response}"
        )
