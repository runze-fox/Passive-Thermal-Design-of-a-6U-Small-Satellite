#!/usr/bin/env python
"""
CLI tool to run a single thermal simulation case.
Usage:
    python scripts/run_case.py --scenario data/scenarios/nominal.yaml
"""
import os
import sys
import argparse
import json

# Add src/ to pythonpath
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from cubesat_thermal.data_io import ProjectData
from cubesat_thermal.solver import ThermalSimulation
from cubesat_thermal.analysis import compute_temperature_margins
from cubesat_thermal.plotting import (
    plot_temperature_history, 
    plot_heat_load_timeline, 
    plot_temperature_margins
)

def run_case(scenario_path: str, data_dir: str, output_dir: str):
    print(f"Loading project data from: {data_dir}")
    project = ProjectData(data_dir)
    
    print(f"Loading scenario from: {scenario_path}")
    scenario = project.load_scenario(scenario_path)
    scenario_name = scenario['scenario_name']
    
    case_out_dir = os.path.join(output_dir, scenario_name)
    os.makedirs(case_out_dir, exist_ok=True)
    
    print(f"Running simulation for scenario: {scenario_name}...")
    sim = ThermalSimulation(scenario)
    res = sim.simulate()
    
    print(f"Simulation finished.")
    print(f"  Orbits simulated: {res['orbits_simulated']}")
    print(f"  Converged: {res['converged']}")
    
    # Check margins
    margins = compute_temperature_margins(res, scenario['resolved_components'])
    
    print("\n--- Temperature Margins Summary ---")
    for n_id, m in margins.items():
        if n_id in ['heater', 'overall_status']:
            continue
        print(f"Node '{n_id}': {m['min_predicted_c']:.1f}°C to {m['max_predicted_c']:.1f}°C")
        print(f"  Limits: {m['min_limit_c']:.1f}°C to {m['max_limit_c']:.1f}°C")
        print(f"  Lower Margin: {m['lower_margin_c']:.1f}°C | Upper Margin: {m['upper_margin_c']:.1f}°C | Status: {m['status']}")
        
    if 'heater' in margins:
        print(f"Battery Heater Duty Cycle: {margins['heater']['duty_cycle']*100:.1f}%")
        print(f"Heater Energy per Orbit: {margins['heater']['energy_per_orbit_wh']:.2f} Wh")
        
    print(f"Overall Status: {margins['overall_status']}")
    print("------------------------------------\n")
    
    # Save JSON summary
    metrics_path = os.path.join(case_out_dir, 'metrics.json')
    # Structure of metrics matching the requested format
    metrics = {
        "scenario": scenario_name,
        "result": margins['overall_status'],
        "periodic_orbits_simulated": res['orbits_simulated'],
        "converged": res['converged'],
        "selected_assumption_ids": list(scenario['assumptions']['assumption_id'].unique())
    }
    
    for n_id, m in margins.items():
        if n_id in ['heater', 'overall_status']:
            continue
        metrics[n_id] = {
            "min_c": m['min_predicted_c'],
            "max_c": m['max_predicted_c'],
            "lower_margin_c": m['lower_margin_c'],
            "upper_margin_c": m['upper_margin_c'],
            "status": m['status']
        }
        
    if 'heater' in margins:
        metrics['heater'] = {
            "duty_cycle": margins['heater']['duty_cycle'],
            "energy_per_orbit_wh": margins['heater']['energy_per_orbit_wh']
        }
        
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics JSON to {metrics_path}")
    
    # Save markdown report
    report_path = os.path.join(case_out_dir, 'report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Thermal Simulation Report: {scenario_name}\n\n")
        f.write(f"- **Description**: {scenario['description']}\n")
        f.write(f"- **Converged**: {res['converged']}\n")
        f.write(f"- **Orbits Simulated**: {res['orbits_simulated']}\n")
        f.write(f"- **Overall Verdict**: **{margins['overall_status']}**\n\n")
        
        f.write("## Component Temperatures and Margins\n\n")
        f.write("| Component | Min Temp [°C] | Max Temp [°C] | Lower Limit [°C] | Upper Limit [°C] | Lower Margin [°C] | Upper Margin [°C] | Status |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for n_id, m in margins.items():
            if n_id in ['heater', 'overall_status']:
                continue
            f.write(f"| `{n_id}` | {m['min_predicted_c']:.2f} | {m['max_predicted_c']:.2f} | {m['min_limit_c']:.2f} | {m['max_limit_c']:.2f} | {m['lower_margin_c']:.2f} | {m['upper_margin_c']:.2f} | **{m['status']}** |\n")
            
        f.write("\n## Thermal Control Performance\n\n")
        f.write(f"- **Heater Duty Cycle**: {margins['heater']['duty_cycle']*100:.2f}%\n")
        f.write(f"- **Heater Energy Consumption per Orbit**: {margins['heater']['energy_per_orbit_wh']:.3f} Wh\n\n")
        
        f.write("## Energy Bookkeeping Balance check\n\n")
        overall = res['energy_balance']['overall_balance']
        f.write(f"- **Thermal Energy Change (dE)**: {overall['dE_thermal_j']:.2f} J\n")
        f.write(f"- **Internal Dissipation Energy Input**: {overall['energy_input_internal_j']:.2f} J\n")
        f.write(f"- **Environmental Heat Input**: {overall['energy_input_env_j']:.2f} J\n")
        f.write(f"- **Heater Heat Input**: {overall['energy_input_heater_j']:.2f} J\n")
        f.write(f"- **Deep Space Radiation Output**: {overall['energy_output_space_radiation_j']:.2f} J\n")
        f.write(f"- **Energy Balance Residual**: {overall['residual_j']:.2f} J (Relative Error: {overall['relative_error']:.2e})\n\n")
        f.write("> [!NOTE]\n")
        f.write("> This is a preliminary, simplified, reference-informed thermal model rather than a flight-qualified design.\n")
        f.write("> It requires future correlation with detailed models and TVAC / thermal-balance test.\n")
        
    print(f"Saved Markdown report to {report_path}")
    
    # Generate figures
    print("Generating figures...")
    plot_temperature_history(res, scenario['resolved_components'], scenario['environment'], case_out_dir)
    plot_heat_load_timeline(res, scenario['environment'], case_out_dir)
    plot_temperature_margins(margins, case_out_dir)
    print(f"Figures saved in: {case_out_dir}")
    
    return res

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run CubeSat Thermal Case")
    parser.add_argument('--scenario', type=str, required=True, help="Path to scenario YAML file")
    parser.add_argument('--data-dir', type=str, default='data', help="Path to data directory")
    parser.add_argument('--output-dir', type=str, default='outputs', help="Path to save outputs")
    
    args = parser.parse_args()
    run_case(args.scenario, args.data_dir, args.output_dir)
