from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ai_scheduler.priority_scorer import AIPriorityScorer, PriorityConfig
from ai_scheduler.resource_monitor import ResourceMonitor, ResourceAwareScheduler
from ai_scheduler.dashboard import Dashboard
from ai_scheduler.storage import TaskStorage
from ai_scheduler.dag import TaskDAG, DAGExecutor


app = FastAPI(title="AI Scheduler API", version="1.0.0")

storage = TaskStorage()
priority_scorer = AIPriorityScorer()
resource_monitor = ResourceMonitor()
resource_scheduler = ResourceAwareScheduler(resource_monitor)
dashboard = Dashboard()
dag = TaskDAG()

active_websockets: list[WebSocket] = []


class TaskCreate(BaseModel):
    task_id: str
    name: str
    complexity: float = 1.0
    estimated_duration: float = 60.0
    deadline: str | None = None
    dependencies: list[str] | None = None


class TaskExecute(BaseModel):
    task_id: str


class TaskUpdate(BaseModel):
    status: str | None = None


class DAGCreate(BaseModel):
    tasks: list[TaskCreate]


class DashboardResponse(BaseModel):
    summary: dict
    tasks: list[dict]
    system: dict


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Scheduler Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/htmx.org@1.9.10"></script>
        <style>
            .pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
            .card { transition: all 0.3s ease; }
            .card:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen">
        <nav class="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 shadow-lg">
            <div class="container mx-auto flex justify-between items-center">
                <h1 class="text-2xl font-bold">AI Scheduler Dashboard</h1>
                <div class="flex gap-4">
                    <span id="connection-status" class="px-3 py-1 bg-green-500 rounded-full text-sm">Connected</span>
                </div>
            </div>
        </nav>
        
        <div class="container mx-auto p-6">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div class="card bg-white rounded-xl shadow p-6">
                    <h3 class="text-gray-500 text-sm">Total Tasks</h3>
                    <p id="stat-total" class="text-3xl font-bold text-blue-600">0</p>
                </div>
                <div class="card bg-white rounded-xl shadow p-6">
                    <h3 class="text-gray-500 text-sm">Running</h3>
                    <p id="stat-running" class="text-3xl font-bold text-green-600">0</p>
                </div>
                <div class="card bg-white rounded-xl shadow p-6">
                    <h3 class="text-gray-500 text-sm">Completed</h3>
                    <p id="stat-completed" class="text-3xl font-bold text-purple-600">0</p>
                </div>
                <div class="card bg-white rounded-xl shadow p-6">
                    <h3 class="text-gray-500 text-sm">Success Rate</h3>
                    <p id="stat-success" class="text-3xl font-bold text-yellow-600">0%</p>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div class="lg:col-span-2">
                    <div class="bg-white rounded-xl shadow p-6 mb-6">
                        <h2 class="text-xl font-bold mb-4">Task Queue</h2>
                        <div id="task-list" class="space-y-3">
                            <p class="text-gray-500 text-center py-8">No tasks yet. Add some tasks below!</p>
                        </div>
                    </div>
                    
                    <div class="bg-white rounded-xl shadow p-6">
                        <h2 class="text-xl font-bold mb-4">Add New Task</h2>
                        <form id="task-form" hx-post="/api/tasks" hx-target="#task-list" hx-swap="afterbegin" class="space-y-4">
                            <div class="grid grid-cols-2 gap-4">
                                <input type="text" name="task_id" placeholder="Task ID" required class="border rounded-lg px-4 py-2">
                                <input type="text" name="name" placeholder="Task Name" required class="border rounded-lg px-4 py-2">
                            </div>
                            <div class="grid grid-cols-3 gap-4">
                                <input type="number" name="complexity" placeholder="Complexity (1-10)" min="1" max="10" value="1" class="border rounded-lg px-4 py-2">
                                <input type="number" name="estimated_duration" placeholder="Duration (seconds)" value="60" class="border rounded-lg px-4 py-2">
                                <input type="datetime-local" name="deadline" class="border rounded-lg px-4 py-2">
                            </div>
                            <input type="text" name="dependencies" placeholder="Dependencies (comma-separated)" class="w-full border rounded-lg px-4 py-2">
                            <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition">
                                Add Task
                            </button>
                        </form>
                    </div>
                </div>

                <div class="space-y-6">
                    <div class="bg-white rounded-xl shadow p-6">
                        <h2 class="text-xl font-bold mb-4">System Resources</h2>
                        <div class="space-y-4">
                            <div>
                                <div class="flex justify-between mb-1">
                                    <span class="text-sm text-gray-600">CPU Usage</span>
                                    <span id="cpu-value" class="text-sm font-bold">0%</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-3">
                                    <div id="cpu-bar" class="bg-blue-600 h-3 rounded-full transition-all" style="width: 0%"></div>
                                </div>
                            </div>
                            <div>
                                <div class="flex justify-between mb-1">
                                    <span class="text-sm text-gray-600">Memory Usage</span>
                                    <span id="memory-value" class="text-sm font-bold">0%</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-3">
                                    <div id="memory-bar" class="bg-green-600 h-3 rounded-full transition-all" style="width: 0%"></div>
                                </div>
                            </div>
                            <div class="pt-4 border-t">
                                <h3 class="font-semibold mb-2">Task Priority Ranking</h3>
                                <div id="priority-list" class="text-sm space-y-2"></div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl shadow p-6">
                        <h2 class="text-xl font-bold mb-4">Quick Actions</h2>
                        <div class="space-y-2">
                            <button onclick="executeNext()" class="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition">
                                Execute Next Task
                            </button>
                            <button onclick="clearCompleted()" class="w-full bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700 transition">
                                Clear Completed
                            </button>
                            <button onclick="exportData()" class="w-full bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 transition">
                                Export Data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = () => document.getElementById('connection-status').textContent = 'Connected';
            ws.onclose = () => {
                document.getElementById('connection-status').textContent = 'Disconnected';
                document.getElementById('connection-status').classList.remove('bg-green-500');
                document.getElementById('connection-status').classList.add('bg-red-500');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            function updateDashboard(data) {
                const summary = data.summary;
                document.getElementById('stat-total').textContent = summary.total_tasks || 0;
                document.getElementById('stat-running').textContent = summary.running || 0;
                document.getElementById('stat-completed').textContent = summary.completed || 0;
                document.getElementById('stat-success').textContent = (data.success_rate || 0) + '%';
                
                const system = data.system || {};
                document.getElementById('cpu-value').textContent = (system.current_cpu || 0) + '%';
                document.getElementById('memory-value').textContent = (system.current_memory || 0) + '%';
                document.getElementById('cpu-bar').style.width = (system.current_cpu || 0) + '%';
                document.getElementById('memory-bar').style.width = (system.current_memory || 0) + '%';
                
                const tasks = data.tasks || [];
                const taskList = document.getElementById('task-list');
                if (tasks.length === 0) {
                    taskList.innerHTML = '<p class="text-gray-500 text-center py-8">No tasks yet!</p>';
                } else {
                    taskList.innerHTML = tasks.slice(0, 10).map(task => `
                        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <span class="font-semibold">${task.name || task.task_id}</span>
                                <span class="ml-2 px-2 py-1 text-xs rounded ${getStatusClass(task.status)}">${task.status || 'pending'}</span>
                            </div>
                            <div class="text-right">
                                <span class="text-sm text-gray-500">Priority: ${(task.priority || 0).toFixed(1)}</span>
                            </div>
                        </div>
                    `).join('');
                }
                
                const priorityList = document.getElementById('priority-list');
                priorityList.innerHTML = tasks.slice(0, 5).map((task, i) => `
                    <div class="flex justify-between">
                        <span>${i + 1}. ${task.name || task.task_id}</span>
                        <span class="font-bold">${(task.priority || 0).toFixed(1)}</span>
                    </div>
                `).join('');
            }
            
            function getStatusClass(status) {
                const classes = {
                    'pending': 'bg-gray-200 text-gray-700',
                    'running': 'bg-yellow-200 text-yellow-700 pulse',
                    'completed': 'bg-green-200 text-green-700',
                    'failed': 'bg-red-200 text-red-700',
                    'paused': 'bg-orange-200 text-orange-700',
                };
                return classes[status] || classes.pending;
            }
            
            async function executeNext() {
                await fetch('/api/tasks/execute-next', { method: 'POST' });
            }
            
            async function clearCompleted() {
                await fetch('/api/tasks/completed', { method: 'DELETE' });
                location.reload();
            }
            
            async function exportData() {
                const response = await fetch('/api/export');
                const data = await response.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'ai_scheduler_export.json';
                a.click();
            }
            
            setInterval(() => {
                fetch('/api/dashboard').then(r => r.json()).then(updateDashboard);
            }, 2000);
        </script>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)


