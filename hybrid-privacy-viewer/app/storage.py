import json
import re
from io import StringIO
from pathlib import Path

import pandas as pd

RUN_ID = re.compile(r"^\d{8}-\d{2}$")


class InvalidRunId(ValueError):
    pass


def check_run_id(run_id: str) -> str:
    if not RUN_ID.match(run_id):
        raise InvalidRunId(run_id)
    return run_id


class LocalStore:
    """Read-only access to a folder laid out like the clean bucket."""

    def __init__(self, root: Path, prefix: str):
        self.root = Path(root)
        self.prefix = prefix.rstrip("/")

    def run_ids(self) -> list[str]:
        base = self.root / self.prefix
        if not base.exists():
            return []
        ids = [p.name.removeprefix("run_id=") for p in base.glob("run_id=*") if p.is_dir()]
        return sorted((i for i in ids if RUN_ID.match(i)), reverse=True)

    def _path(self, run_id: str, name: str) -> Path:
        return self.root / self.prefix / f"run_id={check_run_id(run_id)}" / name

    def exists(self, run_id: str, name: str) -> bool:
        return self._path(run_id, name).is_file()

    def read_text(self, run_id: str, name: str) -> str | None:
        path = self._path(run_id, name)
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def read_json(self, run_id: str, name: str) -> dict | None:
        text = self.read_text(run_id, name)
        return json.loads(text) if text is not None else None

    def read_csv(self, run_id: str, name: str) -> pd.DataFrame | None:
        text = self.read_text(run_id, name)
        return pd.read_csv(StringIO(text)) if text is not None else None
