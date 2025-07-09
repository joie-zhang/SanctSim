#!/usr/bin/env python3
"""
Test script to verify the parallel process fix works correctly.
Simulates multiple processes running simultaneously.
"""

import os
import time
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
import glob

def run_simulation(simulation_id):
    """Run a single simulation with unique ID"""
    print(f"Starting simulation {simulation_id}")
    
    # Run a short simulation 
    cmd = [
        "python", "code/main.py", 
        "--api-provider", "anthropic",
        "--model-name", "claude-3.5-sonnet",
        "--num-rounds", "3",  # Short for testing
        "--num-agents", "2"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
    
    if result.returncode == 0:
        print(f"✓ Simulation {simulation_id} completed successfully")
        return True
    else:
        print(f"✗ Simulation {simulation_id} failed: {result.stderr}")
        return False

def test_parallel_safety():
    """Test that multiple simulations don't interfere with each other"""
    print("=== TESTING PARALLEL PROCESS SAFETY ===")
    
    # Clean up any existing logs
    if os.path.exists("logs"):
        import shutil
        shutil.rmtree("logs")
    
    # Run 3 simulations in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_simulation, i) for i in range(1, 4)]
        results = [future.result() for future in futures]
    
    # Check results
    successful = sum(results)
    print(f"\nResults: {successful}/3 simulations completed successfully")
    
    # Check that separate directories were created
    log_dirs = glob.glob("logs/run_*")
    print(f"Created {len(log_dirs)} separate log directories:")
    for log_dir in sorted(log_dirs):
        info_files = glob.glob(f"{log_dir}/info_*.json")
        print(f"  {log_dir}: {len(info_files)} info files")
        
        # Check that files contain valid JSON
        for info_file in info_files:
            try:
                with open(info_file, 'r') as f:
                    data = json.load(f)
                    print(f"    ✓ {info_file}: Valid JSON with {len(data)} keys")
            except Exception as e:
                print(f"    ✗ {info_file}: Invalid JSON - {e}")
    
    return successful == 3 and len(log_dirs) >= 3

if __name__ == "__main__":
    success = test_parallel_safety()
    if success:
        print("\n🎉 PARALLEL SAFETY TEST PASSED!")
        print("Multiple simulations can now run safely in parallel.")
    else:
        print("\n❌ PARALLEL SAFETY TEST FAILED!")
        print("There are still race condition issues.")