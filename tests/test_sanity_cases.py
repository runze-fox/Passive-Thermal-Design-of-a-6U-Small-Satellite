import pytest
import os
from cubesat_thermal.data_io import ProjectData
from cubesat_thermal.validation import verify_no_forcing_cooling
from cubesat_thermal.solver import ThermalSimulation
from cubesat_thermal.analysis import compute_temperature_margins

def test_no_forcing_cooling():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    project = ProjectData(data_dir)
    scenario_path = os.path.join(data_dir, 'scenarios', 'nominal.yaml')
    scenario = project.load_scenario(scenario_path)
    
    passed = verify_no_forcing_cooling(scenario)
    assert passed is True, "No-forcing cooling test failed (non-monotonic cooling or temperature rise)"

def test_energy_balance_nominal():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    project = ProjectData(data_dir)
    scenario_path = os.path.join(data_dir, 'scenarios', 'nominal.yaml')
    scenario = project.load_scenario(scenario_path)
    
    sim = ThermalSimulation(scenario)
    res = sim.simulate()
    
    # Check energy balance relative error
    rel_err = res['energy_balance']['overall_balance']['relative_error']
    print(f"Nominal case relative energy balance error: {rel_err:.6e}")
    # Verify relative error is very small (numerical integration accuracy limit)
    assert abs(rel_err) < 1e-3, f"Energy conservation failure: relative error is {rel_err}"

def test_heater_cycling_cold_stress():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    project = ProjectData(data_dir)
    scenario_path = os.path.join(data_dir, 'scenarios', 'cold_stress.yaml')
    scenario = project.load_scenario(scenario_path)
    
    sim = ThermalSimulation(scenario)
    res = sim.simulate()
    
    heater_states = res['heater_state']
    
    # Assert that the heater has cycled (switched state at least once)
    assert 1 in heater_states, "Heater did not turn ON during the cold stress scenario."
    assert 0 in heater_states, "Heater did not turn OFF during the cold stress scenario."
    
    # Check margins are classified under the 4-tier model
    margins = compute_temperature_margins(res, scenario['resolved_components'])
    assert margins['battery']['status'] in ('marginal pass', 'acceptable preliminary pass', 'robust pass')
