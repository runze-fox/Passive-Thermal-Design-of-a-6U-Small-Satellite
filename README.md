# Passive Thermal Design of a Small Satellite Under a High-Beta Bounding Hot Case

This repository contains a transparent, reproducible Python thermal-analysis workflow for a **passive thermal design and radiator sizing trade study** of a 6U Small Satellite in a circular 600 km dawn-dusk Sun-Synchronous Orbit (SSO).

> [!IMPORTANT]
> **Engineering Status Disclaimer:**
> This model is **not** flight-qualified and does not serve as a substitute for detailed thermal analysis tools like Thermal Desktop / SINDA-FLUINT. It is a preliminary design verification concept and **requires future correlation with detailed geometric models and TVAC / thermal-balance test data** before flight qualification.
>
> In this version (v1.5):
> 1. Earth and space view factors are **simplified effective exposure factors**, not CAD-derived configuration factors.
> 2. Attitude dynamics are represented through a **scenario-defined effective exposure abstraction** rather than detailed rigid-body dynamics.

---

## 1. Passive Redesign v2 Architecture

To resolve extreme temperature violations in high-beta continuous-sunlight orbits without introducing complex active control or deployable mechanics (such as loop heat pipes or phase-change materials), we implemented a **Passive Thermal Redesign v2**:

### A. Thermal Surface Zoning
We classified all external surfaces into three distinct zones based on their role and environmental exposure:
- **Solar-Array Face** (`solar_cell_assembly` on $+Y$): High-absorptance, high-emissivity solar cells. Net solar absorption is offset by the $18\%$ electrical conversion efficiency ($\alpha_{\text{eff}} = \alpha_s - \eta_{\text{elec}} = 0.55$) to avoid thermal double counting.
- **General Spacecraft External Faces** (`AZ-93 Silicate` on $+X, -X, +Z, -Z$): White paint chosen for its low solar absorptance ($\alpha = 0.16$) and high infrared emittance ($\epsilon = 0.90$) to limit solar heating.
- **Dedicated Radiator Face** (`0.005″ FEP/Ag/Inconel` on $-Y$): Silver FEP tape characterized by extremely low solar absorptance ($\alpha = 0.07$) and high infrared emittance ($\epsilon = 0.79$).

### B. Radiator Face Orientation Physics
In a circular 600 km dawn-dusk SSO (LTAN 06:00/18:00), the solar vector is perpendicular to the velocity direction and lies in the cross-track plane.
- The $+Y$ cross-track face is permanently **Sun-facing** (solar exposure factor $= 0.9$).
- The $-Y$ cross-track face is permanently **anti-Sun** (facing deep space, shaded, solar exposure factor $= 0.0$).
Therefore, the radiator is mounted on the **$-Y$ face** (anti-Sun cross-track face), which has the lowest integrated Sun and Earth view factors.

---

## 2. Repository Structure

```text
cubesat_thermal/
├── README.md
├── pyproject.toml
├── requirements.txt
├── data/
│   ├── materials.csv             # Coatings property catalog (alpha_s, epsilon_ir)
│   ├── components.csv            # Thermal node limits, mass, specific heats
│   ├── surfaces.csv              # Outer face mappings and exposure factors
│   ├── thermal_links.csv         # Conductive couplings
│   ├── assumptions_register.csv  # Verification and provenance audit trail
│   └── scenarios/
│       ├── nominal.yaml          # Nominal mission case (65 deg beta)
│       ├── hot.yaml              # Bounding hot case (74 deg beta, continuous sun)
│       ├── cold.yaml             # Bounding cold case (60 deg beta)
│       └── cold_stress.yaml      # Cold stress case with active heater cycling
├── src/
│   └── cubesat_thermal/
│       ├── __init__.py
│       ├── config.py             # Bounds validation and schema checks
│       ├── data_io.py            # Scenario and CSV parser with solar cell offset
│       ├── environment.py        # Solar/Albedo/Earth IR heat loads & orbit parameters
│       ├── network.py            # Conductive and space radiation exchange
│       ├── controls.py           # Thermostat hysteresis logic
│       ├── solver.py             # Fixed-step RK4 solver with convergence check
│       ├── analysis.py           # Trade studies and temperature margin calculations
│       ├── plotting.py           # Matplotlib figures generation
│       └── validation.py         # Verification tests
├── scripts/
│   ├── run_case.py               # Runs a single scenario
│   ├── run_all_cases.py          # Runs all scenarios
│   ├── run_trade_studies.py      # Sweeps parameters (area, heater, strap, materials, battery isolation)
│   └── build_report_assets.py    # Generates final markdown summary reports
└── tests/                        # Pytest suite
```

---

## 3. Setup and Installation

### Prerequisites
- Python >= 3.8
- `numpy`, `pandas`, `scipy`, `pyyaml`, `matplotlib`, `pytest`

### Installation
Clone this repository and install it in editable mode:
```bash
pip install -e .
```

---

## 4. Run Commands

### 1. Running a Single Case
Run a specific scenario configuration file (e.g., nominal):
```bash
python scripts/run_case.py --scenario data/scenarios/nominal.yaml
```
This generates temperature histories, heat-load timelines, and margin tables inside `outputs/nominal/`.

### 2. Running All Cases
Run all standard cases:
```bash
python scripts/run_all_cases.py
```
This outputs results for the scenarios under `outputs/nominal/`, `outputs/bounding_hot/`, `outputs/bounding_cold/`, and `outputs/cold_stress/`.

### 3. Running Trade Studies
Run the parametric trade sweeps for radiator area, battery heater power, radiator materials, thermal-strap conductance, and battery isolation:
```bash
python scripts/run_trade_studies.py
```
Outputs are written as CSV tables and PNG/SVG figures to `outputs/trades/`.

### 4. Build Consolidated Summary Report
Combine all scenario runs and trade sweeps into a single Markdown summary report:
```bash
python scripts/build_report_assets.py
```
This creates `outputs/summary_report.md`.

---

## 5. Verification and Unit Tests

To execute the test suite (which includes the single-node radiation check, the thermostat hysteresis test, and the zero-forcing cooling check):
```bash
pytest -v
```
All model parameters are traceable to `data/assumptions_register.csv` to ensure data provenance and transparency.
