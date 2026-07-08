"""
Plotting and visualization functions for thermal analysis results.
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Consistent color palette for nodes
NODE_COLORS = {
    'battery': '#ff7f0e',        # Orange
    'avionics': '#1f77b4',       # Blue
    'payload': '#9467bd',        # Purple
    'structure': '#7f7f7f',      # Grey
    'radiator': '#2ca02c',       # Green
    'external_shell': '#8c564b'  # Brown
}

# Color-coding for design-margin status
STATUS_COLORS = {
    'FAIL': '#d62728',                         # Red
    'marginal pass': '#ff7f0e',                 # Orange
    'acceptable preliminary pass': '#bcbd22',   # Gold-yellow
    'robust pass': '#2ca02c'                    # Green
}

def setup_plot_style():
    """Applies a clean, modern style for figures."""
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9
    plt.rcParams['figure.titlesize'] = 14
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['grid.linestyle'] = '--'

def plot_temperature_history(results: dict, comp_limits: pd.DataFrame, env_cfg: dict, out_dir: str):
    """
    Plots the temperature history of all nodes in °C.
    Highlights eclipse periods, heater ON periods, and component limits.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    
    times_min = results['times_s'] / 60.0 # convert to minutes
    period_min = results['orbit_period_s'] / 60.0
    
    # Identify sunlit / eclipse cycles
    sun_dur_min = env_cfg['sunlit_duration_s'] / 60.0
    ecl_dur_min = env_cfg['eclipse_duration_s'] / 60.0
    orbit_min = sun_dur_min + ecl_dur_min
    
    # Shade eclipse regions
    num_orbits = int(np.ceil(times_min[-1] / orbit_min)) if len(times_min) > 0 else 0
    for o in range(num_orbits):
        ecl_start = o * orbit_min + sun_dur_min
        ecl_end = (o + 1) * orbit_min
        ax.axvspan(ecl_start, ecl_end, color='gray', alpha=0.15, label='Eclipse' if o == 0 else "")
        
    # Shade battery heater ON regions
    heater_state = results['heater_state']
    heater_on_indices = np.where(heater_state == 1)[0]
    if len(heater_on_indices) > 0:
        ranges = np.split(heater_on_indices, np.where(np.diff(heater_on_indices) > 1)[0] + 1)
        for idx, r in enumerate(ranges):
            if len(r) > 0:
                ax.axvspan(times_min[r[0]], times_min[r[-1]], color='red', alpha=0.08, label='Heater ON' if idx == 0 else "")
                
    # Plot node temperatures
    limits = comp_limits.set_index('node_id')
    for n_id, temps in results['temperatures_c'].items():
        color = NODE_COLORS.get(n_id, '#333333')
        ax.plot(times_min, temps, label=n_id, color=color, linewidth=1.5)
        
        limit_min = limits.loc[n_id, 'temperature_min_c']
        limit_max = limits.loc[n_id, 'temperature_max_c']
        
        ax.axhline(limit_max, color=color, linestyle='--', alpha=0.4, linewidth=0.8)
        ax.axhline(limit_min, color=color, linestyle='--', alpha=0.4, linewidth=0.8)
        
    ax.set_xlabel('Time [minutes]')
    ax.set_ylabel('Temperature [°C]')
    ax.set_title('Satellite Node Temperature History')
    ax.grid(True)
    
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right', bbox_to_anchor=(1.15, 1.0))
    
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'temperature_history.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'temperature_history.svg'), bbox_inches='tight')
    plt.close()

