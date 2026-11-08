import json
from pathlib import Path


class ConfigManager:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict = {}
        if path.exists():
            self.data = json.loads(path.read_text())

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        self.data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))
