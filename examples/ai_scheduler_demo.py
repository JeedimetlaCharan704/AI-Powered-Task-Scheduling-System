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
)


def simulate_task_execution(task_id: str, resource_monitor: ResourceMonitor, duration: float = 2.0) -> bool:
    resource_monitor.start_task_tracking(task_id)
    
    try:
        start_time = time.time()
        while time.time() - start_time < duration:
            resource_monitor.record_sample(task_id)
            time.sleep(0.5)
        return True
    except Exception:
        return False
    finally:
        resource_monitor.stop_task_tracking(task_id)


def main():
    print("=" * 60)
    print("AI Scheduler Demo - AI-Powered Task Scheduling System")
    print("=" * 60)
    
    priority_scorer = AIPriorityScorer(
        PriorityConfig(
            deadline_weight=0.5,
            complexity_weight=0.3,
            history_weight=0.2,
        )
    )
    
    resource_monitor = ResourceMonitor(sampling_interval=0.3)
    resource_monitor.start()
    
    resource_scheduler = ResourceAwareScheduler(resource_monitor)
    
    dashboard = Dashboard()
    
    tasks = [
        {
            "id": "task_1",
            "name": "Data Processing",
            "complexity": 8.0,
            "deadline": datetime.now() + timedelta(hours=1),
        },
        {
            "id": "task_2",
            "name": "Model Training",
            "complexity": 9.5,
            "deadline": datetime.now() + timedelta(hours=4),
        },
        {
            "id": "task_3",
            "name": "Report Generation",
            "complexity": 3.0,
            "deadline": datetime.now() + timedelta(minutes=30),
        },
        {
            "id": "task_4",
            "name": "Data Backup",
            "complexity": 4.0,
            "deadline": datetime.now() + timedelta(hours=6),
        },
        {
            "id": "task_5",
            "name": "Email Notification",
            "complexity": 1.0,
            "deadline": datetime.now() + timedelta(hours=2),
        },
    ]
    
    print("\n[1] Registering tasks with AI Priority Scorer...")
    for task in tasks:
        priority_scorer.register_task(
            task_id=task["id"],
            complexity=task["complexity"],
            estimated_duration=task["complexity"] * 10,
            deadline=task["deadline"],
        )
        dashboard.register_task(
            task_id=task["id"],
            name=task["name"],
            priority_score=priority_scorer.get_priority_score(task["id"]),
        )
        print(f"  - {task['name']}: Priority Score = {priority_scorer.get_priority_score(task['id']):.2f}")
    
    print("\n[2] AI Task Ranking (sorted by priority):")
    ranking = priority_scorer.get_task_ranking()
    for i, (task_id, score) in enumerate(ranking, 1):
        task_name = next(t["name"] for t in tasks if t["id"] == task_id)
        print(f"  {i}. {task_name}: {score:.2f}")
    
    print("\n[3] AI Suggested Execution Order:")
    task_ids = [t["id"] for t in tasks]
    execution_order = priority_scorer.suggest_execution_order(task_ids)
    for i, task_id in enumerate(execution_order, 1):
        task_name = next(t["name"] for t in tasks if t["id"] == task_id)
        print(f"  {i}. {task_name}")
    
    print("\n[4] Resource Monitoring (simulating tasks)...")
    resource_monitor.record_sample()
    time.sleep(1)
    
    for task_id in execution_order[:3]:
        task_info = next(t for t in tasks if t["id"] == task_id)
        print(f"\n  Executing: {task_info['name']}")
        
        dashboard.start_task(task_id)
        
        success = simulate_task_execution(task_id, resource_monitor, duration=1.5)
        
        usage = resource_monitor.get_task_usage(task_id)
        dashboard.update_task_metrics(task_id, usage["avg_cpu"], usage["avg_memory"])
        
        dashboard.complete_task(task_id, success=success)
        
        priority_scorer.record_execution(task_id, duration=1.5, success=success)
        dashboard.update_priority(task_id, priority_scorer.get_priority_score(task_id))
        
        print(f"    - CPU: {usage['avg_cpu']:.1f}%")
        print(f"    - Memory: {usage['avg_memory']:.1f}%")
        print(f"    - Status: {'SUCCESS' if success else 'FAILED'}")
    
    print("\n[5] System Resource Summary:")
    system_summary = resource_monitor.get_system_summary()
    for key, value in system_summary.items():
        print(f"  - {key}: {value}")
    
    print("\n[6] Dashboard Summary:")
    dashboard.print_console()
    
    print("\n[7] Updated Priority Scores (after execution):")
    for task in tasks:
        score = priority_scorer.get_priority_score(task["id"])
        print(f"  - {task['name']}: {score:.2f}")
    
    print("\n[8] Export Dashboard Data (JSON):")
    json_data = dashboard.export_json()
    print(f"  Dashboard data exported ({len(json_data)} bytes)")
    
    resource_monitor.stop()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
