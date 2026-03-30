from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class TaskStorage:
    def __init__(self, db_path: str = "ai_scheduler.db"):
        self.db_path = db_path
        self._conn = None
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    complexity REAL DEFAULT 1.0,
                    estimated_duration REAL DEFAULT 60.0,
                    deadline TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    duration REAL,
                    success INTEGER,
                    cpu_avg REAL,
                    memory_avg REAL,
                    error TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    task_id TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    PRIMARY KEY (task_id, depends_on),
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
                    FOREIGN KEY (depends_on) REFERENCES tasks(task_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS priority_scores (
                    task_id TEXT PRIMARY KEY,
                    deadline_score REAL,
                    complexity_score REAL,
                    history_score REAL,
                    total_score REAL,
                    calculated_at TEXT,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                )
            """)

    def save_task(
        self,
        task_id: str,
        name: str,
        complexity: float = 1.0,
        estimated_duration: float = 60.0,
        deadline: datetime | None = None,
        status: str = "pending",
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks (task_id, name, complexity, estimated_duration, deadline, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (task_id, name, complexity, estimated_duration, deadline.isoformat() if deadline else None, status, datetime.now().isoformat()))

    def get_task(self, task_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def get_all_tasks(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def update_task_status(self, task_id: str, status: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ?", 
                        (status, datetime.now().isoformat(), task_id))

    def save_execution(
        self,
        task_id: str,
        started_at: datetime,
        completed_at: datetime,
        duration: float,
        success: bool,
        cpu_avg: float = 0.0,
        memory_avg: float = 0.0,
        error: str | None = None,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO task_executions (task_id, started_at, completed_at, duration, success, cpu_avg, memory_avg, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (task_id, started_at.isoformat(), completed_at.isoformat(), duration, int(success), cpu_avg, memory_avg, error))

    def get_task_executions(self, task_id: str, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM task_executions WHERE task_id = ? ORDER BY started_at DESC LIMIT ?
            """, (task_id, limit)).fetchall()
            return [dict(row) for row in rows]

    def get_execution_stats(self, task_id: str | None = None) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if task_id:
                total = conn.execute("SELECT COUNT(*) as count FROM task_executions WHERE task_id = ?", [task_id]).fetchone()["count"]
                successful = conn.execute("SELECT COUNT(*) as count FROM task_executions WHERE task_id = ? AND success = 1", [task_id]).fetchone()["count"]
                avg_duration = conn.execute("SELECT AVG(duration) as avg FROM task_executions WHERE task_id = ?", [task_id]).fetchone()["avg"] or 0
                avg_cpu = conn.execute("SELECT AVG(cpu_avg) as avg FROM task_executions WHERE task_id = ?", [task_id]).fetchone()["avg"] or 0
                avg_memory = conn.execute("SELECT AVG(memory_avg) as avg FROM task_executions WHERE task_id = ?", [task_id]).fetchone()["avg"] or 0
            else:
                total = conn.execute("SELECT COUNT(*) as count FROM task_executions").fetchone()["count"]
                successful = conn.execute("SELECT COUNT(*) as count FROM task_executions WHERE success = 1").fetchone()["count"]
                avg_duration = conn.execute("SELECT AVG(duration) as avg FROM task_executions").fetchone()["avg"] or 0
                avg_cpu = conn.execute("SELECT AVG(cpu_avg) as avg FROM task_executions").fetchone()["avg"] or 0
                avg_memory = conn.execute("SELECT AVG(memory_avg) as avg FROM task_executions").fetchone()["avg"] or 0
            
            return {
                "total_executions": total,
                "successful_executions": successful,
                "failed_executions": total - successful,
                "success_rate": round((successful / total * 100), 2) if total > 0 else 0,
                "avg_duration": round(avg_duration, 2),
                "avg_cpu_usage": round(avg_cpu, 2),
                "avg_memory_usage": round(avg_memory, 2),
            }

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO task_dependencies (task_id, depends_on)
                VALUES (?, ?)
            """, (task_id, depends_on))

    def get_dependencies(self, task_id: str) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT depends_on FROM task_dependencies WHERE task_id = ?", (task_id,)).fetchall()
            return [row[0] for row in rows]

    def get_dependent_tasks(self, task_id: str) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT task_id FROM task_dependencies WHERE depends_on = ?", (task_id,)).fetchall()
            return [row[0] for row in rows]

    def save_priority_scores(self, task_id: str, deadline_score: float, complexity_score: float, history_score: float, total_score: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO priority_scores (task_id, deadline_score, complexity_score, history_score, total_score, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (task_id, deadline_score, complexity_score, history_score, total_score, datetime.now().isoformat()))

    def get_priority_scores(self, task_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM priority_scores WHERE task_id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def export_data(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            tasks = [dict(row) for row in conn.execute("SELECT * FROM tasks").fetchall()]
            executions = [dict(row) for row in conn.execute("SELECT * FROM task_executions").fetchall()]
            dependencies = [dict(row) for row in conn.execute("SELECT * FROM task_dependencies").fetchall()]
            
            return {
                "exported_at": datetime.now().isoformat(),
                "tasks": tasks,
                "executions": executions,
                "dependencies": dependencies,
            }

    def clear_old_executions(self, days: int = 30) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cutoff = datetime.now().isoformat()
            cursor = conn.execute("DELETE FROM task_executions WHERE completed_at < datetime(?, '-' || ? || ' days')",
                                (cutoff, days))
            return cursor.rowcount
