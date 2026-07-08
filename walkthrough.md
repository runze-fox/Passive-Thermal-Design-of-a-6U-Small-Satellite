# Simulation Walkthrough: Passive Thermal Design of a Small Satellite (v1.5 Redesign v2)

We have built a transparent, reproducible Python preliminary thermal-analysis workflow for the **Passive Thermal Design of a Small Satellite Under a High-Beta Bounding Hot Case**. The tool uses a 6-node lumped-parameter thermal network and separates physical thermal nodes from external surface coatings and environmental exposure factors.

---

## 1. Project Scaffolding & Directory Layout

The repository is organized inside the workspace as follows:
- `data/`: Contain CSV databases (`materials.csv`, `components.csv`, `surfaces.csv`, `thermal_links.csv`, `assumptions_register.csv`) and scenario specifications under `scenarios/` (`nominal.yaml`, `hot.yaml`, `cold.yaml`, `cold_stress.yaml`).
- `src/cubesat_thermal/`: Core library package (`config.py`, `data_io.py`, `environment.py`, `controls.py`, `network.py`, `solver.py`, `analysis.py`, `plotting.py`, `validation.py`).
- `scripts/`: Execution and asset compiler scripts (`run_case.py`, `run_all_cases.py`, `run_trade_studies.py`, `build_report_assets.py`).
- `tests/`: Pytest suite verifying core components and validation test cases.
- `outputs/`: Output folder containing logs, JSON metrics, markdown reports, and plots.

---

## 2. Redesign v2 Core Solutions

To resolve extreme temperature violations in high-beta continuous-sunlight orbits without introducing complex active control or deployable mechanics, we implemented a **Passive Thermal Redesign v2**:

### 2.1 Thermal Surface Zoning
We classified all external surfaces into three distinct zones based on their role and environmental exposure:
- **Solar-Array Face** (`solar_cell_assembly` on $+Y$): Net solar absorption is offset by the $18\%$ electrical conversion efficiency ($\alpha_{\text{eff}} = \alpha_s - \eta_{\text{elec}} = 0.55$) to avoid thermal double counting.
- **General Spacecraft External Faces** (`AZ-93 Silicate` on $+X, -X, +Z, -Z$): White paint chosen for its low solar absorptance ($\alpha = 0.16$) and high infrared emittance ($\epsilon = 0.90$) to limit solar heating.
- **Dedicated Radiator Face** (`0.005″ FEP/Ag/Inconel` on $-Y$): Silver FEP tape characterized by extremely low solar absorptance ($\alpha = 0.07$) and high infrared emittance ($\epsilon = 0.79$).

### 2.2 Radiator Face Orientation Physics
In a circular 600 km dawn-dusk SSO (LTAN 06:00/18:00), the solar vector is perpendicular to the velocity direction and lies in the cross-track plane.
- The $+Y$ cross-track face is permanently **Sun-facing** (solar exposure factor $= 0.9$).
- The $-Y$ cross-track face is permanently **anti-Sun** (facing deep space, shaded, solar exposure factor $= 0.0$).
Therefore, the radiator is mounted on the **$-Y$ face** (anti-Sun cross-track face), which has the lowest integrated Sun and Earth view factors.

---

## 3. Case Simulation Results Summary

Following the implementation of Redesign v2, all standard scenarios successfully converged to **robust pass** states without requiring any active cooling or deployable radiator mechanics:

*   **Nominal Case (`nominal.yaml`, $\beta = 65^\circ$)**:
    - **Battery**: $14.8\text{ }^\circ\text{C}$ to $15.1\text{ }^\circ\text{C}$ (Limit: $-10.0\text{ }^\circ\text{C}$ to $45.0\text{ }^\circ\text{C}$ $\rightarrow$ **PASS**)
    - **Avionics**: $16.4\text{ }^\circ\text{C}$ to $17.1\text{ }^\circ\text{C}$ (Limit: $-20.0\text{ }^\circ\text{C}$ to $60.0\text{ }^\circ\text{C}$ $\rightarrow$ **PASS**)
    - **Payload**: $14.1\text{ }^\circ\text{C}$ to $17.7\text{ }^\circ\text{C}$ (Limit: $-10.0\text{ }^\circ\text{C}$ to $50.0\text{ }^\circ\text{C}$ $\rightarrow$ **PASS**)
