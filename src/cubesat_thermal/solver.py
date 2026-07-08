"""
Numerical solver implementing fixed-step RK4 integration, thermostat scheduling,
and periodic steady-state convergence checking.
"""
import numpy as np
import pandas as pd
from .environment import is_sunlit, compute_node_environmental_loads
from .controls import HysteresisThermostat
from .network import ThermalNetwork

def compute_payload_power(t: float, sunlit_duration: float, eclipse_duration: float, payload_cfg: dict) -> float:
    """
    Computes payload power dissipation based on a periodic orbit schedule and phase shift.
    """
    period = sunlit_duration + eclipse_duration
    t_orbit = t % period
    
    # Payload schedule is phase shifted relative to sunlit entry (t_orbit = 0)
    start_time = payload_cfg.get('phase_shift_s', 0.0)
    active_duration = payload_cfg.get('duration_active_s', 0.0)
    end_time = start_time + active_duration
    
    # Check if t_orbit falls inside the active window (handling periodic wrap-around if any)
    if end_time <= period:
        is_active = (t_orbit >= start_time) and (t_orbit < end_time)
    else:
        # Wraps around the orbit period
        is_active = (t_orbit >= start_time) or (t_orbit < (end_time % period))
        
    if is_active:
        return payload_cfg.get('dissipation_active_w', 0.0)
    return payload_cfg.get('dissipation_inactive_w', 0.0)

def compute_node_internal_dissipation(t: float, node_id: str, comp_row: dict, payload_cfg: dict, sunlit_duration: float, eclipse_duration: float, scenario_name: str) -> float:
    """
    Returns the internal electronics dissipation [W] for a node at time t.
    """
    # Select dissipation column based on scenario
    if scenario_name == 'bounding_hot':
        base_power = comp_row.get('hot_dissipation_w', 0.0)
    elif scenario_name in ('bounding_cold', 'cold_stress'):
        base_power = comp_row.get('cold_dissipation_w', 0.0)

    else:
        base_power = comp_row.get('nominal_dissipation_w', 0.0)
        
    if node_id == 'payload':
        return compute_payload_power(t, sunlit_duration, eclipse_duration, payload_cfg)
    return base_power

