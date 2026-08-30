"""SQLite persistence for users, municipalities, zones, and reports."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "sargassum.db"

_local = threading.local()


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_conn() -> sqlite3.Connection:
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = connect()
        _local.conn = conn
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS municipalities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            region TEXT NOT NULL DEFAULT '',
            lat REAL NOT NULL DEFAULT 18.3256,
            lng REAL NOT NULL DEFAULT -65.6524,
            crew_budget INTEGER NOT NULL DEFAULT 8,
            exploration_c REAL NOT NULL DEFAULT 0.72,
            forecast_weight REAL NOT NULL DEFAULT 0.35,
            horizon TEXT NOT NULL DEFAULT 'h24',
            zones_json TEXT NOT NULL,
            event_log_json TEXT NOT NULL DEFAULT '[]',
            previous_cleanup_json TEXT NOT NULL DEFAULT '[]',
            previous_scout_json TEXT NOT NULL DEFAULT '[]',
            weather_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('citizen', 'operations')),
            municipality_id INTEGER NOT NULL REFERENCES municipalities(id),
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            municipality_id INTEGER NOT NULL REFERENCES municipalities(id),
            user_id INTEGER REFERENCES users(id),
            zone_id TEXT NOT NULL,
            volume TEXT NOT NULL,
            submitter_type TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'citizen',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            municipality_id INTEGER NOT NULL REFERENCES municipalities(id),
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            zone_id TEXT,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def dumps(value: Any) -> str:
    return json.dumps(value, default=str)


def loads(value: str, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)
