"""
Thermal network representations, conductive coupling, and radiation exchange.
"""
import numpy as np
import pandas as pd

SIGMA = 5.670374419e-8 # Stefan-Boltzmann constant [W / (m2 K4)]

class ThermalNetwork:
    def __init__(self, components_df: pd.DataFrame, links_df: pd.DataFrame, surfaces_df: pd.DataFrame):
        """
        Initializes the thermal network.
        components_df: resolved components table (contains node_id, C_j_k, limits, etc.)
        links_df: thermal links table (contains node_i, node_j, conductance_w_k)
        surfaces_df: resolved surfaces table (contains surface_id, attached_node_id, area_m2, material_id, etc.)
        """
        self.node_ids = list(components_df['node_id'])
        self.nodes = components_df.set_index('node_id').to_dict(orient='index')
        self.surfaces_df = surfaces_df
        # Pre-convert surfaces to a list of dicts for maximum loop performance
        self.surfaces_list = surfaces_df.to_dict(orient='records')
        
        # Build conductance dictionary
        self.conductance = {n_id: {other_id: 0.0 for other_id in self.node_ids} for n_id in self.node_ids}
        for _, row in links_df.iterrows():
            ni, nj = row['node_i'], row['node_j']
            g = row['conductance_w_k']
            if ni in self.conductance and nj in self.conductance:
                self.conductance[ni][nj] = g
                self.conductance[nj][ni] = g

    def compute_conduction_flows(self, temp_k: dict) -> dict:
        """
        Computes the net conductive heat input to each node.
        Q_cond_i = sum_j G_ij * (T_j - T_i)
        
        Returns:
            dict: mapping node_id to net conductive power in Watts.
        """
        cond_flows = {n_id: 0.0 for n_id in self.node_ids}
        for i in self.node_ids:
            for j in self.node_ids:
                if i == j:
                    continue
                g_ij = self.conductance[i][j]
                if g_ij > 0:
                    flow = g_ij * (temp_k[j] - temp_k[i])
                    cond_flows[i] += flow
        return cond_flows

    def compute_space_radiation_flows(self, temp_k: dict, space_temp_k: float) -> dict:
        """
        Computes the radiation heat loss from all surfaces to deep space.
        Q_rad_space_s = epsilon_s * sigma * A_s * F_s_space * (T_node^4 - T_space^4)
        
        Returns:
            dict: mapping node_id to net radiation power loss to space (positive means loss, i.e. heat leaving)
        """
        rad_losses = {n_id: 0.0 for n_id in self.node_ids}
        
        space_temp_k4 = space_temp_k ** 4
        
        for row in self.surfaces_list:
            node_id = row['attached_node_id']
            area = row['area_m2']
            epsilon = row['epsilon_ir']
            f_space = row['space_view_factor']
            
            node_temp = temp_k[node_id]
            if node_temp <= 0.0:
                raise ValueError(f"Physical violation: Node {node_id} temperature is {node_temp} K (<= 0 K).")
                
            q_rad = epsilon * SIGMA * area * f_space * (node_temp**4 - space_temp_k4)
            rad_losses[node_id] += q_rad
            
        return rad_losses
