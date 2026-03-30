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
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }
        .btn-primary:hover { transform: scale(1.02); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4); }
        input { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: white; }
        input:focus { border-color: #667eea; box-shadow: 0 0 20px rgba(102, 126, 234, 0.3); outline: none; }
    </style>
</head>
<body class="text-white">
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
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
                        <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                    <h2 class="text-xl font-bold mb-4">Task Queue</h2>
                    <div id="task-list" class="space-y-3 max-h-80 overflow-y-auto">
                        <p class="text-gray-500 text-center py-8">No tasks yet!</p>
                    </div>
                </div>
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-xl font-bold mb-4">Add New Task</h2>
                    <form id="task-form" class="space-y-4">
                        <div class="grid grid-cols-2 gap-4">
                            <input type="text" name="task_id" placeholder="Task ID" required class="w-full px-4 py-3 rounded-xl">
                            <input type="text" name="name" placeholder="Task Name" required class="w-full px-4 py-3 rounded-xl">
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <input type="number" name="complexity" min="1" max="10" value="5" placeholder="Complexity" class="w-full px-4 py-3 rounded-xl">
                            <input type="datetime-local" name="deadline" class="w-full px-4 py-3 rounded-xl">
                        </div>
                        <button type="submit" class="w-full btn-primary py-4 rounded-xl font-bold text-lg">Add Task</button>
                    </form>
                </div>
            </div>
            <div class="space-y-6">
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-xl font-bold mb-4">System Resources</h2>
                    <div class="space-y-4">
                        <div>
                            <div class="flex justify-between mb-2">
                                <span class="text-gray-400">CPU</span>
                                <span id="cpu-value" class="font-bold">0%</span>
                            </div>
                            <div class="w-full h-3 bg-white/10 rounded-full">
                                <div id="cpu-bar" class="h-full bg-blue-500 rounded-full transition-all" style="width: 0%"></div>
                            </div>
                        </div>
                        <div>
                            <div class="flex justify-between mb-2">
                                <span class="text-gray-400">Memory</span>
                                <span id="memory-value" class="font-bold">0%</span>
                            </div>
                            <div class="w-full h-3 bg-white/10 rounded-full">
                                <div id="memory-bar" class="h-full bg-purple-500 rounded-full transition-all" style="width: 0%"></div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="glass rounded-2xl p-6">
                    <h2 class="text-xl font-bold mb-4">AI Priority Queue</h2>
                    <div id="priority-list" class="space-y-2">
                        <p class="text-gray-500 text-center py-4">No tasks</p>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        async function loadTasks() {
            try {
                const res = await fetch('/api/tasks');
                const data = await res.json();
                const tasks = data.tasks || [];
                
                document.getElementById('stat-total').textContent = tasks.length;
                document.getElementById('stat-completed').textContent = tasks.filter(t => t.status === 'completed').length;
                document.getElementById('stat-running').textContent = tasks.filter(t => t.status === 'running').length;
                
                if (tasks.length === 0) {
                    document.getElementById('task-list').innerHTML = '<p class="text-gray-500 text-center py-8">No tasks yet!</p>';
                } else {
                    document.getElementById('task-list').innerHTML = tasks.map(task => \`
                        <div class="bg-white/5 rounded-xl p-4 flex items-center justify-between">
                            <div>
                                <h4 class="font-semibold">\${task.name || task.task_id}</h4>
                                <p class="text-sm text-gray-400">\${task.task_id}</p>
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="text-purple-400 font-bold">\${(task.priority || 0).toFixed(1)}</span>
                                <span class="px-3 py-1 rounded-full text-xs \${getStatusClass(task.status)}">\${task.status}</span>
                            </div>
                        </div>
                    \`).join('');
                }
                
                const sorted = [...tasks].sort((a, b) => (b.priority || 0) - (a.priority || 0)).slice(0, 5);
                if (sorted.length > 0) {
                    document.getElementById('priority-list').innerHTML = sorted.map((t, i) => \`
                        <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                            <span class="w-6 h-6 rounded-full \${i === 0 ? 'bg-yellow-500' : 'bg-white/10'} flex items-center justify-center text-xs font-bold">\${i+1}</span>
                            <span class="text-sm">\${t.name || t.task_id}</span>
                            <span class="font-bold text-purple-400">\${(t.priority || 0).toFixed(1)}</span>
                        </div>
                    \`).join('');
                }
            } catch (e) { console.error(e); }
        }
        
        function getStatusClass(s) {
            return {pending:'bg-gray-500/20 text-gray-400', running:'bg-yellow-500/20 text-yellow-400', completed:'bg-green-500/20 text-green-400', failed:'bg-red-500/20 text-red-400'}[s] || 'bg-gray-500/20 text-gray-400';
        }
        
        document.getElementById('task-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const fd = new FormData(e.target);
            await fetch('/api/tasks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    task_id: fd.get('task_id'),
                    name: fd.get('name'),
                    complexity: parseFloat(fd.get('complexity')) || 5,
                    deadline: fd.get('deadline') || null
                })
            });
            e.target.reset();
            loadTasks();
        });
        
        loadTasks();
        setInterval(loadTasks, 3000);
    </script>
</body>
</html>
`;

module.exports = (req, res) => {
    const url = require('url').parse(req.url, true);
    
    if (url.pathname === "/" || url.pathname === "/index") {
        res.setHeader('Content-Type', 'text/html');
        res.send(html);
        return;
    }
    
    if (url.pathname === "/api/tasks" && req.method === "GET") {
        res.json({ tasks: TASKS });
        return;
    }
    
    if (url.pathname === "/api/tasks" && req.method === "POST") {
        const body = req.body || {};
        const task = {
            task_id: body.task_id,
            name: body.name,
            complexity: body.complexity || 5,
            estimated_duration: body.estimated_duration || 60,
            deadline: body.deadline,
            status: "pending",
            priority: Math.random() * 50 + 50,
            created_at: new Date().toISOString()
        };
        TASKS.push(task);
        res.json({ status: "success", task_id: task.task_id });
        return;
    }
    
    if (url.pathname === "/api/dashboard") {
        res.json({
            summary: {
                total_tasks: TASKS.length,
                running: TASKS.filter(t => t.status === "running").length,
                completed: TASKS.filter(t => t.status === "completed").length,
                failed: TASKS.filter(t => t.status === "failed").length,
            },
            tasks: TASKS,
            system: RESOURCE_DATA,
            success_rate: 100
        });
        return;
    }
    
    res.status(404).send("Not Found");
};
