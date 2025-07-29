import requests
from frst_auth_cli.config import load_config
from frst_auth_cli.user import User
from frst_auth_cli.app import App
from frst_auth_cli.caching import TimedCache
from frst_auth_cli.exceptions import AppNotFoundError
from frst_auth_cli.exceptions import UserNotFoundError


class FrstAuthClient:

    def __init__(self, env: str, cache_ttl_minutes: int = 180):
        config = load_config()
        self.envs = config["environments"]
        self.paths = config["paths"]
        if env not in self.envs:
            raise ValueError(f"Ambiente inválido: {env}. Opções: {list(self.envs.keys())}")  # noqa E501
        self.base_url = self.envs[env]
        self._cache = TimedCache(ttl_minutes=cache_ttl_minutes)

    def verify_backend_token(self, backend_token: str) -> User:
        """
        Return the User object for the given uuid.

        Raises:
            UserNotFoundError: If no user with the given backend token exists.
        """
        cache_key = f"backend_token:{backend_token}"
        cached = self._cache.get(cache_key)
        if cached:
            return User(cached)
        url = f"{self.base_url}{self.paths['backend_token']}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {backend_token}"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            self._cache.set(cache_key, data)
            return User(data)
        else:
            raise UserNotFoundError(
                f"Error validating backend_token: {resp.status_code} {resp.text}"  # noqa E501
            )

    def verify_app_token(self, app_token: str) -> App:
        """
        Return the App object for the given uuid.

        Raises:
            AppNotFoundError: If no app with the given app token exists.
        """
        cache_key = f"app_token:{app_token}"
        cached = self._cache.get(cache_key)
        if cached:
            return App(cached)
        url = f"{self.base_url}{self.paths['app_token']}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Token {app_token}"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            self._cache.set(cache_key, data)
            return App(data)
        else:
            raise AppNotFoundError(
                f"Error validating app_token: {resp.status_code} {resp.text}"
            )