class ThermalSimulation:
    def __init__(self, scenario: dict):
        self.scenario = scenario
        self.env = scenario['environment']
        self.payload_cfg = scenario['payload_power']
        self.heater_cfg = scenario['heater']
        self.sim_cfg = scenario['simulation']
        
        self.components_df = scenario['resolved_components']
        self.surfaces_df = scenario['resolved_surfaces']
        self.links_df = scenario['thermal_links']
        
        # Build network
        self.network = ThermalNetwork(self.components_df, self.links_df, self.surfaces_df)
        
        # Set up thermostat
        # Heater ON below heater_on_c, OFF above heater_off_c, initially OFF
        self.thermostat = HysteresisThermostat(
            t_on_c=self.heater_cfg['t_on_c'],
            t_off_c=self.heater_cfg['t_off_c'],
            initial_state=False
        )
        
        self.orbit_period = self.env['sunlit_duration_s'] + self.env['eclipse_duration_s']
        self.surfaces_list = self.surfaces_df.to_dict(orient='records')
        
    def thermal_rhs(self, t: float, temp_k: dict, heater_on: bool) -> dict:
        """
        Computes the rate of change of temperature dT/dt for each node.
        T_dict maps node_id to temperature in Kelvin.
        heater_on is a boolean indicating the fixed heater state for the step.
        """
        # Conduction flows
        cond_flows = self.network.compute_conduction_flows(temp_k)
        
        # Radiation flows
        rad_losses = self.network.compute_space_radiation_flows(temp_k, self.env['space_temperature_k'])
        
        # Environmental loads
        env_loads = compute_node_environmental_loads(t, self.env, self.surfaces_list)
        
        # Internal power & Heater power
        dT_dt = {}
        for n_id in self.network.node_ids:
            node = self.network.nodes[n_id]
            C = node['C_j_k']
            
            # Internal power
            q_int = compute_node_internal_dissipation(
                t, n_id, node, self.payload_cfg, 
                self.env['sunlit_duration_s'], self.env['eclipse_duration_s'],
                self.scenario['scenario_name']
            )
            
            # Heater power (only for battery node)
            q_heat = 0.0
            if n_id == 'battery':
                q_heat = self.heater_cfg['power_w'] if heater_on else 0.0
                
            q_env = env_loads.get(n_id, {'total': 0.0})['total']
            q_cond = cond_flows[n_id]
            q_rad = rad_losses[n_id]
            
            # Energy balance: C * dT/dt = Q_int + Q_env + Q_heater + Q_cond - Q_rad
            net_power = q_int + q_env + q_heat + q_cond - q_rad
            dT_dt[n_id] = net_power / C
            
        return dT_dt

    def simulate(self) -> dict:
        """
        Performs the time-stepping simulation using fixed-step RK4.
        Checks for periodic steady-state convergence.
        """
        dt = self.sim_cfg['timestep_s']
        max_orbits = self.sim_cfg['max_orbits']
        conv_threshold = self.sim_cfg['convergence_threshold_c']
        
        # Initialize temperatures in Kelvin
        init_temp_c = self.sim_cfg['initial_temperature_c']
        temp_k = {n_id: init_temp_c + 273.15 for n_id in self.network.node_ids}
        
        # History lists
        times = []
        temp_history = {n_id: [] for n_id in self.network.node_ids}
        heater_power_history = []
        heater_state_history = []
        internal_dissipation = {n_id: [] for n_id in self.network.node_ids}
        environmental_loads = {n_id: {'solar': [], 'albedo': [], 'earth_ir': [], 'total': []} for n_id in self.network.node_ids}
        space_radiation = {n_id: [] for n_id in self.network.node_ids}
        conduction_flows = {n_id: [] for n_id in self.network.node_ids}
        
        # To track convergence: store temperatures at orbit ends
        orbit_end_temps = []
        
        t = 0.0
        step = 0
        orbit_idx = 0
        
        # Total simulation steps per orbit
        steps_per_orbit = int(np.round(self.orbit_period / dt))
        actual_orbit_period = steps_per_orbit * dt # matches exactly integer steps
        
        converged = False
        
        # Run orbit by orbit
        for orbit_idx in range(max_orbits):
            # Save temperatures at start of this orbit
            orbit_start_temp = {n_id: temp_k[n_id] for n_id in self.network.node_ids}
            
            for _ in range(steps_per_orbit):
                # 1. Store state at start of step
                times.append(t)
                for n_id in self.network.node_ids:
                    temp_history[n_id].append(temp_k[n_id])
                
                # Heater state is piecewise constant during the step
                heater_on = self.thermostat.is_on
                heater_power = self.thermostat.get_power(self.heater_cfg['power_w'])
                heater_state_history.append(1 if heater_on else 0)
                heater_power_history.append(heater_power)
                
                # Log diagnostic variables (evaluated at start of step)
                env_loads = compute_node_environmental_loads(t, self.env, self.surfaces_list)
                conds = self.network.compute_conduction_flows(temp_k)
                rads = self.network.compute_space_radiation_flows(temp_k, self.env['space_temperature_k'])
                
                for n_id in self.network.node_ids:
                    node = self.network.nodes[n_id]
                    q_int = compute_node_internal_dissipation(
                        t, n_id, node, self.payload_cfg, 
                        self.env['sunlit_duration_s'], self.env['eclipse_duration_s'],
                        self.scenario['scenario_name']
                    )
                    internal_dissipation[n_id].append(q_int)
                    
                    e_loads = env_loads.get(n_id, {'solar': 0.0, 'albedo': 0.0, 'earth_ir': 0.0, 'total': 0.0})
                    environmental_loads[n_id]['solar'].append(e_loads['solar'])
                    environmental_loads[n_id]['albedo'].append(e_loads['albedo'])
                    environmental_loads[n_id]['earth_ir'].append(e_loads['earth_ir'])
                    environmental_loads[n_id]['total'].append(e_loads['total'])
                    
                    conduction_flows[n_id].append(conds[n_id])
                    space_radiation[n_id].append(rads[n_id])
                
                # 2. RK4 step integration
                # k1
                dt_k1 = self.thermal_rhs(t, temp_k, heater_on)
                
                # k2
                t_half = t + 0.5 * dt
                temp_k2 = {n_id: temp_k[n_id] + 0.5 * dt * dt_k1[n_id] for n_id in self.network.node_ids}
                dt_k2 = self.thermal_rhs(t_half, temp_k2, heater_on)
                
                # k3
                temp_k3 = {n_id: temp_k[n_id] + 0.5 * dt * dt_k2[n_id] for n_id in self.network.node_ids}
                dt_k3 = self.thermal_rhs(t_half, temp_k3, heater_on)
                
                # k4
                t_next = t + dt
                temp_k4 = {n_id: temp_k[n_id] + dt * dt_k3[n_id] for n_id in self.network.node_ids}
                dt_k4 = self.thermal_rhs(t_next, temp_k4, heater_on)
                
                # Update temperature to next step
                for n_id in self.network.node_ids:
                    temp_k[n_id] += (dt / 6.0) * (dt_k1[n_id] + 2.0 * dt_k2[n_id] + 2.0 * dt_k3[n_id] + dt_k4[n_id])
                
                # 3. Update time
                t = t_next
                
                # 4. Post-step update: update thermostat state based on ACCEPTED new battery temperature
                bat_temp_c = temp_k['battery'] - 273.15
                self.thermostat.update_state(bat_temp_c)
                
                step += 1
                
            # End of orbit calculations
            orbit_end_temp = {n_id: temp_k[n_id] for n_id in self.network.node_ids}
            orbit_end_temps.append(orbit_end_temp)
            
            # Convergence check: compare with previous orbit if we've run at least 5 orbits
            if orbit_idx >= 4: # index 4 is the 5th orbit (0, 1, 2, 3, 4)
                prev_temp = orbit_end_temps[orbit_idx - 1]
                curr_temp = orbit_end_temps[orbit_idx]
                
                # Check maximum temperature difference at end of orbit
                max_diff_c = max(abs(curr_temp[n_id] - prev_temp[n_id]) for n_id in self.network.node_ids)
                if max_diff_c < conv_threshold:
                    converged = True
                    # Let's truncate histories to only simulate up to here!
                    break
                    
        # Package and return results
        results = {
            'times_s': np.array(times),
            'temperatures_k': {n_id: np.array(temp_history[n_id]) for n_id in self.network.node_ids},
            'temperatures_c': {n_id: np.array(temp_history[n_id]) - 273.15 for n_id in self.network.node_ids},
            'heater_state': np.array(heater_state_history),
            'heater_power_w': np.array(heater_power_history),
            'internal_dissipation_w': {n_id: np.array(internal_dissipation[n_id]) for n_id in self.network.node_ids},
            'environmental_loads_w': environmental_loads,
            'space_radiation_w': {n_id: np.array(space_radiation[n_id]) for n_id in self.network.node_ids},
            'conduction_w': {n_id: np.array(conduction_flows[n_id]) for n_id in self.network.node_ids},
            'orbits_simulated': orbit_idx + 1,
            'converged': converged,
            'orbit_period_s': actual_orbit_period
        }
        
        # Add energy bookkeeping check
        results['energy_balance'] = check_energy_balance(results, self.components_df)
        
        return results

