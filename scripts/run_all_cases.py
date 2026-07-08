#!/usr/bin/env python
"""
Runs all scenario cases: nominal, bounding hot, and bounding cold.
"""
import os
import sys

# Add src/ to pythonpath
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from run_case import run_case

def run_all():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, 'data')
    output_dir = os.path.join(project_root, 'outputs')
    
    scenarios = [
        'nominal.yaml',
        'hot.yaml',
        'cold.yaml',
        'cold_stress.yaml'
    ]

    
    print("==================================================")
    print("RUNNING ALL CUBESAT THERMAL CASES")
    print("==================================================\n")
    
    results = {}
    for scenario_file in scenarios:
        scenario_path = os.path.join(data_dir, 'scenarios', scenario_file)
        if not os.path.exists(scenario_path):
            print(f"Error: Scenario file {scenario_path} not found.")
            continue
            
        print(f"\n>>> Running case: {scenario_file} <<<")
        try:
            res = run_case(scenario_path, data_dir, output_dir)
            results[scenario_file] = "SUCCESS"
        except Exception as e:
            print(f"Error executing {scenario_file}: {e}")
            import traceback
            traceback.print_exc()
            results[scenario_file] = f"FAILED: {e}"
            
    print("\n==================================================")
    print("SUMMARY OF ALL CASES")
    print("==================================================")
    for case, status in results.items():
        print(f"{case:<20}: {status}")
    print("==================================================\n")

if __name__ == '__main__':
    run_all()
