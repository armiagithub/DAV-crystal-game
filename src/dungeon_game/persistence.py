import json
from pathlib import Path
from typing import Dict, Any, Optional

PROFILE_DIR = Path.home() / ".dungeon_game"
PROFILE_DIR.mkdir(parents=True, exist_ok=True)

PROGRESS_FILE = PROFILE_DIR / "progress.json"


class LocalProgress:
    """Simple JSON-based progress store per-username."""

    @staticmethod
    def save_progress(username: str, data: Dict[str, Any]) -> bool:
        try:
            all_data: Dict[str, Any] = {}
            if PROGRESS_FILE.exists():
                try:
                    all_data = json.loads(PROGRESS_FILE.read_text())
                except Exception:
                    all_data = {}
            all_data[username] = data
            PROGRESS_FILE.write_text(json.dumps(all_data, indent=2))
            return True
        except Exception:
            return False

    @staticmethod
    def load_progress(username: str) -> Dict[str, Any]:
        if not PROGRESS_FILE.exists():
            return {}
        try:
            all_data = json.loads(PROGRESS_FILE.read_text())
            return all_data.get(username, {})
        except Exception:
            return {}