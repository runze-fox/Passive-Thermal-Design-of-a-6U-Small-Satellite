"""
Data input/output utilities for parsing CSV database tables and scenario YAML files.
"""
import os
import yaml
import pandas as pd
from .config import (
    validate_materials, 
    validate_components, 
    validate_surfaces, 
    validate_thermal_links,
    validate_environment
)

class ProjectData:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.materials_df = None
        self.components_df = None
        self.surfaces_df = None
        self.thermal_links_df = None
        self.assumptions_df = None
        self.load_base_tables()

    def load_base_tables(self):
        """Loads and validates all basic CSV datasets."""
        self.materials_df = pd.read_csv(os.path.join(self.data_dir, 'materials.csv'), encoding='utf-8')
        validate_materials(self.materials_df)

        self.components_df = pd.read_csv(os.path.join(self.data_dir, 'components.csv'), encoding='utf-8')
        validate_components(self.components_df)

        valid_nodes = set(self.components_df['node_id'])
        valid_materials = set(self.materials_df['material_id'])

        self.surfaces_df = pd.read_csv(os.path.join(self.data_dir, 'surfaces.csv'), encoding='utf-8')
        validate_surfaces(self.surfaces_df, valid_nodes, valid_materials)

        self.thermal_links_df = pd.read_csv(os.path.join(self.data_dir, 'thermal_links.csv'), encoding='utf-8')
        validate_thermal_links(self.thermal_links_df, valid_nodes)

        self.assumptions_df = pd.read_csv(os.path.join(self.data_dir, 'assumptions_register.csv'), encoding='utf-8')


    def load_scenario(self, scenario_path: str) -> dict:
        """
        Loads a scenario YAML configuration file, validates environment fields,
        and applies scenario-specific material settings.
        
        Returns a dict containing scenario details:
        - name: scenario name
        - environment: dict of parameters
        - payload_power: dict of payload active/inactive power & schedule
        - heater: heater config (power, thresholds)
        - simulation: simulation options (max_orbits, timestep, convergence, initial_temperature)
        - resolved_surfaces: DataFrame of surfaces with active alpha_s and epsilon_ir
        - resolved_components: DataFrame of components with thermal properties
        """
        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario = yaml.safe_load(f)

        # Validate scenario segments
        if 'environment' not in scenario:
            raise ValueError("Scenario file missing 'environment' section")
        validate_environment(scenario['environment'])

        # Compute orbit parameters dynamically
        from .environment import compute_orbit_parameters
        env = scenario['environment']
        period_s, sunlit_s, eclipse_s = compute_orbit_parameters(env['altitude_km'], env['beta_deg'])
        env['sunlit_duration_s'] = sunlit_s
        env['eclipse_duration_s'] = eclipse_s
        env['orbit_period_s'] = period_s

        prop_type = scenario.get('material_property_type', 'bol').lower()

        if prop_type not in ['bol', 'eol']:
            raise ValueError(f"Unknown material_property_type '{prop_type}', must be 'bol' or 'eol'")

        # Resolve optical properties based on BOL/EOL selection
        resolved_surfaces = self.surfaces_df.copy()
        
        # Merge materials to get BOL or EOL properties
        materials_lookup = self.materials_df.set_index('material_id')
        
        active_alpha = []
        active_epsilon = []
        for _, row in resolved_surfaces.iterrows():
            mat_id = row['material_id']
            if mat_id not in materials_lookup.index:
                raise ValueError(f"Material '{mat_id}' specified in surfaces not found in materials database.")
            
            mat_row = materials_lookup.loc[mat_id]
            alpha_val = mat_row['alpha_s_BOL']
            epsilon_val = mat_row['epsilon_IR']
            
            # Apply solar cell electrical efficiency offset
            # 18% of absorbed solar heat is converted to electrical power and exported
            if mat_id == 'solar_cell_assembly':
                alpha_val = max(0.0, alpha_val - 0.18)
                
            active_alpha.append(alpha_val)
            active_epsilon.append(epsilon_val)


                
        resolved_surfaces['alpha_s'] = active_alpha
        resolved_surfaces['epsilon_ir'] = active_epsilon

        # Prepare active components
        resolved_components = self.components_df.copy()
        # Compute thermal capacitance C = mass * cp
        resolved_components['C_j_k'] = resolved_components['mass_kg'] * resolved_components['cp_j_kgk']

        scenario['resolved_surfaces'] = resolved_surfaces
        scenario['resolved_components'] = resolved_components
        scenario['thermal_links'] = self.thermal_links_df.copy()
        scenario['assumptions'] = self.assumptions_df.copy()

        return scenario
