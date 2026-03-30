from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

RICH_AVAILABLE = False
Console = None
Table = None
Panel = None

try:
    from rich.console import Console as RichConsole
    from rich.table import Table as RichTable
    from rich.panel import Panel as RichPanel
    RICH_AVAILABLE = True
    Console = RichConsole
    Table = RichTable
    Panel = RichPanel
except ImportError:
    pass


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class TaskRecord:
    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    priority_score: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    execution_time: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


class Dashboard:
    def __init__(self, refresh_rate: float = 1.0):
        self.refresh_rate = refresh_rate
        self._tasks: dict[str, TaskRecord] = {}
        self._history: deque[dict] = deque(maxlen=100)
        self._execution_log: deque[dict] = deque(maxlen=1000)
        self._start_time = datetime.now()
        self._console = Console() if RICH_AVAILABLE else None

    def register_task(self, task_id: str, name: str, priority_score: float = 0.0) -> None:
        self._tasks[task_id] = TaskRecord(
            task_id=task_id,
            name=name,
            priority_score=priority_score,
        )

    def start_task(self, task_id: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.RUNNING
            self._tasks[task_id].started_at = datetime.now()

    def update_task_metrics(self, task_id: str, cpu: float, memory: float) -> None:
        if task_id in self._tasks and self._tasks[task_id].status == TaskStatus.RUNNING:
            self._tasks[task_id].cpu_usage = cpu
            self._tasks[task_id].memory_usage = memory

    def complete_task(self, task_id: str, success: bool = True, error: str | None = None) -> None:
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = error
            
            if task.started_at:
                task.execution_time = (task.completed_at - task.started_at).total_seconds()
            
            self._execution_log.append({
                "task_id": task_id,
                "name": task.name,
                "status": task.status.value,
                "execution_time": task.execution_time,
                "cpu_avg": task.cpu_usage,
                "memory_avg": task.memory_usage,
                "timestamp": task.completed_at.isoformat(),
            })

    def pause_task(self, task_id: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.PAUSED

    def resume_task(self, task_id: str) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.PENDING

    def update_priority(self, task_id: str, priority_score: float) -> None:
        if task_id in self._tasks:
            self._tasks[task_id].priority_score = priority_score

    def get_task_summary(self) -> dict:
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        running = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
        paused = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PAUSED)
        
        avg_cpu = 0.0
        avg_memory = 0.0
        running_tasks = [t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]
        if running_tasks:
            avg_cpu = sum(t.cpu_usage for t in running_tasks) / len(running_tasks)
            avg_memory = sum(t.memory_usage for t in running_tasks) / len(running_tasks)
        
        return {
            "total_tasks": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "paused": paused,
            "pending": total - completed - running - failed - paused,
            "avg_cpu_usage": round(avg_cpu, 2),
            "avg_memory_usage": round(avg_memory, 2),
            "uptime": (datetime.now() - self._start_time).total_seconds(),
        }

    def get_task_details(self) -> list[dict]:
        return [
            {
                "task_id": task.task_id,
                "name": task.name,
                "status": task.status.value,
                "priority": task.priority_score,
                "cpu": task.cpu_usage,
                "memory": task.memory_usage,
                "execution_time": task.execution_time,
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.error,
            }
            for task in sorted(self._tasks.values(), key=lambda t: t.priority_score, reverse=True)
        ]

    def get_execution_history(self, limit: int = 50) -> list[dict]:
        return list(self._execution_log)[-limit:]

    def get_success_rate(self) -> float:
        completed_tasks = [e for e in self._execution_log if e["status"] in ["completed", "failed"]]
        if not completed_tasks:
            return 0.0
        successful = sum(1 for e in completed_tasks if e["status"] == "completed")
        return round(successful / len(completed_tasks) * 100, 2)

    def print_console(self) -> None:
        if not self._console:
            print(self.get_summary_text())
            return
        
        self._console.clear()
        
        summary = self.get_task_summary()
        
        summary_table = Table(title="System Summary", show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Tasks", str(summary["total_tasks"]))
        summary_table.add_row("Running", f"[green]{summary['running']}[/green]")
        summary_table.add_row("Completed", f"[blue]{summary['completed']}[/blue]")
        summary_table.add_row("Failed", f"[red]{summary['failed']}[/red]")
        summary_table.add_row("Paused", f"[yellow]{summary['paused']}[/yellow]")
        summary_table.add_row("Success Rate", f"{self.get_success_rate()}%")
        summary_table.add_row("Avg CPU", f"{summary['avg_cpu_usage']}%")
        summary_table.add_row("Avg Memory", f"{summary['avg_memory_usage']}%")
        
        task_table = Table(title="Task Details")
        task_table.add_column("Task", style="cyan")
        task_table.add_column("Status", style="magenta")
        task_table.add_column("Priority", justify="right")
        task_table.add_column("CPU %", justify="right")
        task_table.add_column("Memory %", justify="right")
        task_table.add_column("Time (s)", justify="right")
        
        for task in sorted(self._tasks.values(), key=lambda t: t.priority_score, reverse=True)[:10]:
            status_color = {
                TaskStatus.PENDING: "white",
                TaskStatus.RUNNING: "green",
                TaskStatus.COMPLETED: "blue",
                TaskStatus.FAILED: "red",
                TaskStatus.PAUSED: "yellow",
            }.get(task.status, "white")
            
            task_table.add_row(
                task.name,
                f"[{status_color}]{task.status.value}[/{status_color}]",
                f"{task.priority_score:.1f}",
                f"{task.cpu_usage:.1f}",
                f"{task.memory_usage:.1f}",
                f"{task.execution_time:.2f}" if task.execution_time else "-",
            )
        
        self._console.print(Panel(summary_table, title="[b]Summary[/b]"))
        self._console.print(task_table)

    def get_summary_text(self) -> str:
        summary = self.get_task_summary()
        lines = [
            "=" * 50,
            "AI Scheduler Dashboard",
            "=" * 50,
            f"Total Tasks: {summary['total_tasks']}",
            f"Running: {summary['running']}",
            f"Completed: {summary['completed']}",
            f"Failed: {summary['failed']}",
            f"Paused: {summary['paused']}",
            f"Success Rate: {self.get_success_rate()}%",
            f"Avg CPU: {summary['avg_cpu_usage']}%",
            f"Avg Memory: {summary['avg_memory_usage']}%",
            "=" * 50,
            "Tasks:",
        ]
        
        for task in sorted(self._tasks.values(), key=lambda t: t.priority_score, reverse=True):
            lines.append(
                f"  [{task.status.value}] {task.name} - Priority: {task.priority_score:.1f} | "
                f"CPU: {task.cpu_usage:.1f}% | Mem: {task.memory_usage:.1f}%"
            )
        
        return "\n".join(lines)

    def export_json(self) -> str:
        return json.dumps({
            "summary": self.get_task_summary(),
            "tasks": self.get_task_details(),
            "history": self.get_execution_history(),
            "success_rate": self.get_success_rate(),
            "timestamp": datetime.now().isoformat(),
        }, indent=2)

    def save_report(self, filename: str) -> None:
        with open(filename, "w") as f:
            f.write(self.export_json())
