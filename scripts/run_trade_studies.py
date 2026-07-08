#!/usr/bin/env python
"""
Runs all parameter trade studies and generates CSV records and plots.
"""
import os
import sys
import pandas as pd
import numpy as np

# Add src/ to pythonpath
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from cubesat_thermal.data_io import ProjectData
from cubesat_thermal.analysis import (
    run_radiator_area_trade,
    run_radiator_area_system_trade,
    run_heater_power_trade,
    run_radiator_material_trade,
    run_strap_conductance_trade,
    run_battery_isolation_trade,
    run_payload_radiator_trade
)
from cubesat_thermal.plotting import (
    plot_radiator_area_trade,
    plot_radiator_system_trade,
    plot_heater_power_trade,
    plot_material_candidates,
    plot_strap_conductance_trade,
    plot_battery_isolation_trade,
    plot_payload_radiator_trade
)


def main():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, 'data')
    trades_out_dir = os.path.join(project_root, 'outputs', 'trades')
    os.makedirs(trades_out_dir, exist_ok=True)
    
    print("Loading project tables...")
    project = ProjectData(data_dir)
    
    # Load scenarios
    nominal_scenario = project.load_scenario(os.path.join(data_dir, 'scenarios', 'nominal.yaml'))
    hot_scenario = project.load_scenario(os.path.join(data_dir, 'scenarios', 'hot.yaml'))
    cold_scenario = project.load_scenario(os.path.join(data_dir, 'scenarios', 'cold.yaml'))
    cold_stress_scenario = project.load_scenario(os.path.join(data_dir, 'scenarios', 'cold_stress.yaml'))
    
    print("\n--------------------------------------------------")
    print("RUNNING TRADE STUDY A: RADIATOR AREA")
    print("--------------------------------------------------")
    areas = [0.005, 0.010, 0.015, 0.020, 0.025, 0.030, 0.035, 0.040]
    area_df = run_radiator_area_trade(hot_scenario, areas)
    area_csv = os.path.join(trades_out_dir, 'radiator_area_trade.csv')
    area_df.to_csv(area_csv, index=False)
    print(f"Saved Area Trade to {area_csv}")
    print(area_df.to_string(index=False))
    
    # Avionics max temp limit is 60 C
    plot_radiator_area_trade(area_df, limit_max_c=60.0, out_dir=trades_out_dir)

    print("\n--------------------------------------------------")
    print("RUNNING DUAL-AXIS RADIATOR SIZING SYSTEM TRADE")
    print("--------------------------------------------------")
    system_areas = [0.02, 0.03, 0.04, 0.05, 0.06]
    system_trade_df = run_radiator_area_system_trade(nominal_scenario, hot_scenario, cold_scenario, system_areas)
    system_trade_csv = os.path.join(trades_out_dir, 'radiator_area_system_trade.csv')
    system_trade_df.to_csv(system_trade_csv, index=False)
    print(f"Saved Radiator Sizing System Trade to {system_trade_csv}")
    print(system_trade_df.to_string(index=False))
    
    plot_radiator_system_trade(system_trade_df, limit_max_c=60.0, limit_min_c=-10.0, out_dir=trades_out_dir)

    
    print("\n--------------------------------------------------")
    print("RUNNING TRADE STUDY B: BATTERY HEATER POWER")
    print("--------------------------------------------------")
    powers = [0.0, 2.0, 5.0, 8.0, 10.0, 12.0, 15.0]
    heater_df = run_heater_power_trade(cold_scenario, powers)
    heater_csv = os.path.join(trades_out_dir, 'heater_power_trade.csv')
    heater_df.to_csv(heater_csv, index=False)
    print(f"Saved Heater Trade to {heater_csv}")
    print(heater_df.to_string(index=False))
    
    # Battery min temp limit is -10 C
    plot_heater_power_trade(heater_df, limit_min_c=-10.0, out_dir=trades_out_dir)
    
    print("\n--------------------------------------------------")
    print("RUNNING TRADE STUDY C: RADIATOR MATERIAL Candidates")
    print("--------------------------------------------------")
    material_df = run_radiator_material_trade(hot_scenario, project.materials_df)
    material_csv = os.path.join(trades_out_dir, 'radiator_material_trade.csv')
    material_df.to_csv(material_csv, index=False)
    print(f"Saved Material Trade to {material_csv}")
    print(material_df.to_string(index=False))
    
    plot_material_candidates(project.materials_df, selected_rad_mat='0.005″ FEP/Ag/Inconel', 
                             selected_shell_mat='AZ-93 Silicate', out_dir=trades_out_dir)


    
    print("\n--------------------------------------------------")
    print("RUNNING TRADE STUDY D: AVIONICS THERMAL STRAP CONDUCTANCE")
    print("--------------------------------------------------")
    conductances = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    strap_df = run_strap_conductance_trade(hot_scenario, conductances)
    strap_csv = os.path.join(trades_out_dir, 'strap_conductance_trade.csv')
    strap_df.to_csv(strap_csv, index=False)
    print(f"Saved Strap Trade to {strap_csv}")
    print(strap_df.to_string(index=False))
    
    plot_strap_conductance_trade(strap_df, out_dir=trades_out_dir)
    
    print("\n--------------------------------------------------")
    print("RUNNING TRADE STUDY E: BATTERY TO STRUCTURE ISOLATION")
    print("--------------------------------------------------")
    g_bat_struct = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
    bat_iso_df = run_battery_isolation_trade(hot_scenario, cold_stress_scenario, g_bat_struct)
    bat_iso_csv = os.path.join(trades_out_dir, 'battery_isolation_trade.csv')
    bat_iso_df.to_csv(bat_iso_csv, index=False)
    print(f"Saved Battery Isolation Trade to {bat_iso_csv}")
    print(bat_iso_df.to_string(index=False))
    
    # Battery limits: -10 C to 45 C
    plot_battery_isolation_trade(bat_iso_df, limit_min_c=-10.0, limit_max_c=45.0, out_dir=trades_out_dir)
    
    print("\n--------------------------------------------------")
    print("RUNNING TRADE STUDY F: PAYLOAD TO RADIATOR STRAP")
    print("--------------------------------------------------")
    g_pl_rad = [0.0, 0.2, 0.5, 1.0, 2.0, 5.0]
    pl_rad_df = run_payload_radiator_trade(hot_scenario, g_pl_rad)
    pl_rad_csv = os.path.join(trades_out_dir, 'payload_radiator_trade.csv')
    pl_rad_df.to_csv(pl_rad_csv, index=False)
    print(f"Saved Payload-Radiator Trade to {pl_rad_csv}")
    print(pl_rad_df.to_string(index=False))
    
    # Payload limit: 50 C
    plot_payload_radiator_trade(pl_rad_df, limit_max_c=50.0, out_dir=trades_out_dir)
    
    print(f"\nAll trade studies finished. Plots saved in: {trades_out_dir}")

if __name__ == '__main__':
    main()
