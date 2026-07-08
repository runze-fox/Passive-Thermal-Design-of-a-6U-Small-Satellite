"""
Post-processing, margin checking, and parametric trade studies.
"""
import copy
import numpy as np
import pandas as pd
from .solver import ThermalSimulation

def classify_node_margin(lower_margin: float, upper_margin: float) -> str:
    """Classifies a margin into one of the four tiers."""
    val = min(lower_margin, upper_margin)
    if val < 0.0:
        return "FAIL"
    elif val < 2.0:
        return "marginal pass"
    elif val <= 5.0:
        return "acceptable preliminary pass"
    else:
        return "robust pass"

def compute_temperature_margins(results: dict, components_df: pd.DataFrame) -> dict:
    """
    Computes upper and lower temperature margins [°C] for each node
    against limits specified in components_df.
    
    Upper margin = T_limit_max - T_predicted_max
    Lower margin = T_predicted_min - T_limit_min
    
    Returns:
        dict: margin data and 4-tier status classification summary
    """
    margins = {}
    
    comp_limits = components_df.set_index('node_id')
    
    for n_id in results['temperatures_c'].keys():
        t_history = results['temperatures_c'][n_id]
        
        period_s = results['orbit_period_s']
        times = results['times_s']
        t_final = times[-1]
        
        # Filter data in the final orbit (t >= t_final - period_s)
        final_orbit_mask = times >= (t_final - period_s - 0.1) # small buffer
        t_orbit = t_history[final_orbit_mask]
        
        t_min = float(np.min(t_orbit))
        t_max = float(np.max(t_orbit))
        
        limit_min = float(comp_limits.loc[n_id, 'temperature_min_c'])
        limit_max = float(comp_limits.loc[n_id, 'temperature_max_c'])
        
        lower_margin = t_min - limit_min
        upper_margin = limit_max - t_max
        
        node_status = classify_node_margin(lower_margin, upper_margin)
            
        margins[n_id] = {
            'min_predicted_c': t_min,
            'max_predicted_c': t_max,
            'min_limit_c': limit_min,
            'max_limit_c': limit_max,
            'lower_margin_c': lower_margin,
            'upper_margin_c': upper_margin,
            'status': node_status
        }
        
    # Analyze heater duty cycle over final orbit
    heater_pow = results['heater_power_w']
    times_arr = results['times_s']
    t_final = times_arr[-1]
    final_orbit_mask = times_arr >= (t_final - period_s - 0.1)
    
    orbit_heater_power = heater_pow[final_orbit_mask]
    orbit_times = times_arr[final_orbit_mask]
    
    dt = orbit_times[1] - orbit_times[0] if len(orbit_times) > 1 else 1.0
    total_energy_j = np.sum(orbit_heater_power) * dt
    energy_wh = total_energy_j / 3600.0
    
    max_heater_power = results['heater_power_w'].max()
    duty_cycle = 0.0
    if max_heater_power > 0:
        heater_state = results['heater_state'][final_orbit_mask]
        duty_cycle = float(np.mean(heater_state))
        
    margins['heater'] = {
        'duty_cycle': duty_cycle,
        'energy_per_orbit_wh': energy_wh
    }
    
    # Determine overall status as the worst status across all nodes
    status_priority = {
        "FAIL": 0,
        "marginal pass": 1,
        "acceptable preliminary pass": 2,
        "robust pass": 3
    }
    worst_priority = 3
    for n_id in results['temperatures_c'].keys():
        p = status_priority[margins[n_id]['status']]
        if p < worst_priority:
            worst_priority = p
            
    priority_to_status = {v: k for k, v in status_priority.items()}
    margins['overall_status'] = priority_to_status[worst_priority]
    
    return margins

def run_radiator_area_trade(scenario: dict, areas: list) -> pd.DataFrame:
    """
    Sweeps radiator area and runs simulations under the hot case.
    """
    records = []
    sc = copy.deepcopy(scenario)
    
    for area in areas:
        surfaces = sc['resolved_surfaces']
        surfaces.loc[surfaces['surface_id'] == 'radiator_surface', 'area_m2'] = area
        
        sim = ThermalSimulation(sc)
        res = sim.simulate()
        margins = compute_temperature_margins(res, sc['resolved_components'])
        
        records.append({
            'radiator_area_m2': area,
            'peak_radiator_temp_c': margins['radiator']['max_predicted_c'],
            'peak_avionics_temp_c': margins['avionics']['max_predicted_c'],
            'peak_structure_temp_c': margins['structure']['max_predicted_c'],
            'avionics_margin_c': margins['avionics']['upper_margin_c'],
            'status': margins['overall_status']
        })
        
    return pd.DataFrame(records)

