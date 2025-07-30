import json
from .masking import mask_sensitive_data
from .loggers.file_logger import setup_file_logger
from .loggers.sqlite_logger import SQLiteLogger

file_logger = setup_file_logger()
sqlite_logger = SQLiteLogger()

class HTTPLogger:
    def __init__(self, get_user=None, get_client_ip=None):
        self.get_user = get_user or (lambda headers: "Unknown")
        self.get_client_ip = get_client_ip or (lambda req: getattr(req, "remote_addr", "Unknown"))

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
        user = self.get_user(headers)
        user_agent = headers.get("User-Agent", "Unknown")
        client_ip = self.get_client_ip(request)

        try:
            parsed_response = json.loads(response_body)
        except Exception:
            parsed_response = response_body.decode("utf-8", errors="ignore") if isinstance(response_body, bytes) else response_body

        msg = f"[RESPONSE] {method} {path} | User: {user} | IP: {client_ip} | User-Agent: {user_agent} | Status: {status_code} | Response: {parsed_response}"
        file_logger.info(msg)
        sqlite_logger.log("response", method, path, user, client_ip, user_agent, parsed_response, status_code)
