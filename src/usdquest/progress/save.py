"""SQLite progress store. One row per mission completion."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MissionRecord:
    mission_id: str
    completed_at: str  # ISO 8601
    xp: int


class ProgressStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS completions (
                    mission_id   TEXT PRIMARY KEY,
                    completed_at TEXT NOT NULL,
                    xp           INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def record_completion(self, mission_id: str, xp: int) -> None:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO completions (mission_id, completed_at, xp) VALUES (?, ?, ?)",
                (mission_id, now, xp),
            )

    def is_complete(self, mission_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT 1 FROM completions WHERE mission_id = ? LIMIT 1", (mission_id,)
            )
            return cur.fetchone() is not None

    def total_xp(self) -> int:
        with self._connect() as conn:
            cur = conn.execute("SELECT COALESCE(SUM(xp), 0) FROM completions")
            (total,) = cur.fetchone()
            return int(total)

    def all(self) -> list[MissionRecord]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT mission_id, completed_at, xp FROM completions ORDER BY completed_at"
            )
            return [MissionRecord(*row) for row in cur.fetchall()]


def default_db_path() -> Path:
    from os import environ

    base = environ.get("USDQUEST_DATA_DIR")
    if base:
        return Path(base) / "progress.db"
    # Windows: %LOCALAPPDATA%\USDQuest\progress.db ; other: ~/.local/share/usdquest/progress.db
    localappdata = environ.get("LOCALAPPDATA")
    if localappdata:
        return Path(localappdata) / "USDQuest" / "progress.db"
    return Path.home() / ".local" / "share" / "usdquest" / "progress.db"
