"""
Orbit schedule and environmental heat load calculations (solar, albedo, Earth IR).
"""
import numpy as np
import pandas as pd

def compute_orbit_parameters(altitude_km: float, beta_deg: float) -> tuple:
    """
    Computes orbit period, sunlit duration, and eclipse duration in seconds
    for a circular orbit around Earth using two-body mechanics and cylindrical shadow.
    
    Returns:
        tuple: (orbit_period_s, sunlit_duration_s, eclipse_duration_s)
    """
    R_E = 6378.137  # Earth radius in km
    mu = 3.986004418e5  # Earth gravitational parameter in km^3/s^2
    
    r = R_E + altitude_km  # Orbit radius in km
    
    # 1. Two-body circular orbit period: P = 2 * pi * sqrt(r^3 / mu)
    period_s = 2.0 * np.pi * np.sqrt(r**3 / mu)
    
    # 2. Eclipse duration calculation
    beta_rad = np.radians(beta_deg)
    
    # Critical beta angle where the orbit remains in continuous sunlight:
    # beta_crit = arcsin(R_E / r)
    sin_beta_crit = R_E / r
    if np.abs(beta_rad) >= np.arcsin(sin_beta_crit):
        eclipse_duration_s = 0.0
    else:
        # Cylindrical shadow angular width:
        # cos(Delta_theta_ecl / 2) = sqrt(r^2 - R_E^2) / (r * cos(beta))
        num = np.sqrt(r**2 - R_E**2)
        den = r * np.cos(beta_rad)
        val = num / den
        val = np.clip(val, -1.0, 1.0)
        
        delta_theta_ecl = 2.0 * np.arccos(val)
        eclipse_duration_s = (delta_theta_ecl / (2.0 * np.pi)) * period_s
        
    sunlit_duration_s = period_s - eclipse_duration_s
    
    return float(period_s), float(sunlit_duration_s), float(eclipse_duration_s)

def is_sunlit(t: float, sunlit_duration: float, eclipse_duration: float) -> bool:
    """
    Returns True if the satellite is in the sunlit portion of the orbit.
    Uses a simple square-wave schedule.
    """
    period = sunlit_duration + eclipse_duration
    t_orbit = t % period
    return t_orbit < sunlit_duration


def compute_surface_environmental_loads(t: float, env: dict, surfaces) -> dict:
    """
    Computes environmental heat inputs (Solar, Albedo, Earth IR) in Watts for each surface at time t.
    Supports both pandas DataFrame and pre-converted list of dicts (for performance).
    
    Returns:
        dict: mapping surface_id to dict of {'solar', 'albedo', 'earth_ir', 'total'}
    """
    sunlit = is_sunlit(t, env['sunlit_duration_s'], env['eclipse_duration_s'])
    f_sun = 1.0 if sunlit else 0.0
    
    solar_flux = env['solar_flux_w_m2']
    albedo_coeff = env['albedo']
    earth_ir_flux = env['earth_ir_w_m2']
    
    surfaces_list = surfaces.to_dict(orient='records') if isinstance(surfaces, pd.DataFrame) else surfaces
    
    loads = {}
    for row in surfaces_list:
        surf_id = row['surface_id']
        area = row['area_m2']
        alpha = row['alpha_s']
        epsilon = row['epsilon_ir']
        
        f_solar = row['solar_exposure_factor']
        f_earth = row['earth_view_factor']
        
        # Solar heat load
        q_solar = alpha * solar_flux * area * f_solar * f_sun
        
        # Albedo heat load
        q_albedo = alpha * solar_flux * albedo_coeff * area * f_earth * f_sun
        
        # Earth IR heat load (remains active in eclipse)
        q_earth_ir = epsilon * earth_ir_flux * area * f_earth
        
        loads[surf_id] = {
            'solar': q_solar,
            'albedo': q_albedo,
            'earth_ir': q_earth_ir,
            'total': q_solar + q_albedo + q_earth_ir
        }
        
    return loads

def compute_node_environmental_loads(t: float, env: dict, surfaces) -> dict:
    """
    Sum the environmental loads from all surfaces attached to each thermal node.
    Supports both pandas DataFrame and pre-converted list of dicts.
    
    Returns:
        dict: mapping node_id to dict of {'solar', 'albedo', 'earth_ir', 'total'}
    """
    surfaces_list = surfaces.to_dict(orient='records') if isinstance(surfaces, pd.DataFrame) else surfaces
    surf_loads = compute_surface_environmental_loads(t, env, surfaces_list)
    
    node_loads = {}
    for row in surfaces_list:
        node_id = row['attached_node_id']
        surf_id = row['surface_id']
        s_load = surf_loads[surf_id]
        
        if node_id not in node_loads:
            node_loads[node_id] = {'solar': 0.0, 'albedo': 0.0, 'earth_ir': 0.0, 'total': 0.0}
            
        node_loads[node_id]['solar'] += s_load['solar']
        node_loads[node_id]['albedo'] += s_load['albedo']
        node_loads[node_id]['earth_ir'] += s_load['earth_ir']
        node_loads[node_id]['total'] += s_load['total']
        
    return node_loads
