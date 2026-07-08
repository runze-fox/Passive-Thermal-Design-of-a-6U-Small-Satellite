"""
Configuration validation rules, physical limits, and schema definitions.
"""
import pandas as pd
import numpy as np

def validate_materials(df: pd.DataFrame):
    """
    Validates materials.csv data:
    - alpha_s_BOL and epsilon_IR must be between 0 and 1
    """
    required_cols = ['material_id', 'intended_role', 'alpha_s_BOL', 'epsilon_IR', 'source_table', 'source_url', 'concise_notes']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in materials: {col}")
            
    # Check optical properties are in range [0, 1]
    for col in ['alpha_s_BOL', 'epsilon_IR']:
        if not df[col].between(0.0, 1.0).all():
            invalid = df[~df[col].between(0.0, 1.0)]
            raise ValueError(f"Optical properties in column '{col}' must be between 0 and 1. Invalid rows:\n{invalid}")


def validate_components(df: pd.DataFrame):
    """
    Validates components.csv data:
    - mass_kg and cp_j_kgk must be strictly positive
    - temperature_min_c < temperature_max_c
    """
    required_cols = ['node_id', 'mass_kg', 'cp_j_kgk', 'temperature_min_c', 'temperature_max_c']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in components: {col}")
            
    if not (df['mass_kg'] > 0).all():
        invalid = df[df['mass_kg'] <= 0]
        raise ValueError(f"Masses must be positive. Invalid rows:\n{invalid}")
        
    if not (df['cp_j_kgk'] > 0).all():
        invalid = df[df['cp_j_kgk'] <= 0]
        raise ValueError(f"Specific heats must be positive. Invalid rows:\n{invalid}")
        
    if not (df['temperature_min_c'] < df['temperature_max_c']).all():
        invalid = df[df['temperature_min_c'] >= df['temperature_max_c']]
        raise ValueError(f"Min temperature limit must be less than max temperature limit. Invalid rows:\n{invalid}")

def validate_surfaces(df: pd.DataFrame, valid_node_ids: set, valid_material_ids: set):
    """
    Validates surfaces.csv data:
    - attached_node_id must be in components
    - material_id must be in materials
    - area_m2 must be positive
    - view factors / exposure factors must be non-negative
    """
    required_cols = ['surface_id', 'attached_node_id', 'area_m2', 'material_id', 
                     'solar_exposure_factor', 'earth_view_factor', 'space_view_factor']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in surfaces: {col}")
            
    if not (df['area_m2'] > 0).all():
        invalid = df[df['area_m2'] <= 0]
        raise ValueError(f"Surface areas must be positive. Invalid rows:\n{invalid}")
        
    # Check linked keys
    for node_id in df['attached_node_id']:
        if node_id not in valid_node_ids:
            raise ValueError(f"Surface attached_node_id '{node_id}' not found in components.")
            
    for mat_id in df['material_id']:
        if mat_id not in valid_material_ids:
            raise ValueError(f"Surface material_id '{mat_id}' not found in materials.")
            
    # Check non-negative factor rules
    for col in ['solar_exposure_factor', 'earth_view_factor', 'space_view_factor']:
        if not (df[col] >= 0.0).all():
            invalid = df[df[col] < 0.0]
            raise ValueError(f"Exposure/view factor in column '{col}' cannot be negative. Invalid rows:\n{invalid}")

def validate_thermal_links(df: pd.DataFrame, valid_node_ids: set):
    """
    Validates thermal_links.csv:
    - node_i and node_j must be valid components
    - conductance_w_k must be non-negative
    """
    required_cols = ['node_i', 'node_j', 'conductance_w_k']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in thermal links: {col}")
            
    for col in ['node_i', 'node_j']:
        for val in df[col]:
            if val not in valid_node_ids:
                raise ValueError(f"Thermal link node '{val}' not found in components.")
                
    if not (df['conductance_w_k'] >= 0.0).all():
        invalid = df[df['conductance_w_k'] < 0.0]
        raise ValueError(f"Conductances must be non-negative. Invalid rows:\n{invalid}")

def validate_environment(env: dict):
    """
    Validates environmental parameters from scenario file.
    """
    required_keys = ['solar_flux_w_m2', 'albedo', 'earth_ir_w_m2', 'space_temperature_k', 
                     'altitude_km', 'beta_deg']
    for key in required_keys:
        if key not in env:
            raise ValueError(f"Missing environmental setting in scenario: {key}")
            
    if env['solar_flux_w_m2'] < 0:
        raise ValueError("Solar flux cannot be negative")
    if not (0 <= env['albedo'] <= 1):
        raise ValueError("Albedo coefficient must be between 0 and 1")
    if env['earth_ir_w_m2'] < 0:
        raise ValueError("Earth IR flux cannot be negative")
    if env['space_temperature_k'] < 0:
        raise ValueError("Space temperature cannot be negative")
    if env['altitude_km'] <= 0:
        raise ValueError("Altitude must be positive")
    if not (-90.0 <= env['beta_deg'] <= 90.0):
        raise ValueError("Beta angle must be between -90 and 90 degrees")

    # Optional metadata validation
    if 'orbit_type' in env:
        if env['orbit_type'] not in ['dawn_dusk_sso', 'generic_leo']:
            raise ValueError(f"Unknown orbit_type: {env['orbit_type']}")
    if 'ltan' in env:
        if not isinstance(env['ltan'], str):
            raise ValueError("LTAN must be a string (e.g. '06:00')")


