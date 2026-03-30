# TaskMind - AI-Powered Task Scheduling System

![Status](https://img.shields.io/badge/status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-blue)
![Stars](https://img.shields.io/github/stars/JeedimetlaCharan704/AI-Powered-Task-Scheduling-System)

<div align="center">
  <img src="https://img.shields.io/badge/AI-Powered-FF6B6B?style=for-the-badge" alt="AI Powered">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge" alt="FastAPI">
  <img src="https://img.shields.io/badge/Real--time-4FC3F7?style=for-the-badge" alt="Real-time">
</div>

---

**TaskMind** is an intelligent task scheduling system that uses AI to prioritize and execute tasks based on deadline urgency, complexity, and historical performance. It monitors system resources, supports task dependencies (DAGs), and provides a beautiful real-time web dashboard.

---

## 🌟 Features

### 🤖 AI Priority Scoring
Tasks are automatically ranked using a smart algorithm that considers:
- **Deadline proximity** - Urgent tasks get higher priority
- **Task complexity** - More complex tasks are weighted appropriately  
- **Historical performance** - Learns from past executions to improve future scheduling

### 📊 Beautiful Dashboard
- **Dark theme** with glass morphism design
- **Real-time updates** every 2 seconds
- **Live resource charts** (CPU & Memory)
- **Task priority ranking** with visual indicators
- **Smooth animations** and modern UI

### 🖥️ Resource Monitoring
- Real-time CPU and memory usage tracking
- Per-task resource monitoring
- Live performance charts
- Automatic pausing when resources are scarce

### 🔗 Task Dependencies (DAG)
- Directed Acyclic Graph based task dependencies
- Automatic execution order based on dependencies
- Parallel task execution
- Cycle detection and validation

### 💾 Persistent Storage
- SQLite database for task history
- Execution statistics and analytics
- Export data to JSON

### 🖥️ Multiple Interfaces
- **Web Dashboard** - Beautiful real-time UI
- **REST API** - Full API for integration
- **CLI Tool** - Command-line interface

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/JeedimetlaCharan704/AI-Powered-Task-Scheduling-System.git
cd AI-Powered-Task-Scheduling-System

# Install dependencies
pip install -e ".[ai-scheduler]"
```

### 2. Start the Web Dashboard

```bash
py -m uvicorn ai_scheduler.web:app --reload
```

Then open: **http://localhost:8000**

### 3. Run the Demo

```bash
py examples/ai_scheduler_full_demo.py
```

---

## 🎨 Dashboard Preview

The dashboard features:
- 📈 Real-time resource monitoring with charts
- 🎯 AI-powered task priority ranking
- ⚡ Live task execution status
- 📊 Comprehensive statistics
- 🌙 Beautiful dark theme

---

## 📚 Project Structure

```
src/ai_scheduler/
├── __init__.py           # Module exports
├── priority_scorer.py     # AI priority scoring engine
├── resource_monitor.py    # CPU/memory tracking
├── dashboard.py           # Task dashboard
├── storage.py             # SQLite persistence
├── dag.py                 # Task dependency graphs
├── web.py                 # FastAPI web dashboard
└── cli.py                 # Command-line interface

examples/
├── ai_scheduler_demo.py        # Basic demo
└── ai_scheduler_full_demo.py   # Complete feature demo
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web Dashboard |
| `/api/tasks` | GET | List all tasks |
| `/api/tasks` | POST | Create new task |
| `/api/tasks/{id}` | GET | Get task details |
| `/api/tasks/execute-next` | POST | Execute highest priority task |
| `/api/tasks/completed` | DELETE | Clear completed tasks |
| `/api/dashboard` | GET | Dashboard data |
| `/api/stats` | GET | Execution statistics |
| `/api/dag` | GET | DAG information |
| `/api/dag/validate` | POST | Validate DAG |
| `/api/export` | GET | Export all data |

---

## 💻 CLI Usage

```bash
# Add a task
py -m ai_scheduler.cli task add --id task1 --name "Data Processing" --complexity 8 --deadline "2026-03-30T12:00"

# List tasks
py -m ai_scheduler.cli task list

# View statistics
py -m ai_scheduler.cli stats

# Export data
py -m ai_scheduler.cli export --output my_tasks.json

# Start web dashboard
py -m ai_scheduler.cli run
```

---

## 🧠 How AI Priority Works

The priority score is calculated as:

```
Priority = (Deadline_Score × 0.4) + (Complexity_Score × 0.3) + (History_Score × 0.3)
```

- **Deadline Score**: Higher for tasks closer to deadline (0-100)
- **Complexity Score**: Based on task complexity (1-10)
- **History Score**: Based on execution time and success rate (0-50)

The scheduler learns from execution history and adjusts scores accordingly.

---

## 🛠️ Technologies Used

<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/TailwindCSS-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind">
  <img src="https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chart.js&logoColor=white" alt="Chart.js">
  <img src="https://img.shields.io/badge/SQLite-003545?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/psutil-222222?style=for-the-badge&logo=python&logoColor=white" alt="psutil">
</div>

---

## 👨‍💻 For Developers

TaskMind is designed for AI/ML workflows:

1. **Data Processing Pipelines** - Schedule data collection, cleaning, preprocessing
2. **Model Training** - Queue training jobs with dependency management
3. **Batch Inference** - Schedule large-scale inference tasks
4. **Pipeline Orchestration** - DAG-based workflows for complex AI pipelines

---

## 📄 License

MIT License - See LICENSE.txt

---

<div align="center">
  <p><strong>TaskMind</strong> - Intelligent task scheduling powered by AI</p>
  <p>Made with ❤️ by Jeedimetla Charan</p>
</div>
