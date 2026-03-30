from __future__ import annotations

import time
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


@dataclass
class ResourceUsage:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    task_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_mb": self.memory_mb,
            "task_id": self.task_id,
        }


class ResourceMonitor:
    def __init__(self, max_history: int = 1000, sampling_interval: float = 0.5):
        self.max_history = max_history
        self.sampling_interval = sampling_interval
        self._history: deque[ResourceUsage] = deque(maxlen=max_history)
        self._task_history: dict[str, deque[ResourceUsage]] = {}
        self._active_tasks: dict[str, list[ResourceUsage]] = {}
        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if self._monitoring:
            return
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop(self) -> None:
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
            self._monitor_thread = None

    def _get_system_usage(self) -> tuple[float, float, float]:
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            return cpu, memory.percent, memory.used / (1024 * 1024)
        except ImportError:
            return self._get_fallback_usage()

    def _get_fallback_usage(self) -> tuple[float, float, float]:
        import os
        cpu = 0.0
        memory_mb = 0.0
        
        try:
            load = os.getloadavg()  # type: ignore[attr-defined]
            cpu_count = os.cpu_count() or 1
            cpu = (load[0] / cpu_count * 100)
        except Exception:
            pass
        
        try:
            import resource
            mem_info = resource.getrusage(resource.RUSAGE_SELF)  # type: ignore[attr-defined]
            memory_mb = mem_info.ru_maxrss / 1024
        except Exception:
            pass
        
        return min(cpu, 100.0), 0.0, memory_mb

    def _monitor_loop(self) -> None:
        while self._monitoring:
            usage = ResourceUsage(
                timestamp=datetime.now(),
                cpu_percent=0,
                memory_percent=0,
                memory_mb=0,
            )
            
            cpu, mem_percent, mem_mb = self._get_system_usage()
            usage.cpu_percent = cpu
            usage.memory_percent = mem_percent
            usage.memory_mb = mem_mb
            
            with self._lock:
                self._history.append(usage)
                
                for task_id in list(self._active_tasks.keys()):
                    self._active_tasks[task_id].append(usage)
            
            time.sleep(self.sampling_interval)

    def start_task_tracking(self, task_id: str) -> None:
        with self._lock:
            self._active_tasks[task_id] = []
            self._task_history[task_id] = deque(maxlen=self.max_history)

    def stop_task_tracking(self, task_id: str) -> None:
        with self._lock:
            if task_id in self._active_tasks:
                history = self._active_tasks.pop(task_id)
                history_deque: deque[ResourceUsage] = deque(history, maxlen=self.max_history)
                self._task_history[task_id] = history_deque

    def record_sample(self, task_id: str | None = None) -> ResourceUsage:
        usage = ResourceUsage(
            timestamp=datetime.now(),
            cpu_percent=0,
            memory_percent=0,
            memory_mb=0,
        )
        
        cpu, mem_percent, mem_mb = self._get_system_usage()
        usage.cpu_percent = cpu
        usage.memory_percent = mem_percent
        usage.memory_mb = mem_mb
        usage.task_id = task_id
        
        with self._lock:
            self._history.append(usage)
            if task_id and task_id in self._active_tasks:
                self._active_tasks[task_id].append(usage)
        
        return usage

    def get_current_usage(self) -> ResourceUsage:
        return self.record_sample()

    def get_history(self, limit: int = 100) -> list[ResourceUsage]:
        with self._lock:
            return list(self._history)[-limit:]

    def get_task_usage(self, task_id: str) -> dict:
        with self._lock:
            history = list(self._task_history.get(task_id, []))
        
        if not history:
            return {"task_id": task_id, "samples": 0, "avg_cpu": 0, "avg_memory": 0}
        
        avg_cpu = sum(u.cpu_percent for u in history) / len(history)
        avg_memory = sum(u.memory_percent for u in history) / len(history)
        max_cpu = max(u.cpu_percent for u in history)
        max_memory = max(u.memory_percent for u in history)
        
        return {
            "task_id": task_id,
            "samples": len(history),
            "avg_cpu": round(avg_cpu, 2),
            "avg_memory": round(avg_memory, 2),
            "max_cpu": round(max_cpu, 2),
            "max_memory": round(max_memory, 2),
            "total_memory_mb": round(sum(u.memory_mb for u in history) / len(history), 2),
        }

    def get_all_tasks_usage(self) -> dict[str, dict]:
        with self._lock:
            return {task_id: self.get_task_usage(task_id) for task_id in self._task_history}

    def get_system_summary(self) -> dict:
        history = self.get_history(100)
        if not history:
            return {
                "current_cpu": 0,
                "current_memory": 0,
                "avg_cpu": 0,
                "avg_memory": 0,
            }
        
        latest = history[-1]
        return {
            "current_cpu": round(latest.cpu_percent, 2),
            "current_memory": round(latest.memory_percent, 2),
            "current_memory_mb": round(latest.memory_mb, 2),
            "avg_cpu": round(sum(u.cpu_percent for u in history) / len(history), 2),
            "avg_memory": round(sum(u.memory_percent for u in history) / len(history), 2),
            "max_cpu": round(max(u.cpu_percent for u in history), 2),
            "max_memory": round(max(u.memory_percent for u in history), 2),
        }

    def check_resource_available(self, required_cpu: float = 0, required_memory: float = 0) -> bool:
        current = self.get_current_usage()
        return current.cpu_percent + required_cpu < 95 and current.memory_percent + required_memory < 95


class ResourceAwareScheduler:
    def __init__(self, resource_monitor: ResourceMonitor):
        self.monitor = resource_monitor
        self._paused_tasks: set[str] = set()

    def should_run_task(self, task_id: str, required_resources: tuple[float, float] = (10, 10)) -> bool:
        required_cpu, required_memory = required_resources
        if not self.monitor.check_resource_available(required_cpu, required_memory):
            self._paused_tasks.add(task_id)
            return False
        
        if task_id in self._paused_tasks:
            if self.monitor.check_resource_available(required_cpu, required_memory):
                self._paused_tasks.discard(task_id)
        
        return True

    def get_paused_tasks(self) -> list[str]:
        return list(self._paused_tasks)

    def is_task_paused(self, task_id: str) -> bool:
        return task_id in self._paused_tasks
