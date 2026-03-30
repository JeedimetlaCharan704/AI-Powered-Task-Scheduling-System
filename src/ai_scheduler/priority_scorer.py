from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable


@dataclass
class PriorityConfig:
    deadline_weight: float = 0.4
    complexity_weight: float = 0.3
    history_weight: float = 0.3

    max_deadline_score: float = 100.0
    max_complexity_score: float = 10.0
    max_execution_time_score: float = 300.0


@dataclass
class TaskMetrics:
    task_id: str
    complexity: float = 1.0
    estimated_duration: float = 60.0
    deadline: datetime | None = None
    
    execution_times: list[float] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    last_executed: datetime | None = None

    def add_execution(self, duration: float, success: bool) -> None:
        self.execution_times.append(duration)
        if len(self.execution_times) > 100:
            self.execution_times.pop(0)
        self.last_executed = datetime.now()
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def get_avg_execution_time(self) -> float:
        if not self.execution_times:
            return self.estimated_duration
        return sum(self.execution_times) / len(self.execution_times)


class AIPriorityScorer:
    def __init__(self, config: PriorityConfig | None = None):
        self.config = config or PriorityConfig()
        self.task_metrics: dict[str, TaskMetrics] = {}

    def register_task(
        self,
        task_id: str,
        complexity: float = 1.0,
        estimated_duration: float = 60.0,
        deadline: datetime | None = None,
    ) -> None:
        self.task_metrics[task_id] = TaskMetrics(
            task_id=task_id,
            complexity=complexity,
            estimated_duration=estimated_duration,
            deadline=deadline,
        )

    def record_execution(self, task_id: str, duration: float, success: bool = True) -> None:
        if task_id not in self.task_metrics:
            self.register_task(task_id)
        self.task_metrics[task_id].add_execution(duration, success)

    def calculate_deadline_score(self, task_id: str) -> float:
        metrics = self.task_metrics.get(task_id)
        if not metrics or not metrics.deadline:
            return 50.0
        
        now = datetime.now()
        time_until_deadline = (metrics.deadline - now).total_seconds()
        
        if time_until_deadline <= 0:
            return self.config.max_deadline_score
        
        hours_until_deadline = time_until_deadline / 3600
        score = self.config.max_deadline_score * (1 - (hours_until_deadline / 168))
        return max(0, min(score, self.config.max_deadline_score))

    def calculate_complexity_score(self, task_id: str) -> float:
        metrics = self.task_metrics.get(task_id)
        if not metrics:
            return 5.0
        return min(metrics.complexity, self.config.max_complexity_score)

    def calculate_history_score(self, task_id: str) -> float:
        metrics = self.task_metrics.get(task_id)
        if not metrics:
            return 50.0
        
        avg_time = metrics.get_avg_execution_time()
        success_rate = 0.0
        total = metrics.success_count + metrics.failure_count
        if total > 0:
            success_rate = metrics.success_count / total
        
        time_score = min(avg_time, self.config.max_execution_time_score)
        time_score = (1 - time_score / self.config.max_execution_time_score) * 50
        
        return time_score * success_rate

    def get_priority_score(self, task_id: str) -> float:
        deadline_score = self.calculate_deadline_score(task_id)
        complexity_score = self.calculate_complexity_score(task_id)
        history_score = self.calculate_history_score(task_id)
        
        priority = (
            deadline_score * self.config.deadline_weight +
            complexity_score * self.config.complexity_weight +
            history_score * self.config.history_weight
        )
        
        return round(priority, 2)

    def get_task_ranking(self) -> list[tuple[str, float]]:
        rankings = [(task_id, self.get_priority_score(task_id)) for task_id in self.task_metrics]
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def suggest_execution_order(self, task_ids: list[str]) -> list[str]:
        scored = [(task_id, self.get_priority_score(task_id)) for task_id in task_ids]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [task_id for task_id, _ in scored]

    def get_task_info(self, task_id: str) -> dict:
        metrics = self.task_metrics.get(task_id)
        if not metrics:
            return {}
        
        return {
            "task_id": task_id,
            "priority_score": self.get_priority_score(task_id),
            "deadline_score": self.calculate_deadline_score(task_id),
            "complexity_score": self.calculate_complexity_score(task_id),
            "history_score": self.calculate_history_score(task_id),
            "avg_execution_time": metrics.get_avg_execution_time(),
            "success_rate": metrics.success_count / (metrics.success_count + metrics.failure_count) if (metrics.success_count + metrics.failure_count) > 0 else 0,
            "deadline": metrics.deadline.isoformat() if metrics.deadline else None,
            "complexity": metrics.complexity,
            "last_executed": metrics.last_executed.isoformat() if metrics.last_executed else None,
        }
