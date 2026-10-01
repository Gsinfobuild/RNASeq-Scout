import json
from pathlib import Path
from typing import Any, Dict, List


class BatchCheckpoint:
    VERSION = 2

    def __init__(self, path: str):
        self.path = Path(path)

    def save(self, items: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
        payload = {
            "version": self.VERSION,
            "config": config,
            "items": items,
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)

        temporary = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        temporary.write_text(
            json.dumps(payload, indent=2, default=str),
            encoding="utf-8",
        )

        temporary.replace(self.path)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}

        return json.loads(
            self.path.read_text(encoding="utf-8")
        )

    def exists(self) -> bool:
        return self.path.exists()