async def broadcast_update():
    if active_websockets:
        data = json.dumps({
            "summary": dashboard.get_task_summary(),
            "tasks": dashboard.get_task_details(),
            "system": resource_monitor.get_system_summary(),
            "success_rate": dashboard.get_success_rate(),
        })
        for ws in active_websockets[:]:
            try:
                await ws.send_text(data)
            except:
                active_websockets.remove(ws)


@app.post("/api/tasks")
async def create_task(task: TaskCreate):
    task_id = task.task_id
    deadline = datetime.fromisoformat(task.deadline) if task.deadline else None
    
    priority_scorer.register_task(
        task_id=task_id,
        complexity=task.complexity,
        estimated_duration=task.estimated_duration,
        deadline=deadline,
    )
    
    storage.save_task(
        task_id=task_id,
        name=task.name,
        complexity=task.complexity,
        estimated_duration=task.estimated_duration,
        deadline=deadline,
    )
    
    dashboard.register_task(
        task_id=task_id,
        name=task.name,
        priority_score=priority_scorer.get_priority_score(task_id),
    )
    
    if task.dependencies:
        for dep_id in task.dependencies:
            storage.add_dependency(task_id, dep_id)
            dag.add_task(dep_id, f"Task: {dep_id}")
    
    dag.add_task(task_id, task.name, dependencies=task.dependencies)
    
    await broadcast_update()
    return {"status": "success", "task_id": task_id}