def plot_heat_load_timeline(results: dict, env_cfg: dict, out_dir: str):
    """
    Plots the environmental and internal heat input timelines for the final orbit.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    
    times = results['times_s']
    period = results['orbit_period_s']
    t_final = times[-1]
    
    mask = times >= (t_final - period - 0.1)
    t_plot = (times[mask] - (t_final - period)) / 60.0
    
    tot_solar = np.zeros_like(times[mask])
    tot_albedo = np.zeros_like(times[mask])
    tot_earth_ir = np.zeros_like(times[mask])
    tot_int = np.zeros_like(times[mask])
    tot_heater = results['heater_power_w'][mask]
    
    for n_id in results['temperatures_k'].keys():
        env = results['environmental_loads_w'][n_id]
        tot_solar += np.array(env['solar'])[mask]
        tot_albedo += np.array(env['albedo'])[mask]
        tot_earth_ir += np.array(env['earth_ir'])[mask]
        tot_int += np.array(results['internal_dissipation_w'][n_id])[mask]
        
    ax.plot(t_plot, tot_solar, label='Direct Solar', color='#ffcd56', linewidth=1.5)
    ax.plot(t_plot, tot_albedo, label='Albedo', color='#4bc0c0', linewidth=1.5)
    ax.plot(t_plot, tot_earth_ir, label='Earth IR', color='#9966ff', linewidth=1.5)
    ax.plot(t_plot, tot_int, label='Internal Dissipation', color='#ff6384', linewidth=1.5)
    
    if np.max(tot_heater) > 0:
        ax.plot(t_plot, tot_heater, label='Battery Heater', color='#ff4d4d', linewidth=1.5)
        
    tot_input = tot_solar + tot_albedo + tot_earth_ir + tot_int + tot_heater
    ax.plot(t_plot, tot_input, label='Total Input', color='black', linestyle=':', linewidth=2.0)
    
    sun_dur_min = env_cfg['sunlit_duration_s'] / 60.0
    orbit_dur_min = period / 60.0
    if sun_dur_min < orbit_dur_min:
        ax.axvspan(sun_dur_min, orbit_dur_min, color='gray', alpha=0.15, label='Eclipse')
        
    ax.set_xlabel('Orbit Time [minutes]')
    ax.set_ylabel('Heat Load [W]')
    ax.set_title('Spacecraft Heat Load Timeline (Steady-State Orbit)')
    ax.grid(True)
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.0))
    
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'heat_loads_timeline.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'heat_loads_timeline.svg'), bbox_inches='tight')
    plt.close()

def plot_temperature_margins(margins: dict, out_dir: str):
    """
    Generates a horizontal bar chart displaying prediction ranges and limits.
    """
    setup_plot_style()
    
    nodes = [n for n in margins.keys() if n not in ['heater', 'overall_status']]
    
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    
    y_pos = np.arange(len(nodes))
    
    for idx, n_id in enumerate(nodes):
        m = margins[n_id]
        color = NODE_COLORS.get(n_id, '#333333')
        
        # Draw limits bar
        ax.barh(idx, m['max_limit_c'] - m['min_limit_c'], left=m['min_limit_c'], 
                color=color, alpha=0.12, edgecolor=color, height=0.5, linestyle='--')
        
        # Draw prediction range bar
        ax.barh(idx, m['max_predicted_c'] - m['min_predicted_c'], left=m['min_predicted_c'], 
                color=color, alpha=0.8, edgecolor=color, height=0.3)
        
        # 4-tier colored status note
        color_status = STATUS_COLORS.get(m['status'], 'black')
        status_text = f"  ({m['status']} | LM: {m['lower_margin_c']:.1f}°C, UM: {m['upper_margin_c']:.1f}°C)"
        ax.text(m['max_limit_c'] + 1.5, idx, status_text, va='center', fontsize=8, fontweight='bold',
                color=color_status)
        
    ax.set_yticks(y_pos)
    ax.set_yticklabels(nodes)
    ax.set_xlabel('Temperature [°C]')
    ax.set_title('Satellite Nodes Peak Temperature vs Operating Limits')
    ax.grid(True, axis='x')
    
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'temperature_margins.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'temperature_margins.svg'), bbox_inches='tight')
    plt.close()

def plot_radiator_area_trade(trade_df: pd.DataFrame, limit_max_c: float, out_dir: str):
    """
    Plots the radiator area trade study.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    
    ax.plot(trade_df['radiator_area_m2'], trade_df['peak_avionics_temp_c'], 
            'o-', label='Peak Avionics Temp', color=NODE_COLORS['avionics'])
    ax.plot(trade_df['radiator_area_m2'], trade_df['peak_structure_temp_c'], 
            's-', label='Peak Structure Temp', color=NODE_COLORS['structure'])
    ax.plot(trade_df['radiator_area_m2'], trade_df['peak_radiator_temp_c'], 
            'd-', label='Peak Radiator Temp', color=NODE_COLORS['radiator'])
    
    ax.axhline(limit_max_c, color='red', linestyle='--', label='Avionics Hot Limit (60 °C)', linewidth=1.2)
    
    ax.set_xlabel('Radiator Area [m²]')
    ax.set_ylabel('Peak Hot-Case Temperature [°C]')
    ax.set_title('Radiator Area Sizing Trade Study (Hot Case)')
    ax.grid(True)
    ax.legend()
    
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'trade_radiator_area.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'trade_radiator_area.svg'), bbox_inches='tight')
    plt.close()

