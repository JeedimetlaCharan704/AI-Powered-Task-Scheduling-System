from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ai_scheduler.priority_scorer import AIPriorityScorer, PriorityConfig
from ai_scheduler.resource_monitor import ResourceMonitor, ResourceAwareScheduler
from ai_scheduler.dashboard import Dashboard
from ai_scheduler.storage import TaskStorage
from ai_scheduler.dag import TaskDAG, DAGExecutor


app = FastAPI(
    title="TaskMind - AI-Powered Task Scheduler",
    version="1.0.0",
    description="Intelligent task scheduling powered by AI"
)

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


DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TaskMind - AI Task Scheduler</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { font-family: 'Inter', sans-serif; }
        
        body {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1f 100%);
            min-height: 100vh;
        }
        
        .glass {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .gradient-text {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .card-hover:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        
        .pulse-dot {
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }
        
        .slide-in {
            animation: slideIn 0.5s ease-out;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .glow {
            box-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
        }
        
        .progress-ring {
            transform: rotate(-90deg);
        }
        
        .task-card {
            background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
        }
        
        .status-pending { color: #94a3b8; }
        .status-running { color: #fbbf24; }
        .status-completed { color: #34d399; }
        .status-failed { color: #f87171; }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        input, select, textarea {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            transition: all 0.3s ease;
        }
        
        input:focus, select:focus, textarea:focus {
            border-color: #667eea;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
            outline: none;
        }
        
        .scrollbar-thin::-webkit-scrollbar {
            width: 6px;
        }
        
        .scrollbar-thin::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }
        
        .scrollbar-thin::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.5);
            border-radius: 3px;
        }
        
        .ai-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
    </style>
</head>
<body class="text-white scrollbar-thin overflow-x-hidden">
    
    <!-- Navigation -->
    <nav class="glass fixed w-full top-0 z-50">
        <div class="max-w-7xl mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                        </svg>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold gradient-text">TaskMind</h1>
                        <p class="text-xs text-gray-400">AI-Powered Task Scheduler</p>
                    </div>
                </div>
                <div class="flex items-center gap-4">
                    <div id="connection-status" class="flex items-center gap-2 px-4 py-2 rounded-full glass">
                        <span class="w-2 h-2 rounded-full bg-green-500 pulse-dot"></span>
                        <span class="text-sm">Connected</span>
                    </div>
                    <button onclick="exportData()" class="px-4 py-2 glass rounded-lg hover:bg-white/10 transition">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="pt-24 pb-12 px-6 max-w-7xl mx-auto">
        
        <!-- Hero Stats -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 slide-in">
            <div class="glass rounded-2xl p-6 card-hover transition-all duration-300">
                <div class="flex items-center justify-between mb-4">
                    <div class="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                        <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                        </svg>
                    </div>
                    <span class="text-3xl font-bold text-white" id="stat-total">0</span>
                </div>
                <p class="text-gray-400 text-sm">Total Tasks</p>
            </div>
            
            <div class="glass rounded-2xl p-6 card-hover transition-all duration-300">
                <div class="flex items-center justify-between mb-4">
                    <div class="w-12 h-12 rounded-xl bg-yellow-500/20 flex items-center justify-center">
                        <svg class="w-6 h-6 text-yellow-400 animate-spin" style="animation-duration: 3s" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                    </div>
                    <span class="text-3xl font-bold text-yellow-400" id="stat-running">0</span>
                </div>
                <p class="text-gray-400 text-sm">Running Now</p>
            </div>
            
            <div class="glass rounded-2xl p-6 card-hover transition-all duration-300">
                <div class="flex items-center justify-between mb-4">
                    <div class="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
                        <svg class="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <span class="text-3xl font-bold text-green-400" id="stat-completed">0</span>
                </div>
                <p class="text-gray-400 text-sm">Completed</p>
            </div>
            
            <div class="glass rounded-2xl p-6 card-hover transition-all duration-300">
                <div class="flex items-center justify-between mb-4">
                    <div class="w-12 h-12 rounded-xl ai-badge flex items-center justify-center">
                        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <span class="text-3xl font-bold text-pink-400" id="stat-success">0%</span>
                </div>
                <p class="text-gray-400 text-sm">Success Rate</p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            <!-- Left Column - Task List -->
            <div class="lg:col-span-2 space-y-6">
                
                <!-- Task Queue -->
                <div class="glass rounded-2xl p-6">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-xl font-bold">Task Queue</h2>
                        <div class="flex gap-2">
                            <button onclick="executeNext()" class="btn-primary px-4 py-2 rounded-lg text-sm font-medium">
                                Execute Next
                            </button>
                            <button onclick="clearCompleted()" class="px-4 py-2 glass rounded-lg text-sm hover:bg-white/10 transition">
                                Clear Done
                            </button>
                        </div>
                    </div>
                    <div id="task-list" class="space-y-3 max-h-96 overflow-y-auto scrollbar-thin">
                        <div class="text-center py-12 text-gray-500">
                            <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                            </svg>
                            <p>No tasks yet. Add some tasks below!</p>
                        </div>
                    </div>
                </div>

                <!-- Add Task Form -->
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-xl font-bold mb-6">Add New Task</h2>
                    <form id="task-form" class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm text-gray-400 mb-2">Task ID</label>
                                <input type="text" name="task_id" placeholder="unique_task_id" required 
                                    class="w-full px-4 py-3 rounded-xl">
                            </div>
                            <div>
                                <label class="block text-sm text-gray-400 mb-2">Task Name</label>
                                <input type="text" name="name" placeholder="Data Processing" required 
                                    class="w-full px-4 py-3 rounded-xl">
                            </div>
                        </div>
                        <div class="grid grid-cols-3 gap-4">
                            <div>
                                <label class="block text-sm text-gray-400 mb-2">Complexity (1-10)</label>
                                <input type="number" name="complexity" min="1" max="10" value="5" 
                                    class="w-full px-4 py-3 rounded-xl">
                            </div>
                            <div>
                                <label class="block text-sm text-gray-400 mb-2">Duration (sec)</label>
                                <input type="number" name="estimated_duration" value="60" 
                                    class="w-full px-4 py-3 rounded-xl">
                            </div>
                            <div>
                                <label class="block text-sm text-gray-400 mb-2">Deadline</label>
                                <input type="datetime-local" name="deadline" 
                                    class="w-full px-4 py-3 rounded-xl">
                            </div>
                        </div>
                        <button type="submit" class="w-full btn-primary py-4 rounded-xl font-bold text-lg">
                            Add Task
                        </button>
                    </form>
                </div>
            </div>

            <!-- Right Column - Resources & Priority -->
            <div class="space-y-6">
                
                <!-- Resource Monitor -->
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-xl font-bold mb-6">System Resources</h2>
                    
                    <div class="space-y-6">
                        <div>
                            <div class="flex justify-between items-center mb-3">
                                <span class="text-gray-400">CPU Usage</span>
                                <span class="font-bold" id="cpu-value">0%</span>
                            </div>
                            <div class="w-full h-3 bg-white/10 rounded-full overflow-hidden">
                                <div id="cpu-bar" class="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all duration-500" style="width: 0%"></div>
                            </div>
                        </div>
                        
                        <div>
                            <div class="flex justify-between items-center mb-3">
                                <span class="text-gray-400">Memory Usage</span>
                                <span class="font-bold" id="memory-value">0%</span>
                            </div>
                            <div class="w-full h-3 bg-white/10 rounded-full overflow-hidden">
                                <div id="memory-bar" class="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500" style="width: 0%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-6 pt-6 border-t border-white/10">
                        <canvas id="resourceChart" height="150"></canvas>
                    </div>
                </div>

                <!-- Priority Queue -->
                <div class="glass rounded-2xl p-6">
                    <div class="flex items-center gap-2 mb-6">
                        <svg class="w-5 h-5 text-pink-400" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                        </svg>
                        <h2 class="text-xl font-bold">AI Priority Queue</h2>
                    </div>
                    <div id="priority-list" class="space-y-3">
                        <p class="text-gray-500 text-center py-4">No tasks ranked yet</p>
                    </div>
                </div>

                <!-- Quick Stats -->
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-xl font-bold mb-4">Statistics</h2>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Failed Tasks</span>
                            <span class="font-bold text-red-400" id="stat-failed">0</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Paused</span>
                            <span class="font-bold text-orange-400" id="stat-paused">0</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Avg CPU</span>
                            <span class="font-bold" id="stat-avg-cpu">0%</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Avg Memory</span>
                            <span class="font-bold" id="stat-avg-mem">0%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Toast Notification -->
    <div id="toast" class="fixed bottom-6 right-6 glass rounded-xl p-4 transform translate-y-20 opacity-0 transition-all duration-300 z-50">
        <div class="flex items-center gap-3">
            <div id="toast-icon" class="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            <span id="toast-message">Task added successfully!</span>
        </div>
    </div>

    <script>
        let resourceChart;
        
        // Initialize Chart
        function initChart() {
            const ctx = document.getElementById('resourceChart').getContext('2d');
            resourceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU %',
                            data: [],
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Memory %',
                            data: [],
                            borderColor: '#a855f7',
                            backgroundColor: 'rgba(168, 85, 247, 0.1)',
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            labels: { color: '#94a3b8', font: { size: 10 } }
                        }
                    },
                    scales: {
                        x: { display: false },
                        y: { 
                            display: true,
                            max: 100,
                            ticks: { color: '#64748b', font: { size: 10 } },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        }
                    }
                }
            });
        }
        
        // Show Toast
        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            const toastIcon = document.getElementById('toast-icon');
            const toastMessage = document.getElementById('toast-message');
            
            toastMessage.textContent = message;
            toastIcon.className = `w-8 h-8 rounded-full flex items-center justify-center ${type === 'success' ? 'bg-green-500' : 'bg-red-500'}`;
            
            toast.classList.remove('translate-y-20', 'opacity-0');
            toast.classList.add('translate-y-0', 'opacity-100');
            
            setTimeout(() => {
                toast.classList.add('translate-y-20', 'opacity-0');
                toast.classList.remove('translate-y-0', 'opacity-100');
            }, 3000);
        }
        
        // Get Status Class
        function getStatusClass(status) {
            const classes = {
                'pending': 'bg-gray-500/20 text-gray-400',
                'running': 'bg-yellow-500/20 text-yellow-400 pulse-dot',
                'completed': 'bg-green-500/20 text-green-400',
                'failed': 'bg-red-500/20 text-red-400',
                'paused': 'bg-orange-500/20 text-orange-400'
            };
            return classes[status] || classes.pending;
        }
        
        // Update Dashboard
        async function updateDashboard() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                
                const summary = data.summary || {};
                document.getElementById('stat-total').textContent = summary.total_tasks || 0;
                document.getElementById('stat-running').textContent = summary.running || 0;
                document.getElementById('stat-completed').textContent = summary.completed || 0;
                document.getElementById('stat-success').textContent = (data.success_rate || 0) + '%';
                document.getElementById('stat-failed').textContent = summary.failed || 0;
                document.getElementById('stat-paused').textContent = summary.paused || 0;
                
                const system = data.system || {};
                document.getElementById('cpu-value').textContent = (system.current_cpu || 0).toFixed(1) + '%';
                document.getElementById('memory-value').textContent = (system.current_memory || 0).toFixed(1) + '%';
                document.getElementById('cpu-bar').style.width = (system.current_cpu || 0) + '%';
                document.getElementById('memory-bar').style.width = (system.current_memory || 0) + '%';
                document.getElementById('stat-avg-cpu').textContent = (system.avg_cpu || 0).toFixed(1) + '%';
                document.getElementById('stat-avg-mem').textContent = (system.avg_memory || 0).toFixed(1) + '%';
                
                // Update Chart
                if (resourceChart) {
                    const now = new Date().toLocaleTimeString();
                    resourceChart.data.labels.push(now);
                    resourceChart.data.datasets[0].data.push(system.current_cpu || 0);
                    resourceChart.data.datasets[1].data.push(system.current_memory || 0);
                    
                    if (resourceChart.data.labels.length > 20) {
                        resourceChart.data.labels.shift();
                        resourceChart.data.datasets[0].data.shift();
                        resourceChart.data.datasets[1].data.shift();
                    }
                    resourceChart.update();
                }
                
                // Update Task List
                const tasks = data.tasks || [];
                const taskList = document.getElementById('task-list');
                
                if (tasks.length === 0) {
                    taskList.innerHTML = `
                        <div class="text-center py-12 text-gray-500">
                            <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                            </svg>
                            <p>No tasks yet. Add some tasks below!</p>
                        </div>
                    `;
                } else {
                    taskList.innerHTML = tasks.slice(0, 10).map(task => `
                        <div class="task-card rounded-xl p-4 flex items-center justify-between slide-in">
                            <div class="flex items-center gap-4">
                                <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
                                    <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                                    </svg>
                                </div>
                                <div>
                                    <h4 class="font-semibold">${task.name || task.task_id}</h4>
                                    <p class="text-sm text-gray-400">ID: ${task.task_id}</p>
                                </div>
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="text-sm font-bold text-purple-400">${(task.priority || 0).toFixed(1)}</span>
                                <span class="px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(task.status)}">
                                    ${task.status || 'pending'}
                                </span>
                                <button onclick="runSingleTask('${task.task_id}')" class="px-3 py-1 bg-green-500 hover:bg-green-600 rounded-lg text-xs font-bold text-white transition">
                                    Run
                                </button>
                            </div>
                        </div>
                    `).join('');
                }
                
                // Update Priority List
                const priorityList = document.getElementById('priority-list');
                const topTasks = tasks.slice(0, 5);
                
                if (topTasks.length === 0) {
                    priorityList.innerHTML = '<p class="text-gray-500 text-center py-4">No tasks ranked yet</p>';
                } else {
                    priorityList.innerHTML = topTasks.map((task, i) => `
                        <div class="flex items-center justify-between p-3 rounded-lg bg-white/5">
                            <div class="flex items-center gap-3">
                                <span class="w-6 h-6 rounded-full ${i === 0 ? 'bg-gradient-to-br from-yellow-400 to-orange-500' : 'bg-white/10'} flex items-center justify-center text-xs font-bold">
                                    ${i + 1}
                                </span>
                                <span class="text-sm">${task.name || task.task_id}</span>
                            </div>
                            <span class="font-bold text-purple-400">${(task.priority || 0).toFixed(1)}</span>
                        </div>
                    `).join('');
                }
                
            } catch (error) {
                console.error('Error updating dashboard:', error);
            }
        }
        
        // Execute Next Task
        async function executeNext() {
            try {
                const response = await fetch('/api/tasks/execute-next', { method: 'POST' });
                const result = await response.json();
                showToast(result.message || 'Task executed!', 'success');
                updateDashboard();
            } catch (error) {
                showToast('Error executing task', 'error');
            }
        }
        
        // Run Single Task
        async function runSingleTask(taskId) {
            try {
                const response = await fetch('/api/tasks/' + taskId + '/execute', { method: 'POST' });
                const result = await response.json();
                showToast('Task ' + taskId + ' executed!', 'success');
                updateDashboard();
            } catch (error) {
                showToast('Error executing task', 'error');
            }
        }
        
        // Clear Completed
        async function clearCompleted() {
            try {
                await fetch('/api/tasks/completed', { method: 'DELETE' });
                showToast('Completed tasks cleared!', 'success');
                updateDashboard();
            } catch (error) {
                showToast('Error clearing tasks', 'error');
            }
        }
        
        // Export Data
        async function exportData() {
            try {
                const response = await fetch('/api/export');
                const data = await response.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'taskmind_export_' + new Date().toISOString().split('T')[0] + '.json';
                a.click();
                showToast('Data exported successfully!', 'success');
            } catch (error) {
                showToast('Error exporting data', 'error');
            }
        }
        
        // Form Submit
        document.getElementById('task-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            const task = {
                task_id: formData.get('task_id'),
                name: formData.get('name'),
                complexity: parseFloat(formData.get('complexity')),
                estimated_duration: parseFloat(formData.get('estimated_duration')),
                deadline: formData.get('deadline') || null
            };
            
            try {
                const response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(task)
                });
                
                if (response.ok) {
                    showToast('Task added successfully!', 'success');
                    e.target.reset();
                    updateDashboard();
                } else {
                    showToast('Error adding task', 'error');
                }
            } catch (error) {
                showToast('Error adding task', 'error');
            }
        });
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initChart();
            updateDashboard();
            setInterval(updateDashboard, 2000);
        });
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def root():
    return DASHBOARD_HTML


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


@app.post("/api/tasks/{task_id}/execute")
async def execute_single_task(task_id: str):
    task = storage.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
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
