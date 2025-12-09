import json
import os
from pathlib import Path
from typing import Dict, Optional

try:
    import requests
except Exception:
    requests = None  # optional dependency


PROFILE_DIR = Path.home() / ".dungeon_game" / "profiles"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)


class LocalProfile:
    """
    Simple local JSON profile storage.
    """
    def __init__(self, username: str):
        self.username = username
        self.path = PROFILE_DIR / f"{username}.json"
        self.data: Dict = {}

    def load(self) -> Dict:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as fh:
                self.data = json.load(fh)
        else:
            # default template
            self.data = {
                "username": self.username,
                "class": "warrior",
                "hp": 100,
                "attack": 10,
                "defense": 5,
                "crystals": 0,
                "inventory": {},
            }
        return self.data

    def save(self, data: Dict):
        self.data = data
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2)


class OnlineAuthClient:
    """
    Minimal online account client. This is optional and depends on an HTTP API.
    The methods will raise RuntimeError if `requests` is not available or the server
    fails to respond. Use LocalProfile as a fallback.
    """
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url.rstrip("/")

    def _post(self, path: str, payload: Dict) -> Dict:
        if requests is None:
            raise RuntimeError("requests is not installed; online features unavailable")
        resp = requests.post(f"{self.server_url}{path}", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def register(self, username: str, password: str) -> Dict:
        return self._post("/register", {"username": username, "password": password})

    def login(self, username: str, password: str) -> Dict:
        return self._post("/login", {"username": username, "password": password})

    def upload_profile(self, username: str, profile_data: Dict, token: Optional[str] = None) -> Dict:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if requests is None:
            raise RuntimeError("requests is not installed; online features unavailable")
        resp = requests.post(f"{self.server_url}/profiles/{username}", json=profile_data, headers=headers, timeout=5)
        resp.raise_for_status()
        return resp.json()

    def download_profile(self, username: str, token: Optional[str] = None) -> Dict:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if requests is None:
            raise RuntimeError("requests is not installed; online features unavailable")
        resp = requests.get(f"{self.server_url}/profiles/{username}", headers=headers, timeout=5)
        resp.raise_for_status()
        return resp.json()