def run_radiator_area_system_trade(nominal_sc: dict, hot_sc: dict, cold_sc: dict, areas: list) -> pd.DataFrame:
    """
    Sweeps radiator area across nominal, hot, and cold scenarios.
    For each area, returns metrics for all three cases to illustrate the design trade-off.
    """
    records = []
    for area in areas:
        # 1. Hot Case
        h_sc = copy.deepcopy(hot_sc)
        h_sc['resolved_surfaces'].loc[h_sc['resolved_surfaces']['surface_id'] == 'radiator_surface', 'area_m2'] = area
        h_sim = ThermalSimulation(h_sc)
        h_res = h_sim.simulate()
        h_margins = compute_temperature_margins(h_res, h_sc['resolved_components'])
        
        # 2. Nominal Case
        n_sc = copy.deepcopy(nominal_sc)
        n_sc['resolved_surfaces'].loc[n_sc['resolved_surfaces']['surface_id'] == 'radiator_surface', 'area_m2'] = area
        n_sim = ThermalSimulation(n_sc)
        n_res = n_sim.simulate()
        n_margins = compute_temperature_margins(n_res, n_sc['resolved_components'])
        
        # 3. Cold Case
        c_sc = copy.deepcopy(cold_sc)
        c_sc['resolved_surfaces'].loc[c_sc['resolved_surfaces']['surface_id'] == 'radiator_surface', 'area_m2'] = area
        c_sim = ThermalSimulation(c_sc)
        c_res = c_sim.simulate()
        c_margins = compute_temperature_margins(c_res, c_sc['resolved_components'])
        
        records.append({
            'radiator_area_m2': area,
            'hot_peak_avionics_c': h_margins['avionics']['max_predicted_c'],
            'hot_peak_battery_c': h_margins['battery']['max_predicted_c'],
            'nom_peak_avionics_c': n_margins['avionics']['max_predicted_c'],
            'nom_peak_battery_c': n_margins['battery']['max_predicted_c'],
            'cold_min_avionics_c': c_margins['avionics']['min_predicted_c'],
            'cold_min_battery_c': c_margins['battery']['min_predicted_c'],
            'cold_heater_duty_cycle': c_margins['heater']['duty_cycle'],
            'cold_heater_energy_wh': c_margins['heater']['energy_per_orbit_wh']
        })
        
    return pd.DataFrame(records)


def run_heater_power_trade(scenario: dict, powers: list) -> pd.DataFrame:
    """
    Sweeps battery survival heater power and runs simulations under the cold case.
    """
    records = []
    sc = copy.deepcopy(scenario)
    
    for power in powers:
        sc['heater']['power_w'] = power
        
        sim = ThermalSimulation(sc)
        res = sim.simulate()
        margins = compute_temperature_margins(res, sc['resolved_components'])
        
        records.append({
            'heater_power_w': power,
            'min_battery_temp_c': margins['battery']['min_predicted_c'],
            'battery_lower_margin_c': margins['battery']['lower_margin_c'],
            'heater_duty_cycle': margins['heater']['duty_cycle'],
            'heater_energy_wh': margins['heater']['energy_per_orbit_wh'],
            'status': margins['overall_status']
        })
        
    return pd.DataFrame(records)

def run_radiator_material_trade(scenario: dict, materials_df: pd.DataFrame) -> pd.DataFrame:
    """
    Sweeps through candidate materials for the radiator and runs simulations under the hot case.
    """
    records = []
    sc = copy.deepcopy(scenario)
    prop_type = sc.get('material_property_type', 'bol').lower()
    
    for _, mat in materials_df.iterrows():
        mat_id = mat['material_id']
        surfaces = sc['resolved_surfaces']
        surfaces.loc[surfaces['surface_id'] == 'radiator_surface', 'material_id'] = mat_id
        
        alpha = mat['alpha_s_BOL']
        epsilon = mat['epsilon_IR']

        
        surfaces.loc[surfaces['surface_id'] == 'radiator_surface', 'alpha_s'] = alpha
        surfaces.loc[surfaces['surface_id'] == 'radiator_surface', 'epsilon_ir'] = epsilon
        
        sim = ThermalSimulation(sc)
        res = sim.simulate()
        margins = compute_temperature_margins(res, sc['resolved_components'])
        
        records.append({
            'material_id': mat_id,
            'alpha_s': alpha,
            'epsilon_ir': epsilon,
            'peak_radiator_temp_c': margins['radiator']['max_predicted_c'],
            'peak_avionics_temp_c': margins['avionics']['max_predicted_c'],
            'avionics_margin_c': margins['avionics']['upper_margin_c'],
            'status': margins['overall_status']
        })
        
    return pd.DataFrame(records)

