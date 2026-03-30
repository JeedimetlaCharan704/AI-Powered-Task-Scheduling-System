#!/usr/bin/env python3
"""
Quick test script for AI Scheduler Web Dashboard
Starts the server and makes a test request
"""
import subprocess
import time
import sys
import os
import signal
import requests

def test_api():
    proc = None
    try:
        print("Starting AI Scheduler Web Dashboard...")
        proc = subprocess.Popen(
            [sys.executable, "-m", "ai_scheduler.cli", "run"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Waiting for server to start...")
        time.sleep(4)
        
        print("\nTesting APIs...\n")
        
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"[OK] Homepage: Status {response.status_code}")
        assert "<html" in response.text.lower(), "HTML content not found"
        
        response = requests.get("http://localhost:8000/api/dashboard", timeout=5)
        print(f"[OK] Dashboard API: Status {response.status_code}")
        data = response.json()
        print(f"    - Total tasks: {data.get('summary', {}).get('total_tasks', 0)}")
        
        response = requests.get("http://localhost:8000/api/stats", timeout=5)
        print(f"[OK] Stats API: Status {response.status_code}")
        
        response = requests.get("http://localhost:8000/api/dag", timeout=5)
        print(f"[OK] DAG API: Status {response.status_code}")
        
        print("\nAll API tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        return False
    finally:
        if proc:
            proc.terminate()
            proc.wait(timeout=5)

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
