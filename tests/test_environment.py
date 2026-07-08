import pytest
import pandas as pd
from cubesat_thermal.environment import is_sunlit, compute_surface_environmental_loads

def test_is_sunlit():
    sunlit_dur = 3600.0
    ecl_dur = 2100.0
    period = sunlit_dur + ecl_dur
    
    # In sunlit period
    assert is_sunlit(0.0, sunlit_dur, ecl_dur) is True
    assert is_sunlit(1800.0, sunlit_dur, ecl_dur) is True
    assert is_sunlit(3599.0, sunlit_dur, ecl_dur) is True
    
    # In eclipse period
    assert is_sunlit(3600.0, sunlit_dur, ecl_dur) is False
    assert is_sunlit(4500.0, sunlit_dur, ecl_dur) is False
    assert is_sunlit(5699.0, sunlit_dur, ecl_dur) is False
    
    # Periodic check (second orbit)
    assert is_sunlit(period + 100.0, sunlit_dur, ecl_dur) is True
    assert is_sunlit(period + sunlit_dur + 100.0, sunlit_dur, ecl_dur) is False

def test_surface_environmental_loads():
    env = {
        'solar_flux_w_m2': 1361.0,
        'albedo': 0.3,
        'earth_ir_w_m2': 230.0,
        'space_temperature_k': 3.0,
        'sunlit_duration_s': 3600.0,
        'eclipse_duration_s': 2100.0
    }
    
    surfaces_df = pd.DataFrame([
        {
            'surface_id': 'test_surface',
            'attached_node_id': 'test_node',
            'area_m2': 0.1,
            'material_id': 'test_mat',
            'solar_exposure_factor': 1.0,
            'earth_view_factor': 0.5,
            'space_view_factor': 0.5,
            'alpha_s': 0.25,
            'epsilon_ir': 0.8
        }
    ])
    
    # Sunlit segment
    loads_sun = compute_surface_environmental_loads(1000.0, env, surfaces_df)['test_surface']
    
    # Direct Solar = alpha * solar_flux * area * f_solar = 0.25 * 1361 * 0.1 * 1.0 = 34.025 W
    assert abs(loads_sun['solar'] - 34.025) < 1e-4
    
    # Albedo = alpha * solar_flux * albedo_coeff * area * f_earth = 0.25 * 1361 * 0.3 * 0.1 * 0.5 = 5.10375 W
    assert abs(loads_sun['albedo'] - 5.10375) < 1e-4
    
    # Earth IR = epsilon * earth_ir_flux * area * f_earth = 0.8 * 230 * 0.1 * 0.5 = 9.2 W
    assert abs(loads_sun['earth_ir'] - 9.2) < 1e-4
    
    # Eclipse segment
    loads_ecl = compute_surface_environmental_loads(4000.0, env, surfaces_df)['test_surface']
    
    # Solar and Albedo must be zero in eclipse
    assert loads_ecl['solar'] == 0.0
    assert loads_ecl['albedo'] == 0.0
    
    # Earth IR must remain active in eclipse
    assert abs(loads_ecl['earth_ir'] - 9.2) < 1e-4