def plot_radiator_system_trade(trade_df: pd.DataFrame, limit_max_c: float, limit_min_c: float, out_dir: str):
    """
    Plots the dual-axis trade-off of radiator area sizing:
    - Left Axis (Red): Hot Case peak avionics temperature (limit 60°C)
    - Right Axis (Blue): Cold Case min battery temperature (limit -10°C)
    """
    setup_plot_style()
    fig, ax1 = plt.subplots(figsize=(7, 4.5), dpi=150)
    
    color1 = 'tab:red'
    ax1.set_xlabel('Radiator Area ($A_{rad}$ [m$^2$])')
    ax1.set_ylabel('Hot Case Peak Avionics Temp [°C]', color=color1)
    line1 = ax1.plot(trade_df['radiator_area_m2'], trade_df['hot_peak_avionics_c'], 
                     'o-', color=color1, label='Peak Avionics (Hot Case)')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.axhline(limit_max_c, color='red', linestyle='--', alpha=0.7, linewidth=1.2,
               label=f'Avionics Hot Limit ({limit_max_c}°C)')
    
    ax2 = ax1.twinx()
    color2 = 'tab:blue'
    ax2.set_ylabel('Cold Case Min Battery Temp [°C]', color=color2)
    line2 = ax2.plot(trade_df['radiator_area_m2'], trade_df['cold_min_battery_c'], 
                     's--', color=color2, label='Min Battery (Cold Case)')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.axhline(limit_min_c, color='blue', linestyle='-.', alpha=0.7, linewidth=1.2,
               label=f'Battery Cold Limit ({limit_min_c}°C)')
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
    
    plt.title('Radiator Area Trade-Off: Hot vs. Cold Performance')
    ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'radiator_area_system_trade.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'radiator_area_system_trade.svg'), bbox_inches='tight')
    plt.close()


def plot_heater_power_trade(trade_df: pd.DataFrame, limit_min_c: float, out_dir: str):
    """
    Plots the battery heater power trade study.
    """
    setup_plot_style()
    fig, ax1 = plt.subplots(figsize=(7, 4.5), dpi=150)
    
    color_temp = NODE_COLORS['battery']
    ax1.plot(trade_df['heater_power_w'], trade_df['min_battery_temp_c'], 
             'o-', color=color_temp, label='Min Battery Temp')
    ax1.axhline(limit_min_c, color='red', linestyle='--', label='Battery Cold Limit (-10 °C)', linewidth=1.2)
    
    ax1.set_xlabel('Heater Power [W]')
    ax1.set_ylabel('Min Cold-Case Temperature [°C]', color=color_temp)
    ax1.tick_params(axis='y', labelcolor=color_temp)
    ax1.grid(True)
    
    ax2 = ax1.twinx()
    color_dc = '#2ca02c'
    ax2.plot(trade_df['heater_power_w'], trade_df['heater_duty_cycle'] * 100, 
             's--', color=color_dc, label='Heater Duty Cycle')
    ax2.set_ylabel('Heater Duty Cycle [%]', color=color_dc)
    ax2.tick_params(axis='y', labelcolor=color_dc)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.title('Survival Heater Power Sizing Trade Study (Cold Case)')
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'trade_heater_power.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'trade_heater_power.svg'), bbox_inches='tight')
    plt.close()

