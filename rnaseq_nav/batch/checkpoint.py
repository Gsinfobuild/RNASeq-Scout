"""Checkpoint persistence for RNA-Seq Scout batch execution."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BatchCheckpoint:
    """Persist batch state so interrupted jobs can resume safely."""

    VERSION = 1

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def save(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        document = {
            "version": self.VERSION,
            **payload,
        }

        temporary = self.path.with_suffix(
            self.path.suffix + ".tmp"
        )

        temporary.write_text(
            json.dumps(
                document,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            encoding="utf-8",
        )

        temporary.replace(self.path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}

        return json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )
