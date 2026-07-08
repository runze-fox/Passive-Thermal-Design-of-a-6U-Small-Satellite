"""
Programmatic validation and verification checks for code correctness.
"""
import copy
import numpy as np
import pandas as pd
from .solver import ThermalSimulation
from .network import SIGMA

def verify_no_forcing_cooling(base_scenario: dict) -> bool:
    """
    Validation Test 1: No forcing sanity test.
    - Zero out all internal dissipation.
    - Zero out all environmental fluxes (solar, albedo, Earth IR).
    - Initial temperature = 300 K.
    - Verify that all nodes cool monotonically towards deep space temperature (3 K).
    """
    sc = copy.deepcopy(base_scenario)
    
    # Zero environmental fluxes
    sc['environment']['solar_flux_w_m2'] = 0.0
    sc['environment']['albedo'] = 0.0
    sc['environment']['earth_ir_w_m2'] = 0.0
    
    # Zero internal dissipation
    sc['resolved_components']['nominal_dissipation_w'] = 0.0
    sc['resolved_components']['hot_dissipation_w'] = 0.0
    sc['resolved_components']['cold_dissipation_w'] = 0.0
    
    sc['payload_power']['dissipation_active_w'] = 0.0
    sc['payload_power']['dissipation_inactive_w'] = 0.0
    sc['payload_power']['duration_active_s'] = 0.0
    
    # Disable heater
    sc['heater']['power_w'] = 0.0
    
    # Set run settings
    sc['simulation']['max_orbits'] = 3
    sc['simulation']['initial_temperature_c'] = 27.0 # 300.15 K
    sc['simulation']['convergence_threshold_c'] = 0.0 # run full orbits
    
    sim = ThermalSimulation(sc)
    res = sim.simulate()
    
    temps = res['temperatures_k']
    
    # Verify monotonic decrease for all nodes
    passed = True
    for n_id, t_arr in temps.items():
        # Check if temperatures are strictly decreasing or constant (if isolated, but here coupled)
        # Note: at least nodes attached to surfaces must cool monotonically.
        # Nodes internally coupled to them might warm up slightly initially if their initial temperatures
        # are lower, but since all start at 300K and heat flows only to space, all temperatures should decrease.
        diffs = np.diff(t_arr)
        # Verify that overall trend is cooling and no step increases temperature above 300.15
        if not (diffs <= 0.001).all(): # allow tiny numerical noise
            passed = False
            print(f"FAILED: Node {n_id} has temperature increase during cooling test.")
            
        final_temp = t_arr[-1]
        if final_temp >= t_arr[0]:
            passed = False
            print(f"FAILED: Node {n_id} did not cool down. Initial: {t_arr[0]} K, Final: {final_temp} K")
            
    return passed

def verify_steady_state_radiation(base_scenario: dict) -> float:
    """
    Validation Test 2: Steady-state radiation sanity test.
    - Isolate the radiator node (conductances set to 0).
    - Constant internal dissipation on radiator = 10 W.
    - Zero out external environmental loads (solar, albedo, Earth IR) on radiator.
    - Set space view factor of radiator surface = 1.0.
    - Space temperature = 0 K (for simple equation compliance).
    - Compare numerical steady-state temperature with analytical:
      T_analytical = (Q / (epsilon * sigma * A))^(1/4)
    
    Returns:
        float: Absolute difference in Kelvin between numerical and analytical results.
    """
    sc = copy.deepcopy(base_scenario)
    
    # Isolate radiator links
    links = sc['thermal_links']
    links['conductance_w_k'] = 0.0
    
    # Set radiator node properties
    sc['environment']['solar_flux_w_m2'] = 0.0
    sc['environment']['albedo'] = 0.0
    sc['environment']['earth_ir_w_m2'] = 0.0
    sc['environment']['space_temperature_k'] = 0.0 # for clean analytical match
    
    # Remove other surfaces, keep only radiator_surface
    surfaces = sc['resolved_surfaces']
    surfaces = surfaces[surfaces['surface_id'] == 'radiator_surface'].copy()
    surfaces.loc[surfaces['surface_id'] == 'radiator_surface', 'space_view_factor'] = 1.0
    surfaces.loc[surfaces['surface_id'] == 'radiator_surface', 'earth_view_factor'] = 0.0
    surfaces.loc[surfaces['surface_id'] == 'radiator_surface', 'solar_exposure_factor'] = 0.0
    sc['resolved_surfaces'] = surfaces
    
    # Set radiator node to constant dissipation = 10 W
    comp = sc['resolved_components']
    comp.loc[comp['node_id'] == 'radiator', 'nominal_dissipation_w'] = 10.0
    comp.loc[comp['node_id'] == 'radiator', 'hot_dissipation_w'] = 10.0
    comp.loc[comp['node_id'] == 'radiator', 'cold_dissipation_w'] = 10.0
    sc['resolved_components'] = comp
    
    # Let's run for 20 orbits to ensure steady state is reached
    sc['simulation']['max_orbits'] = 20
    sc['simulation']['timestep_s'] = 5.0
    sc['simulation']['convergence_threshold_c'] = 1e-5 # tight limit
    sc['simulation']['initial_temperature_c'] = 50.0
    
    sim = ThermalSimulation(sc)
    res = sim.simulate()
    
    # Numerical steady-state temp of radiator in Kelvin
    t_num = res['temperatures_k']['radiator'][-1]
    
    # Analytical steady-state calculation
    rad_row = surfaces[surfaces['surface_id'] == 'radiator_surface'].iloc[0]
    area = rad_row['area_m2']
    epsilon = rad_row['epsilon_ir']
    Q = 10.0
    
    t_analytical = (Q / (epsilon * SIGMA * area)) ** 0.25
    
    diff = abs(t_num - t_analytical)
    return diff
