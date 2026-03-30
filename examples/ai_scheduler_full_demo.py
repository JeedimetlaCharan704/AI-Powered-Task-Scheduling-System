#!/usr/bin/env python3
from __future__ import annotations

import time
import random
from datetime import datetime, timedelta

from ai_scheduler import (
    AIPriorityScorer,
    PriorityConfig,
    ResourceMonitor,
    ResourceAwareScheduler,
    Dashboard,
    TaskStorage,
    TaskDAG,
    DAGExecutor,
)


def example_task(name: str, duration: float = 1.0):
    print(f"  [EXEC] {name} - started")
    time.sleep(duration)
    print(f"  [EXEC] {name} - completed")
    return f"{name} result"


def demo_priority_scorer():
    print("\n" + "=" * 60)
    print("DEMO 1: AI Priority Scorer")
    print("=" * 60)

    scorer = AIPriorityScorer(PriorityConfig(
        deadline_weight=0.5,
        complexity_weight=0.3,
        history_weight=0.2,
    ))

    tasks = [
        ("data_processing", "Data Processing", 8.0, datetime.now() + timedelta(hours=1)),
        ("model_training", "Model Training", 9.0, datetime.now() + timedelta(hours=4)),
        ("report_gen", "Report Generation", 3.0, datetime.now() + timedelta(minutes=30)),
        ("backup", "Data Backup", 4.0, datetime.now() + timedelta(hours=6)),
        ("notification", "Email Notification", 1.0, datetime.now() + timedelta(hours=2)),
    ]

    print("\nRegistering tasks:")
    for task_id, name, complexity, deadline in tasks:
        scorer.register_task(task_id, complexity=complexity, deadline=deadline)
        score = scorer.get_priority_score(task_id)
        print(f"  - {name}: Priority = {score:.2f}")

    print("\nTask Ranking (by priority):")
    ranking = scorer.get_task_ranking()
    for i, (task_id, score) in enumerate(ranking, 1):
        print(f"  {i}. {task_id}: {score:.2f}")

    print("\nSimulating task execution...")
    for task_id, _, _, _ in tasks[:3]:
        time.sleep(0.5)
        scorer.record_execution(task_id, duration=random.uniform(1, 3), success=True)

    print("\nUpdated rankings after learning:")
    ranking = scorer.get_task_ranking()
    for i, (task_id, score) in enumerate(ranking, 1):
        print(f"  {i}. {task_id}: {score:.2f}")


def demo_resource_monitor():
    print("\n" + "=" * 60)
    print("DEMO 2: Resource Monitor")
    print("=" * 60)

    monitor = ResourceMonitor(sampling_interval=0.2)
    monitor.start()

    print("\nMonitoring system resources...")
    for i in range(5):
        time.sleep(0.5)
        usage = monitor.record_sample()
        print(f"  Sample {i+1}: CPU={usage.cpu_percent:.1f}% | Memory={usage.memory_percent:.1f}%")

    print("\nStarting task tracking...")
    monitor.start_task_tracking("demo_task")

    for i in range(3):
        time.sleep(0.3)
        monitor.record_sample("demo_task")

    monitor.stop_task_tracking("demo_task")

    task_usage = monitor.get_task_usage("demo_task")
    print(f"\nTask 'demo_task' usage:")
    print(f"  Avg CPU: {task_usage['avg_cpu']:.1f}%")
    print(f"  Avg Memory: {task_usage['avg_memory']:.1f}%")
    print(f"  Samples: {task_usage['samples']}")

    print(f"\nSystem summary:")
    summary = monitor.get_system_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    monitor.stop()


def demo_dashboard():
    print("\n" + "=" * 60)
    print("DEMO 3: Dashboard")
    print("=" * 60)

    dashboard = Dashboard()

    print("\nRegistering tasks...")
    tasks = [
        ("task_1", "Data Processing", 75.0),
        ("task_2", "Model Training", 85.0),
        ("task_3", "Report Generation", 60.0),
    ]

    for task_id, name, priority in tasks:
        dashboard.register_task(task_id, name, priority)

    print("\nUpdating task statuses...")
    dashboard.start_task("task_1")
    dashboard.update_task_metrics("task_1", 45.5, 30.2)
    dashboard.complete_task("task_1", success=True)

    dashboard.start_task("task_2")
    dashboard.update_task_metrics("task_2", 80.0, 50.0)
    dashboard.complete_task("task_2", success=True)

    print("\nDashboard output:")
    dashboard.print_console()

    print("\nExporting to JSON...")
    json_data = dashboard.export_json()
    print(f"  Exported {len(json_data)} bytes")


