#!/usr/bin/env python
"""
Consolidates metrics and trade studies into a final technical note / report.
"""
import os
import sys
import json
import pandas as pd
import numpy as np

# Add src/ to pythonpath
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

def df_to_markdown(df: pd.DataFrame) -> str:
    """Manually formats a pandas DataFrame to a markdown table to avoid tabulate dependency."""
    cols = df.columns
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    separator = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, r in df.iterrows():
        row_cells = []
        for c in cols:
            val = r[c]
            if isinstance(val, (float, np.float64)):
                if abs(val) < 1.0 and val != 0.0:
                    row_cells.append(f"{val:.5f}")
                else:
                    row_cells.append(f"{val:.2f}")
            else:
                row_cells.append(str(val))
        rows.append("| " + " | ".join(row_cells) + " |")
    return "\n".join([header, separator] + rows)

def build_report():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    outputs_dir = os.path.join(project_root, 'outputs')
    
    print("Building report assets...")
    
    # Load case metrics
    cases = ['nominal', 'bounding_hot', 'bounding_cold', 'cold_stress']
    case_data = {}
    
    for case in cases:
        metrics_path = os.path.join(outputs_dir, case, 'metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                case_data[case] = json.load(f)
                
    # Build summary markdown
    summary_path = os.path.join(outputs_dir, 'summary_report.md')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("# Passive Thermal Design of a Small Satellite Under a High-Beta Bounding Hot Case - Summary Report\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> **Analysis Status:** Preliminary reference-informed thermal design. Not flight-qualified. This analysis serves as a verification concept and requires future correlation with detailed geometric models and TVAC / thermal-balance test.\n\n")
        
        # Case summary table
        f.write("## 1. Case Simulation Results\n\n")
        f.write("| Case | Status | Orbits Simulated | Battery Temp [°C] | Avionics Temp [°C] | Payload Temp [°C] | Structure Temp [°C] | Heater Duty Cycle | Heater Energy [Wh/orbit] |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
        
        for case in cases:
            if case not in case_data:
                continue
            data = case_data[case]
            
            # Extract temperatures
            bat = f"{data['battery']['min_c']:.1f} to {data['battery']['max_c']:.1f}"
            av = f"{data['avionics']['min_c']:.1f} to {data['avionics']['max_c']:.1f}"
            pl = f"{data['payload']['min_c']:.1f} to {data['payload']['max_c']:.1f}"
            struct = f"{data['structure']['min_c']:.1f} to {data['structure']['max_c']:.1f}"
            
            hc = data.get('heater', {})
            dc = f"{hc.get('duty_cycle', 0.0)*100:.1f}%"
            en = f"{hc.get('energy_per_orbit_wh', 0.0):.2f}"
            
            f.write(f"| `{case}` | **{data['result']}** | {data['periodic_orbits_simulated']} | {bat} | {av} | {pl} | {struct} | {dc} | {en} |\n")
            
        f.write("\n")
        
        # Trade studies section
        f.write("## 2. Trade Studies Summary\n\n")
        
        # Area trade
        area_csv = os.path.join(outputs_dir, 'trades', 'radiator_area_trade.csv')
        if os.path.exists(area_csv):
            f.write("### Trade A: Radiator Area Sweep (Hot Case)\n\n")
            df = pd.read_csv(area_csv)
            f.write(df_to_markdown(df))
            f.write("\n\n")
            
        # System area trade
        sys_area_csv = os.path.join(outputs_dir, 'trades', 'radiator_area_system_trade.csv')
        if os.path.exists(sys_area_csv):
            f.write("### Trade A2: System-Level Radiator Sizing Trade-Off (Hot vs. Cold Performance)\n\n")
            df = pd.read_csv(sys_area_csv)
            f.write(df_to_markdown(df))
            f.write("\n\n")

            
        # Heater power trade
        heater_csv = os.path.join(outputs_dir, 'trades', 'heater_power_trade.csv')
        if os.path.exists(heater_csv):
            f.write("### Trade B: Battery Survival Heater Power (Cold Case)\n\n")
            df = pd.read_csv(heater_csv)
            f.write(df_to_markdown(df))
            f.write("\n\n")
            
        # Material trade
        mat_csv = os.path.join(outputs_dir, 'trades', 'radiator_material_trade.csv')
        if os.path.exists(mat_csv):
            f.write("### Trade C: Radiator Material Coating Performance (Hot Case)\n\n")
            df = pd.read_csv(mat_csv)
            f.write(df_to_markdown(df))
            f.write("\n\n")
            
        # Strap trade
        strap_csv = os.path.join(outputs_dir, 'trades', 'strap_conductance_trade.csv')
        if os.path.exists(strap_csv):
            f.write("### Trade D: Avionics-to-Radiator Thermal Strap Conductance (Hot Case)\n\n")
            df = pd.read_csv(strap_csv)
            f.write(df_to_markdown(df))
            f.write("\n\n")
            
        # Battery isolation trade
        bat_iso_csv = os.path.join(outputs_dir, 'trades', 'battery_isolation_trade.csv')
        if os.path.exists(bat_iso_csv):
            f.write("### Trade E: Battery-to-Structure Conductive Isolation Sweep\n\n")
            df = pd.read_csv(bat_iso_csv)
            f.write(df_to_markdown(df))
            f.write("\n\n")
            
        # Payload-radiator conductance trade
        pl_rad_csv = os.path.join(outputs_dir, 'trades', 'payload_radiator_trade.csv')
        if os.path.exists(pl_rad_csv):
            f.write("### Trade F: Payload-to-Radiator Conductive Strap Sweep (Hot Case)\n\n")
            df = pd.read_csv(pl_rad_csv)
            f.write(df_to_markdown(df))
            f.write("\n\n")
            
    print(f"Summary report written to {summary_path}")

if __name__ == '__main__':
    build_report()
