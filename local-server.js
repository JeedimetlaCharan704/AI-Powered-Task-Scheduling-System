const http = require('http');
const url = require('url');
const querystring = require('querystring');

const TASKS = [];
const RESOURCE_DATA = {
  current_cpu: 0,
  current_memory: 0,
  avg_cpu: 0,
  avg_memory: 0,
};

const html = `
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
        .pulse-dot { animation: pulse 2s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .slide-in { animation: slideIn 0.5s ease-out; }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }
        .btn-primary:hover { transform: scale(1.02); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4); }
        input { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: white; }
        input:focus { border-color: #667eea; box-shadow: 0 0 20px rgba(102, 126, 234, 0.3); outline: none; }
        .task-card { background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02)); }
        .scrollbar-thin::-webkit-scrollbar { width: 6px; }
        .scrollbar-thin::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); }
        .scrollbar-thin::-webkit-scrollbar-thumb { background: rgba(102, 126, 234, 0.5); border-radius: 3px; }
    </style>
</head>
<body class="text-white scrollbar-thin overflow-x-hidden">
    
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
                <div class="flex items-center gap-2 px-4 py-2 rounded-full glass">
                    <span class="w-2 h-2 rounded-full bg-green-500 pulse-dot"></span>
                    <span class="text-sm">Live</span>
                </div>
            </div>
        </div>
    </nav>

    <main class="pt-24 pb-12 px-6 max-w-7xl mx-auto">
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 slide-in">
            <div class="glass rounded-2xl p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <div class="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                        <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                        </svg>
                    </div>
                    <span class="text-3xl font-bold" id="stat-total">0</span>
                </div>
                <p class="text-gray-400 text-sm">Total Tasks</p>
            </div>
            
            <div class="glass rounded-2xl p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <div class="w-12 h-12 rounded-xl bg-yellow-500/20 flex items-center justify-center">
                        <svg class="w-6 h-6 text-yellow-400 animate-spin" style="animation-duration: 3s" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                    </div>
                    <span class="text-3xl font-bold text-yellow-400" id="stat-running">0</span>
                </div>
                <p class="text-gray-400 text-sm">Running</p>
            </div>
            
            <div class="glass rounded-2xl p-6 card-hover">
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
            
            <div class="glass rounded-2xl p-6 card-hover">
                <div class="flex items-center justify-between mb-4">
                    <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500 to-red-500 flex items-center justify-center">
                        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                        </svg>
                    </div>
                    <span class="text-3xl font-bold text-pink-400" id="stat-success">100%</span>
                </div>
                <p class="text-gray-400 text-sm">Success Rate</p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 space-y-6">
                
                <div class="glass rounded-2xl p-6">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-xl font-bold">Task Queue</h2>
                        <button onclick="executeNext()" class="btn-primary px-4 py-2 rounded-lg text-sm font-medium">
                            Execute Next
                        </button>
                    </div>
                    <div id="task-list" class="space-y-3 max-h-96 overflow-y-auto scrollbar-thin">
                        <p class="text-gray-500 text-center py-12">No tasks yet. Add some tasks below!</p>
                    </div>
                </div>
                
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-xl font-bold mb-6">Add New Task</h2>
                    <form id="task-form" class="space-y-4">
                        <div>
                            <label class="block text-sm text-gray-400 mb-2">Task Name</label>
                            <input type="text" name="name" placeholder="Data Processing" required class="w-full px-4 py-3 rounded-xl">
                        </div>
                        <div class="grid grid-cols-3 gap-4">
                            <div>
                                <label class="block text-sm text-gray-400 mb-2">Complexity (1-10)</label>
                                <input type="number" name="complexity" min="1" max="10" value="5" class="w-full px-4 py-3 rounded-xl">
                            </div>
                            <div>
                                <label class="block text-sm text-gray-400 mb-2">Duration (sec)</label>
                                <input type="number" name="estimated_duration" value="60" class="w-full px-4 py-3 rounded-xl">
                            </div>
                            <div>
                                <label class="block text-sm text-gray-400 mb-2">Deadline</label>
                                <input type="datetime-local" name="deadline" class="w-full px-4 py-3 rounded-xl">
                            </div>
                        </div>
                        <button type="submit" class="w-full btn-primary py-4 rounded-xl font-bold text-lg">Add Task</button>
                    </form>
                </div>
            </div>
            
            <div class="space-y-6">
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-xl font-bold mb-6">System Resources</h2>
                    <div class="space-y-6">
                        <div>
                            <div class="flex justify-between items-center mb-3">
                                <span class="text-gray-400">CPU Usage</span>
                                <span class="font-bold" id="cpu-value">0%</span>
                            </div>
                            <div class="w-full h-3 bg-white/10 rounded-full">
                                <div id="cpu-bar" class="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all" style="width: 0%"></div>
                            </div>
                        </div>
                        <div>
                            <div class="flex justify-between items-center mb-3">
                                <span class="text-gray-400">Memory Usage</span>
                                <span class="font-bold" id="memory-value">0%</span>
                            </div>
                            <div class="w-full h-3 bg-white/10 rounded-full">
                                <div id="memory-bar" class="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all" style="width: 0%"></div>
                            </div>
                        </div>
                    </div>
                    <div class="mt-6 pt-6 border-t border-white/10">
                        <canvas id="resourceChart" height="150"></canvas>
                    </div>
                </div>
                
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
            </div>
        </div>
    </main>

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
        
        function initChart() {
            const ctx = document.getElementById('resourceChart').getContext('2d');
            resourceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        { label: 'CPU %', data: [], borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', fill: true, tension: 0.4 },
                        { label: 'Memory %', data: [], borderColor: '#a855f7', backgroundColor: 'rgba(168, 85, 247, 0.1)', fill: true, tension: 0.4 }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: true, labels: { color: '#94a3b8', font: { size: 10 } } } },
                    scales: { x: { display: false }, y: { display: true, max: 100, ticks: { color: '#64748b', font: { size: 10 } } } }
                }
            });
        }
        
        function showToast(message, type) {
            type = type || 'success';
            const toast = document.getElementById('toast');
            document.getElementById('toast-message').textContent = message;
            document.getElementById('toast-icon').className = 'w-8 h-8 rounded-full flex items-center justify-center ' + (type === 'success' ? 'bg-green-500' : 'bg-red-500');
            toast.classList.remove('translate-y-20', 'opacity-0');
            toast.classList.add('translate-y-0', 'opacity-100');
            setTimeout(function() { toast.classList.add('translate-y-20', 'opacity-0'); }, 3000);
        }
        
        function getStatusClass(status) {
            return { pending: 'bg-gray-500/20 text-gray-400', running: 'bg-yellow-500/20 text-yellow-400 pulse-dot', completed: 'bg-green-500/20 text-green-400', failed: 'bg-red-500/20 text-red-400' }[status] || 'bg-gray-500/20 text-gray-400';
        }
        
        async function loadTasks() {
            try {
                const res = await fetch('/api/dashboard');
                const data = await res.json();
                
                document.getElementById('stat-total').textContent = data.summary.total_tasks || 0;
                document.getElementById('stat-running').textContent = data.summary.running || 0;
                document.getElementById('stat-completed').textContent = data.summary.completed || 0;
                document.getElementById('stat-success').textContent = (data.success_rate || 100) + '%';
                
                const system = data.system || {};
                document.getElementById('cpu-value').textContent = (system.current_cpu || 0).toFixed(1) + '%';
                document.getElementById('memory-value').textContent = (system.current_memory || 0).toFixed(1) + '%';
                document.getElementById('cpu-bar').style.width = (system.current_cpu || 0) + '%';
                document.getElementById('memory-bar').style.width = (system.current_memory || 0) + '%';
                
                if (resourceChart) {
                    resourceChart.data.labels.push(new Date().toLocaleTimeString());
                    resourceChart.data.datasets[0].data.push(system.current_cpu || 0);
                    resourceChart.data.datasets[1].data.push(system.current_memory || 0);
                    if (resourceChart.data.labels.length > 20) {
                        resourceChart.data.labels.shift();
                        resourceChart.data.datasets[0].data.shift();
                        resourceChart.data.datasets[1].data.shift();
                    }
                    resourceChart.update();
                }
                
                const tasks = data.tasks || [];
                if (tasks.length === 0) {
                    document.getElementById('task-list').innerHTML = '<p class="text-gray-500 text-center py-12">No tasks yet. Add some tasks below!</p>';
                } else {
                    document.getElementById('task-list').innerHTML = tasks.map(function(task) {
                        return '<div class="task-card rounded-xl p-4 flex items-center justify-between slide-in">' +
                            '<div class="flex items-center gap-4">' +
                                '<div class="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">' +
                                    '<svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
                                        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>' +
                                    '</svg>' +
                                '</div>' +
                                '<div>' +
                                    '<h4 class="font-semibold">' + (task.name || task.task_id) + '</h4>' +
                                    '<p class="text-sm text-gray-400">ID: ' + task.task_id + '</p>' +
                                '</div>' +
                            '</div>' +
                            '<div class="flex items-center gap-3">' +
                                '<span class="text-sm font-bold text-purple-400">' + (task.priority || 0).toFixed(1) + '</span>' +
                                '<span class="px-3 py-1 rounded-full text-xs font-medium ' + getStatusClass(task.status) + '">' + (task.status || 'pending') + '</span>' +
                                '<button onclick="runTask(\\'' + task.task_id + '\\')" class="px-3 py-1 bg-green-500 hover:bg-green-600 rounded-lg text-xs font-bold text-white transition">Run</button>' +
                            '</div>' +
                        '</div>';
                    }).join('');
                }
                
                const sorted = tasks.slice().sort(function(a, b) { return (b.priority || 0) - (a.priority || 0); }).slice(0, 5);
                if (sorted.length > 0) {
                    document.getElementById('priority-list').innerHTML = sorted.map(function(t, i) {
                        return '<div class="flex items-center justify-between p-3 rounded-lg bg-white/5">' +
                            '<div class="flex items-center gap-3">' +
                                '<span class="w-6 h-6 rounded-full ' + (i === 0 ? 'bg-gradient-to-br from-yellow-400 to-orange-500' : 'bg-white/10') + ' flex items-center justify-center text-xs font-bold">' + (i+1) + '</span>' +
                                '<span class="text-sm">' + (t.name || t.task_id) + '</span>' +
                            '</div>' +
                            '<span class="font-bold text-purple-400">' + (t.priority || 0).toFixed(1) + '</span>' +
                        '</div>';
                    }).join('');
                } else {
                    document.getElementById('priority-list').innerHTML = '<p class="text-gray-500 text-center py-4">No tasks ranked yet</p>';
                }
            } catch (e) { console.error(e); }
        }
        
        async function executeNext() {
            try {
                await fetch('/api/tasks/execute-next', { method: 'POST' });
                showToast('Task executed!', 'success');
                loadTasks();
            } catch (e) { showToast('Error', 'error'); }
        }
        
        async function runTask(taskId) {
            try {
                await fetch('/api/tasks/' + taskId + '/execute', { method: 'POST' });
                showToast('Task ' + taskId + ' executed!', 'success');
                loadTasks();
            } catch (e) { showToast('Error', 'error'); }
        }
        
        document.getElementById('task-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            const fd = new FormData(e.target);
            const res = await fetch('/api/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_id: 'task_' + Date.now(),
                    name: fd.get('name'),
                    complexity: parseFloat(fd.get('complexity')) || 5,
                    estimated_duration: parseFloat(fd.get('estimated_duration')) || 60,
                    deadline: fd.get('deadline') || null
                })
            });
            if (res.ok) {
                showToast('Task added!', 'success');
                e.target.reset();
                loadTasks();
            } else {
                showToast('Error adding task', 'error');
            }
        });
        
        document.addEventListener('DOMContentLoaded', function() {
            initChart();
            loadTasks();
            setInterval(loadTasks, 2000);
        });
    </script>
</body>
</html>
`;