def demo_storage():
    print("\n" + "=" * 60)
    print("DEMO 4: Persistent Storage (SQLite)")
    print("=" * 60)

    storage = TaskStorage("demo_scheduler.db")

    print("\nSaving tasks...")
    storage.save_task(
        "task_1",
        "Data Processing",
        complexity=8.0,
        estimated_duration=120.0,
        deadline=datetime.now() + timedelta(hours=2),
    )
    storage.save_task("task_2", "Model Training", complexity=9.0)
    storage.save_task("task_3", "Report Generation", complexity=4.0)

    print("\nAdding dependencies...")
    storage.add_dependency("task_2", "task_1")
    storage.add_dependency("task_3", "task_2")

    print("\nSaving execution history...")
    storage.save_execution(
        "task_1",
        started_at=datetime.now() - timedelta(minutes=30),
        completed_at=datetime.now() - timedelta(minutes=28),
        duration=120.0,
        success=True,
        cpu_avg=45.5,
        memory_avg=30.2,
    )

    print("\nRetrieving tasks:")
    tasks = storage.get_all_tasks()
    for task in tasks:
        print(f"  - {task['task_id']}: {task['name']} ({task['status']})")

    print("\nTask dependencies:")
    for task in tasks:
        deps = storage.get_dependencies(task['task_id'])
        if deps:
            print(f"  {task['task_id']} depends on: {deps}")

    print("\nExecution statistics:")
    stats = storage.get_execution_stats()
    print(f"  Total: {stats['total_executions']}")
    print(f"  Success rate: {stats['success_rate']}%")
    print(f"  Avg duration: {stats['avg_duration']}s")

    try:
        import os
        if os.path.exists("demo_scheduler.db"):
            os.remove("demo_scheduler.db")
            print("\nCleaned up demo database.")
    except PermissionError:
        print("\n(Database file left for cleanup)")


def demo_dag():
    print("\n" + "=" * 60)
    print("DEMO 5: Task Dependencies (DAG)")
    print("=" * 60)

    dag = TaskDAG()

    print("\nCreating task DAG...")
    dag.add_task("fetch_data", "Fetch Data", func=lambda: print("  -> Fetching data..."))
    dag.add_task("process", "Process Data", func=lambda: print("  -> Processing data..."))
    dag.add_task("train_model", "Train Model", func=lambda: print("  -> Training model..."))
    dag.add_task("evaluate", "Evaluate Model", func=lambda: print("  -> Evaluating model..."))
    dag.add_task("deploy", "Deploy Model", func=lambda: print("  -> Deploying model..."))
    dag.add_task("notify", "Send Notification", func=lambda: print("  -> Sending notification..."))

    dag.tasks["process"].dependencies = ["fetch_data"]
    dag.tasks["train_model"].dependencies = ["process"]
    dag.tasks["evaluate"].dependencies = ["train_model"]
    dag.tasks["deploy"].dependencies = ["evaluate"]
    dag.tasks["notify"].dependencies = ["deploy"]
    
    dag.tasks["fetch_data"].dependents = ["process"]
    dag.tasks["process"].dependents = ["train_model"]
    dag.tasks["train_model"].dependents = ["evaluate"]
    dag.tasks["evaluate"].dependents = ["deploy"]
    dag.tasks["deploy"].dependents = ["notify"]

    print("\nDAG validation:")
    is_valid, errors = dag.validate()
    print(f"  Valid: {is_valid}")
    if not is_valid:
        for error in errors:
            print(f"  Error: {error}")

    print("\nExecution order:", dag.get_execution_order())
    print("\nParallel batches:", dag.get_parallel_batches())

    print("\nDAG info:")
    info = dag.get_dag_info()
    for key, value in info.items():
        print(f"  {key}: {value}")


