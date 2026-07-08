import pytest
import os
from cubesat_thermal.data_io import ProjectData
from cubesat_thermal.validation import verify_steady_state_radiation

def test_single_node_radiation_validation():
    # Load project data to get base datasets
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    project = ProjectData(data_dir)
    
    # Load nominal scenario to use as base
    scenario_path = os.path.join(data_dir, 'scenarios', 'nominal.yaml')
    scenario = project.load_scenario(scenario_path)
    
    # Run radiation verification
    diff = verify_steady_state_radiation(scenario)
    
    # Verify that numerical and analytical steady-state temperatures differ by less than 0.1 Kelvin
    print(f"Radiation verification temperature difference: {diff:.6f} K")
    assert diff < 0.1, f"Failed steady-state radiation check: diff is {diff} K"
