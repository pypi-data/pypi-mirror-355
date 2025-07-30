import json
from .masking import mask_sensitive_data
from .loggers.file_logger import setup_file_logger
from .loggers.sqlite_logger import SQLiteLogger

file_logger = setup_file_logger()
sqlite_logger = SQLiteLogger()

class HTTPLogger:
    def __init__(self, get_user=None, get_client_ip=None):
        self.get_user = get_user or self._default_get_user
        self.get_client_ip = get_client_ip or self._default_get_ip

    def _default_get_user(self, headers, request=None):
        try:
            # Django
            if hasattr(request, "user"):
                return str(request.user) if request.user.is_authenticated else "Anonymous"
            # FastAPI
            if hasattr(request, "state") and hasattr(request.state, "user"):
                return str(request.state.user)
            # Flask (optional: attach `user` to request manually)
            if hasattr(request, "user"):
                return str(request.user)
        except Exception:
            pass
        return "Unknown"

    def _default_get_ip(self, request):
        try:
            if hasattr(request, "META"):  # Django
                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                if x_forwarded_for:
                    return x_forwarded_for.split(",")[0]
                return request.META.get("REMOTE_ADDR", "Unknown")
            if hasattr(request, "headers") and hasattr(request, "remote_addr"):  # Flask
                return request.headers.get("X-Forwarded-For", request.remote_addr)
            if hasattr(request, "client"):  # FastAPI
                return request.client.host
        except Exception:
            pass
        return "Unknown"

    def log_request(self, method, path, headers, body, request):
        user = self.get_user(headers)
        user_agent = headers.get("User-Agent", "Unknown")
        client_ip = self.get_client_ip(request)

        try:
            parsed_body = json.loads(body)
            masked_body = mask_sensitive_data(parsed_body)
        except Exception:
            masked_body = body.decode("utf-8", errors="ignore") if isinstance(body, bytes) else body

        msg = f"[REQUEST] {method} {path} | User: {user} | IP: {client_ip} | User-Agent: {user_agent} | Payload: {masked_body}"
        file_logger.info(msg)
        sqlite_logger.log("request", method, path, user, client_ip, user_agent, masked_body)

    def log_response(self, method, path, headers, response_body, status_code, request):
        user = self.get_user(headers, request)
        user_agent = headers.get("User-Agent", "Unknown")
        client_ip = self.get_client_ip(request)

        # Try to detect if content is HTML
        content_type = headers.get("Content-Type", "") or ""

        if "html" in content_type.lower() or path.endswith(".html"):
            parsed_response = "[HTML content skipped]"
        else:
            try:
                parsed_response = json.loads(response_body)
            except Exception:
                parsed_response = (
                    response_body.decode("utf-8", errors="ignore")
                    if isinstance(response_body, bytes)
                    else str(response_body)
                )

        msg = f"[RESPONSE] {method} {path} | User: {user} | IP: {client_ip} | User-Agent: {user_agent} | Status: {status_code} | Response: {parsed_response}"
        file_logger.info(msg)
        sqlite_logger.log("response", method, path, user, client_ip, user_agent, parsed_response, status_code)
