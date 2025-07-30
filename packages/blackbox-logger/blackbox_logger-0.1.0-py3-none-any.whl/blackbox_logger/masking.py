SENSITIVE_FIELDS = {"password", "pass", "passwd", "secret", "token", "api_key"}

def mask_sensitive_data(data):
    if isinstance(data, dict):
        return {
            key: "***" if key.lower() in SENSITIVE_FIELDS else mask_sensitive_data(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    return data