@app.get("/api/tasks")
async def list_tasks():
    tasks = storage.get_all_tasks()
    priority_scores = {}
    for task in tasks:
        task_id = task["task_id"]
        priority_scores[task_id] = priority_scorer.get_priority_score(task_id)
    
    tasks_with_priority = [
        {**task, "priority": priority_scores.get(task["task_id"], 0)}
        for task in tasks
    ]
    
    return {"tasks": tasks_with_priority}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task["priority"] = priority_scorer.get_priority_score(task_id)
    task["executions"] = storage.get_task_executions(task_id)
    task["stats"] = storage.get_execution_stats(task_id)
    task["dependencies"] = storage.get_dependencies(task_id)
    
    return task


@app.post("/api/tasks/execute-next")
async def execute_next_task():
    task_ids = [t["task_id"] for t in storage.get_all_tasks() if t["status"] == "pending"]
    if not task_ids:
        return {"status": "no_tasks", "message": "No pending tasks"}
    
    execution_order = priority_scorer.suggest_execution_order(task_ids)
    task_id = execution_order[0]
    
    dashboard.start_task(task_id)
    storage.update_task_status(task_id, "running")
    
    resource_monitor.start_task_tracking(task_id)
    
    start_time = time.time()
    success = True
    error = None
    
    try:
        await asyncio.sleep(2)
    except Exception as e:
        success = False
        error = str(e)
    
    duration = time.time() - start_time
    resource_monitor.stop_task_tracking(task_id)
    
    usage = resource_monitor.get_task_usage(task_id)
    
    storage.save_execution(
        task_id=task_id,
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration=duration,
        success=success,
        cpu_avg=usage["avg_cpu"],
        memory_avg=usage["avg_memory"],
        error=error,
    )
    
    dashboard.update_task_metrics(task_id, usage["avg_cpu"], usage["avg_memory"])
    dashboard.complete_task(task_id, success=success, error=error)
    storage.update_task_status(task_id, "completed" if success else "failed")
    
    priority_scorer.record_execution(task_id, duration, success)
    dashboard.update_priority(task_id, priority_scorer.get_priority_score(task_id))
    
    await broadcast_update()
    return {"status": "executed", "task_id": task_id, "duration": duration}


@app.delete("/api/tasks/completed")
async def clear_completed():
    for task in storage.get_all_tasks():
        if task["status"] == "completed":
            storage.update_task_status(task["task_id"], "deleted")
    return {"status": "cleared"}


@app.get("/api/dashboard")
async def get_dashboard():
    return {
        "summary": dashboard.get_task_summary(),
        "tasks": dashboard.get_task_details(),
        "system": resource_monitor.get_system_summary(),
        "success_rate": dashboard.get_success_rate(),
    }


@app.get("/api/stats")
async def get_stats():
    return storage.get_execution_stats()


@app.get("/api/dag")
async def get_dag_info():
    return dag.get_dag_info()


@app.post("/api/dag/validate")
async def validate_dag():
    is_valid, errors = dag.validate()
    return {"valid": is_valid, "errors": errors}


@app.get("/api/export")
async def export_all():
    return storage.export_data()


def run_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