function handleRequest(req, res) {
    const pathname = url.parse(req.url).pathname;
    
    if (pathname === "/" || pathname === "/index") {
        res.writeHead(200, {'Content-Type': 'text/html'});
        res.end(html);
        return;
    }
    
    if (pathname === "/api/tasks" && req.method === "GET") {
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify({ tasks: TASKS }));
        return;
    }
    
    if (pathname === "/api/tasks" && req.method === "POST") {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            const taskData = JSON.parse(body || '{}');
            const deadline = taskData.deadline ? new Date(taskData.deadline) : null;
            const now = new Date();
            const hoursUntilDeadline = deadline ? (deadline - now) / (1000 * 60 * 60) : 24;
            const deadlineScore = Math.min(100, Math.max(0, hoursUntilDeadline * 10));
            const complexity = taskData.complexity || 5;
            const priority = (deadlineScore * 0.5) + (complexity * 5) + (Math.random() * 10);
            
            const task = {
                task_id: taskData.task_id || 'task_' + Date.now(),
                name: taskData.name,
                complexity: complexity,
                estimated_duration: taskData.estimated_duration || 60,
                deadline: taskData.deadline,
                status: "pending",
                priority: priority,
                created_at: new Date().toISOString()
            };
            TASKS.push(task);
            res.writeHead(200, {'Content-Type': 'application/json'});
            res.end(JSON.stringify({ status: "success", task_id: task.task_id }));
        });
        return;
    }
    
    if (pathname === "/api/tasks/execute-next" && req.method === "POST") {
        const pending = TASKS.filter(t => t.status === "pending");
        if (pending.length === 0) {
            res.writeHead(200, {'Content-Type': 'application/json'});
            res.end(JSON.stringify({ status: "no_tasks", message: "No pending tasks" }));
            return;
        }
        pending.sort((a, b) => (b.priority || 0) - (a.priority || 0));
        const task = pending[0];
        task.status = "running";
        setTimeout(() => {
            task.status = "completed";
            RESOURCE_DATA.current_cpu = Math.random() * 30 + 10;
            RESOURCE_DATA.current_memory = Math.random() * 20 + 70;
        }, 2000);
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify({ status: "executed", task_id: task.task_id }));
        return;
    }
    
    if (pathname.match(/\/api\/tasks\/([^\/]+)\/execute/) && req.method === "POST") {
        const match = pathname.match(/\/api\/tasks\/([^\/]+)\/execute/);
        const taskId = match[1];
        const task = TASKS.find(t => t.task_id === taskId);
        if (!task) {
            res.writeHead(404, {'Content-Type': 'application/json'});
            res.end(JSON.stringify({ error: "Task not found" }));
            return;
        }
        task.status = "running";
        setTimeout(() => {
            task.status = "completed";
            RESOURCE_DATA.current_cpu = Math.random() * 30 + 10;
            RESOURCE_DATA.current_memory = Math.random() * 20 + 70;
        }, 2000);
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify({ status: "executed", task_id: task.task_id }));
        return;
    }
    
    if (pathname === "/api/dashboard") {
        const completed = TASKS.filter(t => t.status === "completed").length;
        const failed = TASKS.filter(t => t.status === "failed").length;
        const total = TASKS.length;
        res.writeHead(200, {'Content-Type': 'application/json'});
        res.end(JSON.stringify({
            summary: {
                total_tasks: TASKS.length,
                running: TASKS.filter(t => t.status === "running").length,
                completed: completed,
                failed: failed,
                paused: 0,
            },
            tasks: TASKS,
            system: RESOURCE_DATA,
            success_rate: total > 0 ? Math.round((completed / total) * 100) : 100
        }));
        return;
    }
    
    res.writeHead(404, {'Content-Type': 'text/plain'});
    res.end("Not Found");
}

const PORT = process.env.PORT || 3000;
http.createServer(handleRequest).listen(PORT, () => {
    console.log('Server running at http://localhost:' + PORT + '/');
});