def plot_material_candidates(materials_df: pd.DataFrame, selected_rad_mat: str, selected_shell_mat: str, out_dir: str):
    """
    Plots candidate materials on an alpha_s vs epsilon_ir chart.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=150)
    
    for idx, row in materials_df.iterrows():
        # Plot a single scatter point for each material
        ax.scatter(row['alpha_s_BOL'], row['epsilon_IR'], marker='o', s=100,
                   label=f"{row['material_id']} (NASA SmallSat)")
        
        # Add labels to points
        ax.annotate(row['material_id'], (row['alpha_s_BOL'] + 0.02, row['epsilon_IR'] - 0.02), fontsize=8, weight='bold')
        
    ax.set_xlabel('Solar Absorptivity ($\\alpha_s$)')
    ax.set_ylabel('IR Emissivity ($\\epsilon_{IR}$)')
    ax.set_title('Coating Surface Property Candidates (NASA SmallSat)')
    
    # Annotate key design zones
    ax.text(0.02, 0.90, 'Radiator Zone\n(Low $\\alpha$, High $\\epsilon$)', 
            fontsize=8, color='green', bbox=dict(facecolor='green', alpha=0.08, boxstyle='round'))
    ax.text(0.02, 0.10, 'Insulation Zone\n(Low $\\alpha$, Low $\\epsilon$)', 
            fontsize=8, color='blue', bbox=dict(facecolor='blue', alpha=0.08, boxstyle='round'))
    ax.text(0.70, 0.90, 'Absorber Zone\n(High $\\alpha$, High $\\epsilon$)', 
            fontsize=8, color='orange', bbox=dict(facecolor='orange', alpha=0.08, boxstyle='round'))
    
    ax.grid(True)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    
    plt.legend(loc='lower right')
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'material_property_trade.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'material_property_trade.svg'), bbox_inches='tight')
    plt.close()


def plot_strap_conductance_trade(trade_df: pd.DataFrame, out_dir: str):
    """
    Plots the strap conductance trade study.
    """
    setup_plot_style()
    fig, ax1 = plt.subplots(figsize=(7, 4.5), dpi=150)
    
    color_temp = NODE_COLORS['avionics']
    ax1.plot(trade_df['strap_conductance_w_k'], trade_df['peak_avionics_temp_c'], 
             'o-', color=color_temp, label='Peak Avionics Temp')
    ax1.set_xlabel('Thermal Strap Conductance [W/K]')
    ax1.set_ylabel('Peak Avionics Temperature [°C]', color=color_temp)
    ax1.tick_params(axis='y', labelcolor=color_temp)
    ax1.grid(True)
    
    ax2 = ax1.twinx()
    color_drop = '#e377c2'
    ax2.plot(trade_df['strap_conductance_w_k'], trade_df['temp_drop_avionics_to_rad_c'], 
             's--', color=color_drop, label='Strap Temp Drop')
    ax2.set_ylabel('Temperature Drop Avionics-to-Radiator [°C]', color=color_drop)
    ax2.tick_params(axis='y', labelcolor=color_drop)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.title('Avionics Thermal Strap Conductance Trade Study (Hot Case)')
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'trade_strap_conductance.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'trade_strap_conductance.svg'), bbox_inches='tight')
    plt.close()

def plot_battery_isolation_trade(trade_df: pd.DataFrame, limit_min_c: float, limit_max_c: float, out_dir: str):
    """
    Plots the battery isolation sweep trade study.
    Shows hot peak battery, cold min battery, and battery heater Wh/orbit.
    """
    setup_plot_style()
    fig, ax1 = plt.subplots(figsize=(7, 4.5), dpi=150)
    
    x = trade_df['battery_structure_conductance_w_k']
    
    # Left Axis: Temperatures
    ax1.plot(x, trade_df['hot_battery_peak_c'], 'ro-', label='Hot Battery Peak')
    ax1.plot(x, trade_df['cold_battery_min_c'], 'bo-', label='Cold Battery Minimum')
    
    ax1.axhline(limit_max_c, color='red', linestyle='--', label='Battery Hot Limit (45 °C)', alpha=0.5, linewidth=1.0)
    ax1.axhline(limit_min_c, color='blue', linestyle='--', label='Battery Cold Limit (-10 °C)', alpha=0.5, linewidth=1.0)
    
    ax1.set_xlabel('Battery-to-Structure Conductance G [W/K]')
    ax1.set_ylabel('Battery Temperature [°C]', color='black')
    ax1.grid(True)
    
    # Right Axis: Heater energy in Wh
    ax2 = ax1.twinx()
    color_energy = 'purple'
    ax2.plot(x, trade_df['heater_energy_wh'], 's--', color=color_energy, label='Heater Energy (Cold Case)')
    ax2.set_ylabel('Survival Heater Energy [Wh/orbit]', color=color_energy)
    ax2.tick_params(axis='y', labelcolor=color_energy)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center right')
    
    plt.title('Battery Isolation Trade Study (Hot Case vs Cold Case)')
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'trade_battery_isolation.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'trade_battery_isolation.svg'), bbox_inches='tight')
    plt.close()

def plot_payload_radiator_trade(trade_df: pd.DataFrame, limit_max_c: float, out_dir: str):
    """
    Plots the payload-to-radiator sweep.
    """
    setup_plot_style()
    fig, ax = plt.subplots(figsize=(7, 4.5), dpi=150)
    
    x = trade_df['payload_radiator_conductance_w_k']
    
    ax.plot(x, trade_df['peak_payload_temp_c'], 'o-', color=NODE_COLORS['payload'], label='Peak Payload Temp')
    ax.plot(x, trade_df['peak_radiator_temp_c'], 's-', color=NODE_COLORS['radiator'], label='Peak Radiator Temp')
    
    ax.axhline(limit_max_c, color='red', linestyle='--', label='Payload Hot Limit (50 °C)', linewidth=1.2)
    
    ax.set_xlabel('Payload-to-Radiator Equivalent Conductance [W/K]')
    ax.set_ylabel('Peak Hot-Case Temperature [°C]')
    ax.set_title('Payload-to-Radiator Conductive Strap Sweep (Hot Case)')
    ax.grid(True)
    ax.legend()
    
    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    plt.savefig(os.path.join(out_dir, 'trade_payload_radiator.png'), bbox_inches='tight')
    plt.savefig(os.path.join(out_dir, 'trade_payload_radiator.svg'), bbox_inches='tight')
    plt.close()
