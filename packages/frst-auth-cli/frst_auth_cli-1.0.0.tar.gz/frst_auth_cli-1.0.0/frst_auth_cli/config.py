import os
import json


CONFIG_PATH = os.path.expanduser("~/.frst_auth_cli/config.json")


DEFAULT_CONFIG = {
    "environments": {
        "aws-dev": "https://api-auth.dev.frstfalconi.cloud",
        "aws-prod": "https://api-auth.frstfalconi.cloud",
        "gcp-dev": "https://api-auth.dev.frstfalconi.com.br",
        "gcp-prod": "https://api-auth.frstfalconi.com.br"
    },
    "paths": {
        "backend_token": "/api/v1/me",
        "app_token": "/api/v1/auth-app"
    }
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            environments = data.get("environments", DEFAULT_CONFIG["environments"])  # noqa E501
            paths = data.get("paths", DEFAULT_CONFIG["paths"])
            return {"environments": environments, "paths": paths}
    return DEFAULT_CONFIG


def save_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
