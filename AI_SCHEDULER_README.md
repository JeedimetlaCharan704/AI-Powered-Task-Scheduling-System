# TaskMind - AI-Powered Task Scheduling System

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

**TaskMind** is an intelligent task scheduling system that uses AI to prioritize and execute tasks based on deadline urgency, complexity, and historical performance. It monitors system resources, supports task dependencies (DAGs), and provides both a web dashboard and CLI interface.

---

## Features

### 1. AI Priority Scoring
Tasks are automatically ranked using a smart algorithm that considers:
- **Deadline proximity** - Urgent tasks get higher priority
- **Task complexity** - More complex tasks are weighted appropriately
- **Historical performance** - Learns from past executions to improve future scheduling

### 2. Resource Monitoring
- Real-time CPU and memory usage tracking
- Per-task resource monitoring
- Automatic pausing of low-priority tasks when resources are scarce
- System health dashboard

### 3. Task Dependencies (DAG)
Support for complex workflows with:
- Directed Acyclic Graph (DAG) based task dependencies
- Automatic execution order based on dependencies
- Parallel task execution
- Cycle detection and validation

### 4. Persistent Storage
- SQLite database for task history
- Execution statistics and analytics
- Export data to JSON

### 5. Web Dashboard
- Beautiful web interface built with FastAPI
- Real-time updates via WebSocket
- Task management UI
- Resource usage graphs

### 6. CLI Tool
Full command-line interface for:
- Task creation, listing, and deletion
- Task execution
- Statistics viewing
- DAG operations
- Data export

---

## Installation

```bash
# Clone the repository
cd apscheduler-master

# Install in editable mode
pip install -e .

# Install with all features
pip install -e ".[ai-scheduler]"
```

---

## Quick Start

### 1. Start the Web Dashboard

```bash
py -m ai_scheduler.cli run
```

Then open: **http://localhost:8000**

### 2. Run the Demo

```bash
py examples/ai_scheduler_full_demo.py
```

### 3. Use the CLI

```bash
# Add a task
py -m ai_scheduler.cli task add --id task1 --name "Data Processing" --complexity 8 --deadline "2026-03-30T12:00"

# List tasks
py -m ai_scheduler.cli task list

# View statistics
py -m ai_scheduler.cli stats

# Export data
py -m ai_scheduler.cli export --output my_tasks.json
```

---

## Project Structure

```
src/ai_scheduler/
├── priority_scorer.py     # AI priority scoring engine
├── resource_monitor.py     # CPU/memory tracking
├── dashboard.py            # Console visualization
├── storage.py              # SQLite persistence
├── dag.py                  # Task dependency graphs
├── web.py                  # FastAPI web dashboard
└── cli.py                  # Command-line interface

examples/
├── ai_scheduler_demo.py        # Basic demo
└── ai_scheduler_full_demo.py   # Complete feature demo
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web Dashboard |
| `/api/tasks` | GET | List all tasks |
| `/api/tasks` | POST | Create new task |
| `/api/tasks/{id}` | GET | Get task details |
| `/api/tasks/execute-next` | POST | Execute highest priority task |
| `/api/dashboard` | GET | Dashboard data |
| `/api/stats` | GET | Execution statistics |
| `/api/dag` | GET | DAG information |
| `/api/dag/validate` | POST | Validate DAG |
| `/api/export` | GET | Export all data |

---

## Example Usage

### Python Code Example

```python
from ai_scheduler import (
    AIPriorityScorer,
    PriorityConfig,
    ResourceMonitor,
    Dashboard,
    TaskStorage,
    TaskDAG,
)

# Initialize components
scorer = AIPriorityScorer()
monitor = ResourceMonitor()
dashboard = Dashboard()
storage = TaskStorage()

# Register a task with AI priority scorer
scorer.register_task(
    task_id="data_processing",
    complexity=8.0,
    deadline=datetime.now() + timedelta(hours=1),
)

# Get AI-calculated priority
priority = scorer.get_priority_score("data_processing")
print(f"Task priority: {priority}")

# Monitor resources
monitor.start()
usage = monitor.record_sample()
print(f"CPU: {usage.cpu_percent}%, Memory: {usage.memory_percent}%")

# Create task dependencies
dag = TaskDAG()
dag.add_task("fetch", "Fetch Data")
dag.add_task("process", "Process Data")
dag.tasks["process"].dependencies = ["fetch"]
```

---

## How AI Priority Works

The priority score is calculated as:

```
Priority = (Deadline_Score × 0.4) + (Complexity_Score × 0.3) + (History_Score × 0.3)
```

- **Deadline Score**: Higher for tasks closer to deadline (0-100)
- **Complexity Score**: Based on task complexity (1-10)
- **History Score**: Based on execution time and success rate (0-50)

The scheduler learns from execution history and adjusts scores accordingly.

---

## Technologies Used

- **Python 3.10+** - Core language
- **FastAPI** - Web framework
- **SQLite** - Local database
- **psutil** - System resource monitoring
- **Rich** - Beautiful terminal output

---

## For AI Automation Engineers

TaskMind is designed for AI/ML workflows:

1. **Data Processing Pipelines** - Schedule data collection, cleaning, preprocessing
2. **Model Training** - Queue training jobs with dependency management
3. **Batch Inference** - Schedule large-scale inference tasks
4. **Pipeline Orchestration** - DAG-based workflows for complex AI pipelines

---

## License

MIT License - See LICENSE.txt

---

**TaskMind** - *Intelligent task scheduling powered by AI*