*   **Bounding Hot Case (`hot.yaml`, $\beta = 74^\circ$, continuous sun)**:
    - **Battery**: $35.0\text{ }^\circ\text{C}$ to $35.4\text{ }^\circ\text{C}$ (Limit: $-10.0\text{ }^\circ\text{C}$ to $45.0\text{ }^\circ\text{C}$ $\rightarrow$ **PASS**)
    - **Avionics**: $38.1\text{ }^\circ\text{C}$ to $39.2\text{ }^\circ\text{C}$ (Limit: $-20.0\text{ }^\circ\text{C}$ to $60.0\text{ }^\circ\text{C}$ $\rightarrow$ **PASS**)
    - **Payload**: $34.0\text{ }^\circ\text{C}$ to $40.3\text{ }^\circ\text{C}$ (Limit: $-10.0\text{ }^\circ\text{C}$ to $50.0\text{ }^\circ\text{C}$ $\rightarrow$ **PASS**)
*   **Bounding Cold Case (`cold.yaml`, $\beta = 60^\circ$)**:
    - **Battery**: $5.0\text{ }^\circ\text{C}$ to $10.0\text{ }^\circ\text{C}$ (Limit: $-10.0\text{ }^\circ\text{C}$ to $45.0\text{ }^\circ\text{C}$ $\rightarrow$ **PASS**)
    - **Battery Heater Duty Cycle**: $36.7\%$ ($5.92\text{ Wh/orbit}$)

---

## 4. System-Level Radiator Sizing Trade-Off

To find the optimal radiator sizing, we swept the radiator area $A_{\text{rad}}$ from $0.02\text{ m}^2$ to $0.06\text{ m}^2$ across Nominal, Hot, and Cold cases:

| Radiator Area ($A_{\text{rad}}$) | Hot Case Peak Avionics Temp | Cold Case Min Battery Temp | Cold Case Heater Duty Cycle | Cold Case Heater Energy |
| :---: | :---: | :---: | :---: | :---: |
| **$0.02\text{ m}^2$** | $39.17\text{ }^\circ\text{C}$ | $5.00\text{ }^\circ\text{C}$ | $36.7\%$ | $5.92\text{ Wh/orbit}$ |
| **$0.03\text{ m}^2$** | $34.87\text{ }^\circ\text{C}$ | $5.00\text{ }^\circ\text{C}$ | $41.5\%$ | $6.69\text{ Wh/orbit}$ |
| **$0.04\text{ m}^2$** | $31.15\text{ }^\circ\text{C}$ | $5.00\text{ }^\circ\text{C}$ | $49.0\%$ | $7.90\text{ Wh/orbit}$ |
| **$0.05\text{ m}^2$** | $27.80\text{ }^\circ\text{C}$ | $5.00\text{ }^\circ\text{C}$ | $63.6\%$ | $10.26\text{ Wh/orbit}$ |
| **$0.06\text{ m}^2$** | $24.81\text{ }^\circ\text{C}$ | $4.99\text{ }^\circ\text{C}$ | $60.9\%$ | $9.81\text{ Wh/orbit}$ |

### Engineering Takeaways:
1. **Hot-Case Sizing**: Even with the smallest radiator area ($0.02\text{ m}^2$), the avionics peaks at $39.17\text{ }^\circ\text{C}$, which is well below its $60.0\text{ }^\circ\text{C}$ maximum limit.
2. **Cold-Case Sizing**: While a larger radiator (e.g., $0.05\text{ m}^2$) lowers the hot peak to $27.80\text{ }^\circ\text{C}$, it simultaneously increases the heater energy consumption per orbit by $73\%$ (from $5.92\text{ Wh}$ to $10.26\text{ Wh}$).
3. **Optimum Selection**: For a small satellite, power is typically the most constrained resource. Therefore, **$0.02\text{ m}^2$ is the optimal radiator size**, as it guarantees ample thermal margin in the hot case while minimizing the battery survival heater's power drain.

This is a classic thermal control engineering trade-off: **never size a radiator larger than necessary, as it directly increases cold-case heater power penalties.**
