from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Any


class TaskStatus(Enum):
    PENDING = "pending"
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    task_id: str
    name: str
    func: Callable | None = None
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    result: Any = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3


class TaskDAG:
    def __init__(self):
        self.tasks: dict[str, TaskNode] = {}
        self._execution_order: list[str] = []

    def add_task(
        self,
        task_id: str,
        name: str,
        func: Callable | None = None,
        dependencies: list[str] | None = None,
        max_retries: int = 3,
    ) -> TaskNode:
        node = TaskNode(
            task_id=task_id,
            name=name,
            func=func,
            dependencies=dependencies or [],
            max_retries=max_retries,
        )
        self.tasks[task_id] = node
        
        for dep_id in node.dependencies:
            if dep_id not in self.tasks:
                self.add_task(dep_id, f"Task: {dep_id}")
            if task_id not in self.tasks[dep_id].dependents:
                self.tasks[dep_id].dependents.append(task_id)
        
        return node

    def get_ready_tasks(self) -> list[TaskNode]:
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            if not task.dependencies:
                ready.append(task)
                continue
            
            all_deps_completed = all(
                self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            
            if all_deps_completed:
                ready.append(task)
        
        return ready

    def mark_running(self, task_id: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.RUNNING
            self.tasks[task_id].started_at = datetime.now()

    def mark_completed(self, task_id: str, result: Any = None) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].completed_at = datetime.now()
            self.tasks[task_id].result = result

    def mark_failed(self, task_id: str, error: str) -> None:
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.WAITING
                task.error = f"Retry {task.retry_count}/{task.max_retries}: {error}"
            else:
                task.status = TaskStatus.FAILED
                task.error = error
                task.completed_at = datetime.now()
                
                for dependent_id in task.dependents:
                    self.tasks[dependent_id].status = TaskStatus.SKIPPED

    def get_execution_order(self) -> list[str]:
        if self._execution_order:
            return self._execution_order
        
        visited = set()
        order = []

        def visit(task_id: str) -> None:
            if task_id in visited:
                return
            visited.add(task_id)
            
            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    visit(dep_id)
            
            order.append(task_id)

        for task_id in self.tasks:
            visit(task_id)

        self._execution_order = order
        return order

    def get_parallel_batches(self) -> list[list[str]]:
        batches = []
        completed = set()
        
        while len(completed) < len(self.tasks):
            batch = []
            
            for task_id, task in self.tasks.items():
                if task_id in completed:
                    continue
                if task.status not in [TaskStatus.PENDING, TaskStatus.WAITING]:
                    continue
                
                deps_met = all(dep_id in completed for dep_id in task.dependencies)
                if deps_met:
                    batch.append(task_id)
            
            if not batch:
                break
            
            batches.append(batch)
            for task_id in batch:
                if self.tasks[task_id].status == TaskStatus.COMPLETED:
                    completed.add(task_id)
        
        return batches

    def validate(self) -> tuple[bool, list[str]]:
        errors = []
        
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    errors.append(f"Task '{task_id}' depends on non-existent task '{dep_id}'")
        
        if self._has_cycle():
            errors.append("DAG contains a cycle")
        
        return len(errors) == 0, errors

    def _has_cycle(self) -> bool:
        visited = set()
        rec_stack = set()

        def dfs(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dep_id not in visited:
                        if dfs(dep_id):
                            return True
                    elif dep_id in rec_stack:
                        return True
            
            rec_stack.remove(task_id)
            return False

        for task_id in self.tasks:
            if task_id not in visited:
                if dfs(task_id):
                    return True
        
        return False

    def get_task_info(self, task_id: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {}
        
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status.value,
            "dependencies": task.dependencies,
            "dependents": task.dependents,
            "result": str(task.result)[:100] if task.result else None,
            "error": task.error,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
        }

    def get_dag_info(self) -> dict:
        return {
            "total_tasks": len(self.tasks),
            "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED),
            "skipped": sum(1 for t in self.tasks.values() if t.status == TaskStatus.SKIPPED),
            "execution_order": self.get_execution_order(),
            "parallel_batches": self.get_parallel_batches(),
        }

    def reset(self) -> None:
        for task in self.tasks.values():
            task.status = TaskStatus.PENDING
            task.result = None
            task.error = None
            task.started_at = None
            task.completed_at = None
            task.retry_count = 0
        self._execution_order = []


class DAGExecutor:
    def __init__(self, dag: TaskDAG):
        self.dag = dag
        self._running = False

    async def execute_async(self, max_parallel: int = 5) -> dict:
        import asyncio
        
        self._running = True
        results = {}
        errors = {}
        
        while self._running:
            ready_tasks = self.dag.get_ready_tasks()
            if not ready_tasks:
                break
            
            batch = ready_tasks[:max_parallel]
            batch_results = await asyncio.gather(
                *[self._execute_task_async(task) for task in batch],
                return_exceptions=True
            )
            
            for task, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    errors[task.task_id] = str(result)
                else:
                    results[task.task_id] = result
        
        return {"results": results, "errors": errors, "completed": self.dag.get_dag_info()}

    async def _execute_task_async(self, task: TaskNode) -> Any:
        import asyncio
        
        self.dag.mark_running(task.task_id)
        
        try:
            if task.func:
                if asyncio.iscoroutinefunction(task.func):
                    result = await task.func()
                else:
                    result = task.func()
            else:
                result = None
            
            self.dag.mark_completed(task.task_id, result)
            return result
        except Exception as e:
            self.dag.mark_failed(task.task_id, str(e))
            raise

    def execute(self, max_parallel: int = 5) -> dict:
        import concurrent.futures
        
        self._running = True
        results = {}
        errors = {}
        
        while self._running:
            ready_tasks = self.dag.get_ready_tasks()
            if not ready_tasks:
                break
            
            batch = ready_tasks[:max_parallel]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
                futures = {executor.submit(self._execute_task, task): task for task in batch}
                
                for future in concurrent.futures.as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                        results[task.task_id] = result
                    except Exception as e:
                        errors[task.task_id] = str(e)
        
        return {"results": results, "errors": errors, "completed": self.dag.get_dag_info()}

    def _execute_task(self, task: TaskNode) -> Any:
        self.dag.mark_running(task.task_id)
        
        try:
            if task.func:
                result = task.func()
            else:
                result = None
            
            self.dag.mark_completed(task.task_id, result)
            return result
        except Exception as e:
            self.dag.mark_failed(task.task_id, str(e))
            raise