def run_strap_conductance_trade(scenario: dict, conductances: list) -> pd.DataFrame:
    """
    Sweeps the avionics-to-radiator thermal strap conductance and runs simulations under the hot case.
    """
    records = []
    sc = copy.deepcopy(scenario)
    
    for g in conductances:
        links = sc['thermal_links']
        mask = ((links['node_i'] == 'avionics') & (links['node_j'] == 'radiator')) | \
               ((links['node_i'] == 'radiator') & (links['node_j'] == 'avionics'))
        links.loc[mask, 'conductance_w_k'] = g
        
        sim = ThermalSimulation(sc)
        res = sim.simulate()
        margins = compute_temperature_margins(res, sc['resolved_components'])
        
        records.append({
            'strap_conductance_w_k': g,
            'peak_avionics_temp_c': margins['avionics']['max_predicted_c'],
            'peak_radiator_temp_c': margins['radiator']['max_predicted_c'],
            'temp_drop_avionics_to_rad_c': margins['avionics']['max_predicted_c'] - margins['radiator']['max_predicted_c'],
            'avionics_margin_c': margins['avionics']['upper_margin_c'],
            'status': margins['overall_status']
        })
        
    return pd.DataFrame(records)

def run_battery_isolation_trade(hot_scenario: dict, cold_scenario: dict, conductances: list) -> pd.DataFrame:
    """
    Sweeps the conductive coupling G between the battery and the structure.
    Runs the hot case for hot peak, and the cold stress case for cold minimum and heater energy.
    """
    records = []
    
    for g in conductances:
        # 1. Hot Case
        hot_sc = copy.deepcopy(hot_scenario)
        hot_links = hot_sc['thermal_links']
        mask_hot = ((hot_links['node_i'] == 'battery') & (hot_links['node_j'] == 'structure')) | \
                   ((hot_links['node_i'] == 'structure') & (hot_links['node_j'] == 'battery'))
        hot_links.loc[mask_hot, 'conductance_w_k'] = g
        
        hot_sim = ThermalSimulation(hot_sc)
        hot_res = hot_sim.simulate()
        hot_margins = compute_temperature_margins(hot_res, hot_sc['resolved_components'])
        
        # 2. Cold Stress Case
        cold_sc = copy.deepcopy(cold_scenario)
        cold_links = cold_sc['thermal_links']
        mask_cold = ((cold_links['node_i'] == 'battery') & (cold_links['node_j'] == 'structure')) | \
                    ((cold_links['node_i'] == 'structure') & (cold_links['node_j'] == 'battery'))
        cold_links.loc[mask_cold, 'conductance_w_k'] = g
        
        cold_sim = ThermalSimulation(cold_sc)
        cold_res = cold_sim.simulate()
        cold_margins = compute_temperature_margins(cold_res, cold_sc['resolved_components'])
        
        records.append({
            'battery_structure_conductance_w_k': g,
            'hot_battery_peak_c': hot_margins['battery']['max_predicted_c'],
            'cold_battery_min_c': cold_margins['battery']['min_predicted_c'],
            'heater_duty_cycle': cold_margins['heater']['duty_cycle'],
            'heater_energy_wh': cold_margins['heater']['energy_per_orbit_wh'],
            'hot_case_status': hot_margins['overall_status'],
            'cold_case_status': cold_margins['overall_status']
        })
        
    return pd.DataFrame(records)

def run_payload_radiator_trade(hot_scenario: dict, conductances: list) -> pd.DataFrame:
    """
    Sweeps equivalent conductive path conductance between payload and radiator under the hot case.
    """
    records = []
    
    for g in conductances:
        hot_sc = copy.deepcopy(hot_scenario)
        links = hot_sc['thermal_links']
        
        # Add payload-to-radiator link row
        new_link = pd.DataFrame([{
            'node_i': 'payload',
            'node_j': 'radiator',
            'conductance_w_k': g,
            'link_type': 'conductive',
            'basis': 'trade_study',
            'source_or_assumption_id': 'TRADE_PL_RAD',
            'notes': 'Payload-to-radiator sweep link'
        }])
        hot_sc['thermal_links'] = pd.concat([links, new_link], ignore_index=True)
        
        sim = ThermalSimulation(hot_sc)
        res = sim.simulate()
        margins = compute_temperature_margins(res, hot_sc['resolved_components'])
        
        records.append({
            'payload_radiator_conductance_w_k': g,
            'peak_payload_temp_c': margins['payload']['max_predicted_c'],
            'peak_radiator_temp_c': margins['radiator']['max_predicted_c'],
            'payload_margin_c': margins['payload']['upper_margin_c'],
            'status': margins['overall_status']
        })
        
    return pd.DataFrame(records)
