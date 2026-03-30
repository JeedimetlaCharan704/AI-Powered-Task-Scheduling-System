#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime

from ai_scheduler.priority_scorer import AIPriorityScorer, PriorityConfig
from ai_scheduler.resource_monitor import ResourceMonitor
from ai_scheduler.dashboard import Dashboard
from ai_scheduler.storage import TaskStorage
from ai_scheduler.dag import TaskDAG, DAGExecutor


def main():
    parser = argparse.ArgumentParser(description="AI Scheduler CLI", prog="ai-scheduler")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    task_parser = subparsers.add_parser("task", help="Task management")
    task_subparsers = task_parser.add_subparsers(dest="action")

    task_add = task_subparsers.add_parser("add", help="Add a new task")
    task_add.add_argument("--id", required=True, help="Task ID")
    task_add.add_argument("--name", required=True, help="Task name")
    task_add.add_argument("--complexity", type=float, default=1.0, help="Task complexity (1-10)")
    task_add.add_argument("--duration", type=float, default=60.0, help="Estimated duration (seconds)")
    task_add.add_argument("--deadline", help="Deadline (ISO format)")
    task_add.add_argument("--deps", nargs="*", help="Dependencies")

    task_list = task_subparsers.add_parser("list", help="List all tasks")
    task_list.add_argument("--status", help="Filter by status")

    task_exec = task_subparsers.add_parser("execute", help="Execute a task")
    task_exec.add_argument("--id", required=True, help="Task ID")

    task_del = task_subparsers.add_parser("delete", help="Delete a task")
    task_del.add_argument("--id", required=True, help="Task ID")

    subparsers.add_parser("run", help="Run the web dashboard")
    subparsers.add_parser("daemon", help="Run as a background scheduler")

    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--task", help="Task ID for task-specific stats")

    dag_parser = subparsers.add_parser("dag", help="DAG operations")
    dag_subparsers = dag_parser.add_subparsers(dest="dag_action")
    dag_validate = dag_subparsers.add_parser("validate", help="Validate DAG")
    dag_exec = dag_subparsers.add_parser("execute", help="Execute DAG")
    dag_exec.add_argument("--parallel", type=int, default=3, help="Max parallel tasks")

    export_parser = subparsers.add_parser("export", help="Export data")
    export_parser.add_argument("--output", default="ai_scheduler_export.json", help="Output file")

    args = parser.parse_args()

    storage = TaskStorage()

    if args.command == "task":
        handle_task_command(args, storage)
    elif args.command == "run":
        from ai_scheduler.web import run_server
        print("Starting AI Scheduler Web Dashboard on http://localhost:8000")
        run_server()
    elif args.command == "daemon":
        run_daemon(storage)
    elif args.command == "stats":
        show_stats(args, storage)
    elif args.command == "dag":
        handle_dag_command(args, storage)
    elif args.command == "export":
        export_data(args, storage)
    else:
        parser.print_help()


def handle_task_command(args, storage):
    priority_scorer = AIPriorityScorer()
    dashboard = Dashboard()

    if args.action == "add":
        deadline = datetime.fromisoformat(args.deadline) if args.deadline else None

        priority_scorer.register_task(
            task_id=args.id,
            complexity=args.complexity,
            estimated_duration=args.duration,
            deadline=deadline,
        )

        storage.save_task(
            task_id=args.id,
            name=args.name,
            complexity=args.complexity,
            estimated_duration=args.duration,
            deadline=deadline,
        )

        if args.deps:
            for dep in args.deps:
                storage.add_dependency(args.id, dep)

        score = priority_scorer.get_priority_score(args.id)
        print(f"Task '{args.id}' added with priority score: {score:.2f}")

        if args.deps:
            print(f"Dependencies: {', '.join(args.deps)}")

    elif args.action == "list":
        tasks = storage.get_all_tasks()
        if args.status:
            tasks = [t for t in tasks if t["status"] == args.status]

        if not tasks:
            print("No tasks found.")
            return

        print(f"{'Task ID':<20} {'Name':<25} {'Status':<12} {'Priority':<10}")
        print("-" * 70)

        for task in tasks:
            task_id = task["task_id"]
            priority = priority_scorer.get_priority_score(task_id)
            print(f"{task_id:<20} {task['name'][:24]:<25} {task['status']:<12} {priority:<10.2f}")

    elif args.action == "execute":
        task = storage.get_task(args.id)
        if not task:
            print(f"Task '{args.id}' not found.")
            return

        print(f"Executing task '{args.id}'...")
        storage.update_task_status(args.id, "running")

        time.sleep(1)

        storage.save_execution(
            task_id=args.id,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration=1.0,
            success=True,
        )

        storage.update_task_status(args.id, "completed")
        print(f"Task '{args.id}' completed successfully!")

    elif args.action == "delete":
        task = storage.get_task(args.id)
        if not task:
            print(f"Task '{args.id}' not found.")
            return

        storage.update_task_status(args.id, "deleted")
        print(f"Task '{args.id}' deleted.")


def run_daemon(storage):
    priority_scorer = AIPriorityScorer()
    resource_monitor = ResourceMonitor()
    dashboard = Dashboard()

    resource_monitor.start()

    print("AI Scheduler Daemon started. Press Ctrl+C to stop.")

    try:
        while True:
            tasks = storage.get_all_tasks()
            pending = [t for t in tasks if t["status"] == "pending"]

            if pending:
                task_ids = [t["task_id"] for t in pending]
                order = priority_scorer.suggest_execution_order(task_ids)

                print(f"Next task: {order[0] if order else 'None'}")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutting down...")
        resource_monitor.stop()


def show_stats(args, storage):
    if args.task:
        stats = storage.get_execution_stats(args.task)
        print(f"\nStatistics for task '{args.task}':")
    else:
        stats = storage.get_execution_stats()
        print("\nOverall Statistics:")

    print(f"  Total Executions: {stats['total_executions']}")
    print(f"  Successful: {stats['successful_executions']}")
    print(f"  Failed: {stats['failed_executions']}")
    print(f"  Success Rate: {stats['success_rate']}%")
    print(f"  Avg Duration: {stats['avg_duration']}s")
    print(f"  Avg CPU Usage: {stats['avg_cpu_usage']}%")
    print(f"  Avg Memory Usage: {stats['avg_memory_usage']}%")


def handle_dag_command(args, storage):
    dag = TaskDAG()

    tasks = storage.get_all_tasks()
    for task in tasks:
        deps = storage.get_dependencies(task["task_id"])
        dag.add_task(task["task_id"], task["name"], dependencies=deps if deps else None)

    if args.dag_action == "validate":
        is_valid, errors = dag.validate()
        if is_valid:
            print("DAG is valid!")
        else:
            print("DAG has errors:")
            for error in errors:
                print(f"  - {error}")

    elif args.dag_action == "execute":
        print(f"Executing DAG with max {args.parallel} parallel tasks...")
        executor = DAGExecutor(dag)
        result = executor.execute(max_parallel=args.parallel)
        print(f"\nCompleted: {result['completed']['completed']}/{result['completed']['total_tasks']}")

        if result['errors']:
            print("\nErrors:")
            for task_id, error in result['errors'].items():
                print(f"  {task_id}: {error}")


def export_data(args, storage):
    data = storage.export_data()

    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Data exported to '{args.output}'")
    print(f"  Tasks: {len(data['tasks'])}")
    print(f"  Executions: {len(data['executions'])}")
    print(f"  Dependencies: {len(data['dependencies'])}")


if __name__ == "__main__":
    main()