def demo_full_workflow():
    print("\n" + "=" * 60)
    print("DEMO 6: Full AI-Powered Workflow")
    print("=" * 60)

    scorer = AIPriorityScorer()
    monitor = ResourceMonitor(sampling_interval=0.2)
    storage = TaskStorage("workflow_demo.db")
    dashboard = Dashboard()

    monitor.start()

    tasks = [
        ("ml_pipeline_1", "Data Collection", 6.0, 300, timedelta(hours=1)),
        ("ml_pipeline_2", "Data Cleaning", 7.0, 200, timedelta(hours=2)),
        ("ml_pipeline_3", "Feature Engineering", 8.0, 400, timedelta(hours=3)),
        ("ml_pipeline_4", "Model Training", 9.0, 600, timedelta(hours=4)),
        ("ml_pipeline_5", "Model Evaluation", 5.0, 150, timedelta(hours=5)),
        ("ml_pipeline_6", "Deploy Model", 4.0, 100, timedelta(hours=6)),
    ]

    print("\n[1] Initializing AI Scheduler...")
    for task_id, name, complexity, duration, deadline in tasks:
        scorer.register_task(task_id, complexity, duration, datetime.now() + deadline)
        storage.save_task(task_id, name, complexity, duration, datetime.now() + deadline)
        dashboard.register_task(task_id, name, scorer.get_priority_score(task_id))

    storage.add_dependency("ml_pipeline_2", "ml_pipeline_1")
    storage.add_dependency("ml_pipeline_3", "ml_pipeline_2")
    storage.add_dependency("ml_pipeline_4", "ml_pipeline_3")
    storage.add_dependency("ml_pipeline_5", "ml_pipeline_4")
    storage.add_dependency("ml_pipeline_6", "ml_pipeline_5")

    print("\n[2] AI Priority Analysis:")
    ranking = scorer.get_task_ranking()
    for task_id, score in ranking[:3]:
        task_info = next(t for t in tasks if t[0] == task_id)
        print(f"  - {task_info[1]}: {score:.2f}")

    print("\n[3] Executing AI-Prioritized Tasks...")

    pending_tasks = [t[0] for t in tasks]
    execution_order = scorer.suggest_execution_order(pending_tasks)

    for task_id in execution_order[:3]:
        task_info = next(t for t in tasks if t[0] == task_id)
        print(f"\n  Executing: {task_info[1]}")

        dashboard.start_task(task_id)
        storage.update_task_status(task_id, "running")

        monitor.start_task_tracking(task_id)
        start_time = time.time()

        time.sleep(0.5)

        duration = time.time() - start_time
        monitor.stop_task_tracking(task_id)
        usage = monitor.get_task_usage(task_id)

        dashboard.update_task_metrics(task_id, usage["avg_cpu"], usage["avg_memory"])
        dashboard.complete_task(task_id, success=True)
        storage.update_task_status(task_id, "completed")

        storage.save_execution(
            task_id,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration=duration,
            success=True,
            cpu_avg=usage["avg_cpu"],
            memory_avg=usage["avg_memory"],
        )

        scorer.record_execution(task_id, duration, True)
        dashboard.update_priority(task_id, scorer.get_priority_score(task_id))

        print(f"    Duration: {duration:.2f}s")
        print(f"    CPU: {usage['avg_cpu']:.1f}% | Memory: {usage['avg_memory']:.1f}%")

    print("\n[4] System Statistics:")
    stats = storage.get_execution_stats()
    print(f"  Total executions: {stats['total_executions']}")
    print(f"  Success rate: {stats['success_rate']}%")
    print(f"  Avg CPU: {stats['avg_cpu_usage']:.1f}%")
    print(f"  Avg Memory: {stats['avg_memory_usage']:.1f}%")

    print("\n[5] Dashboard Summary:")
    summary = dashboard.get_task_summary()
    print(f"  Total tasks: {summary['total_tasks']}")
    print(f"  Running: {summary['running']}")
    print(f"  Completed: {summary['completed']}")
    print(f"  Success rate: {dashboard.get_success_rate()}%")

    monitor.stop()

    try:
        import os
        if os.path.exists("workflow_demo.db"):
            os.remove("workflow_demo.db")
            print("\n[6] Cleaned up demo database.")
    except PermissionError:
        print("\n[6] Database file left for cleanup.")


def main():
    print("=" * 60)
    print("  AI SCHEDULER - FULL FEATURE DEMONSTRATION")
    print("=" * 60)

    demo_priority_scorer()
    demo_resource_monitor()
    demo_dashboard()
    demo_storage()
    demo_dag()
    demo_full_workflow()

    print("\n" + "=" * 60)
    print("  ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nTo start the web dashboard: ai-scheduler run")
    print("To see CLI help: ai-scheduler --help")


if __name__ == "__main__":
    main()
