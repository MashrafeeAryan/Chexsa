"""Durable local task snapshots. No browser handles or screenshots are serialized."""

import json
import os
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .models import TaskSpec, TaskState


class TaskJournal:
    def __init__(self, path=None):
        root = Path(os.environ.get("CHEXSA_STATE_DIR", str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Chexsa")))
        self.path = Path(path) if path else root / "tasks.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=5)
        self.connection.execute("CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL, updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        self.connection.commit()

    def save(self, state):
        payload = json.dumps(asdict(state), ensure_ascii=False)
        with self.connection:
            self.connection.execute("INSERT INTO tasks(id,status,payload) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,payload=excluded.payload,updated=CURRENT_TIMESTAMP", (state.id, state.status, payload))

    def load(self, task_id):
        row = self.connection.execute("SELECT payload FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown task {task_id}.")
        data = json.loads(row[0])
        data["spec"] = TaskSpec(**data["spec"])
        return TaskState(**data)

    def recent(self, limit=10):
        return [{"id": row[0], "status": row[1], "updated": row[2]} for row in self.connection.execute("SELECT id,status,updated FROM tasks ORDER BY updated DESC,rowid DESC LIMIT ?", (limit,))]

    def close(self):
        self.connection.close()