def check_energy_balance(results: dict, components_df: pd.DataFrame) -> dict:
    """
    Verifies energy conservation across the simulation.
    Saves cumulative energy in Joules for each component and for the whole network.
    
    Total energy change = Cumulative (Q_int + Q_env + Q_heater - Q_rad) dt
    (Conduction sums to zero for the entire spacecraft).
    """
    times = results['times_s']
    dt = times[1] - times[0] if len(times) > 1 else 1.0
    num_steps = len(times)
    
    nodes = list(results['temperatures_k'].keys())
    C_vals = components_df.set_index('node_id')['C_j_k'].to_dict()
    
    node_balances = {}
    
    # Net energy terms summed over the entire run
    for n_id in nodes:
        t_init = results['temperatures_k'][n_id][0]
        t_final = results['temperatures_k'][n_id][-1]
        
        dE_thermal = C_vals[n_id] * (t_final - t_init)
        
        # Integrate powers
        e_int = np.sum(results['internal_dissipation_w'][n_id]) * dt
        e_env = np.sum(results['environmental_loads_w'][n_id]['total']) * dt
        e_cond = np.sum(results['conduction_w'][n_id]) * dt
        e_rad = np.sum(results['space_radiation_w'][n_id]) * dt
        
        e_heat = 0.0
        if n_id == 'battery':
            e_heat = np.sum(results['heater_power_w']) * dt
            
        expected_dE = e_int + e_env + e_heat + e_cond - e_rad
        residual = dE_thermal - expected_dE
        
        node_balances[n_id] = {
            'dE_thermal_j': dE_thermal,
            'energy_input_internal_j': e_int,
            'energy_input_env_j': e_env,
            'energy_input_heater_j': e_heat,
            'energy_input_conduction_j': e_cond,
            'energy_output_space_radiation_j': e_rad,
            'residual_j': residual,
            'relative_error': residual / max(1.0, abs(dE_thermal))
        }
        
    # Overall vehicle balance
    total_dE_thermal = sum(b['dE_thermal_j'] for b in node_balances.values())
    total_e_int = sum(b['energy_input_internal_j'] for b in node_balances.values())
    total_e_env = sum(b['energy_input_env_j'] for b in node_balances.values())
    total_e_heat = sum(b['energy_input_heater_j'] for b in node_balances.values())
    total_e_cond = sum(b['energy_input_conduction_j'] for b in node_balances.values()) # should be zero
    total_e_rad = sum(b['energy_output_space_radiation_j'] for b in node_balances.values())
    
    total_expected = total_e_int + total_e_env + total_e_heat - total_e_rad
    total_residual = total_dE_thermal - total_expected
    
    return {
        'node_balances': node_balances,
        'overall_balance': {
            'dE_thermal_j': total_dE_thermal,
            'energy_input_internal_j': total_e_int,
            'energy_input_env_j': total_e_env,
            'energy_input_heater_j': total_e_heat,
            'energy_input_conduction_j': total_e_cond,
            'energy_output_space_radiation_j': total_e_rad,
            'residual_j': total_residual,
            'relative_error': total_residual / max(1.0, abs(total_dE_thermal))
        }
    }
