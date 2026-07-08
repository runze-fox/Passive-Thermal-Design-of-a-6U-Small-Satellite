# Reference-Informed Preliminary Thermal Analysis of a 6U LEO CubeSat
## Implementation Brief for Coding Agent

## 1. Project objective

Build a transparent, reproducible Python thermal-analysis workflow for a **reference-informed preliminary thermal design** of a nominal 6U CubeSat in low Earth orbit (LEO).

The model is **not** intended to be flight-qualified or a substitute for Thermal Desktop / SINDA-FLUINT. It is an early-phase engineering model intended to:

1. Evaluate transient temperatures during sunlit and eclipse portions of LEO orbit.
2. Compare nominal, bounding-hot, and bounding-cold mission cases.
3. Evaluate initial thermal-control choices:
   - exterior material/coating selection;
   - radiator area;
   - radiator emissivity and solar absorptivity;
   - conductive coupling / thermal-strap effectiveness;
   - battery survival-heater power and thermostat thresholds.
4. Report temperature margins against declared component operating limits.
5. Preserve full data provenance: every parameter is either:
   - public/reference-derived;
   - derived from a public source;
   - or explicitly labeled as an engineering assumption.

The model should prioritize **clarity, traceability, modularity, and plot quality** over maximum physical fidelity.

---

## 2. Core modeling philosophy

Use a lumped-parameter thermal network:

- Each thermal node has one uniform temperature.
- Internal conduction is represented with equivalent thermal conductances.
- External radiation is modeled with simplified view factors.
- Direct solar, albedo, Earth IR, internal electronics dissipation, deep-space radiation, and heater power are included.
- No convection in orbit.
- A piecewise orbit environment represents sunlit and eclipse periods.
- Thermal control is modeled with thermostat hysteresis.

The governing equation for node `i` is:

\[
C_i \frac{dT_i}{dt}
=
Q_{\mathrm{internal},i}
+
Q_{\mathrm{solar},i}
+
Q_{\mathrm{albedo},i}
+
Q_{\mathrm{EarthIR},i}
+
Q_{\mathrm{heater},i}
+
\sum_j G_{ij}(T_j-T_i)
-
Q_{\mathrm{rad\_space},i}
\]

where:

- \(C_i=m_i c_{p,i}\) is lumped thermal capacitance [J/K].
- \(G_{ij}\) is effective conductive coupling [W/K].
- \(Q_{\mathrm{rad\_space}}\) is outgoing radiation to deep space [W].
- All temperatures in physical equations must use Kelvin.

For a node with direct view to deep space:

\[
Q_{\mathrm{rad\_space},i}
=
\epsilon_i \sigma A_i F_{i\rightarrow space}
\left(T_i^4-T_{space}^4\right)
\]

Use `T_space = 3 K` or `4 K`; document the selected value.

For direct solar heating:

\[
Q_{\mathrm{solar},i}
=
\alpha_{s,i}\, S\, A_i\, \max(0,\cos\theta_i)\, f_{\mathrm{sunlit}}
\]

For a first-pass model, albedo and Earth IR may use simplified effective view factors:

\[
Q_{\mathrm{albedo},i}
=
\alpha_{s,i}\, S\, ALB\, A_i\, F_{i\rightarrow Earth}\, f_{\mathrm{sunlit}}
\]

\[
Q_{\mathrm{EarthIR},i}
=
\epsilon_{IR,i}\, EIR\, A_i\, F_{i\rightarrow Earth}
\]

This simplification should be stated explicitly in documentation.

---

## 3. Scope

### In scope

- Circular LEO mission concept.
- 6U CubeSat simplified bus geometry.
- Direct solar heating.
- Earth albedo.
- Earth IR / planetary IR.
- Eclipse transitions.
- Deep-space radiative heat rejection.
- Internal component dissipation.
- Passive surface-property trade study.
- Battery heater with hysteresis.
- Equivalent conductive heat paths.
- Nominal / hot / cold cases.
- Design-trade plots and temperature margins.
- Parameter provenance / assumptions register.

### Explicitly out of scope

- Flight-qualified detailed thermal model.
- CAD-derived view-factor calculation.
- Full multi-reflection radiosity solver.
- Detailed internal radiation cavity model.
- Detailed harness thermal conduction.
- PCB or electronic-component-level model.
- Detailed MLI layer-by-layer model.
- Atomic oxygen degradation model.
- Contamination model.
- Launch ascent free-molecular heating and aeroheating.
- Detailed two-phase heat-pipe / loop heat-pipe model.
- Real MDA Space proprietary hardware, mission geometry, or internal design data.
- TVAC test execution or correlation to real chamber data.

---

## 4. Reference architecture

### 4.1 Simplified platform geometry

Use a standard nominal 6U rectangular envelope:

\[
L \times W \times H = 0.30 \times 0.20 \times 0.10\ \mathrm{m}
\]

This geometry is only a preliminary reference envelope, not a claim of exact flight hardware geometry.

External faces:

| Face ID | Nominal dimensions | Area [m²] | Proposed role |
|---|---:|---:|---|
| `+X` / `-X` | 0.30 × 0.20 m | 0.060 | large outer faces / solar panel or radiator candidate |
| `+Y` / `-Y` | 0.30 × 0.10 m | 0.030 | side faces |
| `+Z` / `-Z` | 0.20 × 0.10 m | 0.020 | end faces / payload aperture candidate |

For the first version, do not attempt arbitrary attitude dynamics. Use a declared fixed attitude convention and surface exposure factors.

### 4.2 Recommended thermal nodes

Implement the following six-node network:

| Node ID | Description | Key behavior |
|---|---|---|
| `battery` | Battery pack | cold-sensitive; thermostat heater |
| `avionics` | OBC / EPS / radio electronics lump | continuous or near-continuous internal dissipation |
| `payload` | Earth-observation payload | duty-cycled dissipation |
| `structure` | Main aluminum structural bus / mounting deck | thermal hub |
| `radiator` | Dedicated high-emittance thermal rejection surface | radiation-dominant node |
| `external_panel` | Representative external wall / body-mounted solar-panel-coupled node | receives orbit heat loads |

Optional future expansion: separate solar panel, payload optical bench, and dedicated battery enclosure nodes.

### 4.3 Recommended conductive links

Implement each as symmetric effective conductance `G_ij` [W/K]:

- battery ↔ structure
- avionics ↔ structure
- payload ↔ structure
- structure ↔ radiator
- avionics ↔ radiator (thermal strap path)
- external_panel ↔ structure

Store these links in a config file, not hardcoded in solver code.

---

## 5. Thermal-control architecture assumptions

Use the following architecture concept in diagrams/documentation:

- A dedicated radiator surface has low solar absorptivity and high IR emissivity.
- Avionics have a conductive path / equivalent thermal strap to radiator.
- Battery is mounted to structure and has a survival heater.
- Battery is thermally moderated from direct external exposure.
- Payload has a duty cycle and conducts to structure.
- External panel receives direct solar, albedo, and Earth IR according to simplified exposure factors.

Do not claim a specific commercial material until source values have been entered in the data register.

---

## 6. Required cases

### 6.1 Nominal case

Purpose: establish expected periodic orbital behavior.

Suggested starting assumptions:

- Circular LEO altitude: 550 km.
- Orbit period: either computed from orbital mechanics or configured as approximately 95 minutes.
- Sunlit duration: approximately 60 minutes.
- Eclipse duration: approximately 35 minutes.
- Solar flux: nominal reference value.
- Albedo: nominal value.
- Earth IR: nominal value.
- Nominal internal power schedule.
- Simulate at least 5 consecutive orbits, or until approximate periodic steady state is reached.

### 6.2 Bounding hot case

Purpose: identify maximum temperatures and radiator adequacy.

Use a deliberately conservative stacking of unfavorable assumptions, such as:

- high solar flux;
- high albedo;
- high Earth IR;
- maximum avionics dissipation;
- maximum payload duty cycle or continuous high-power payload operation;
- degraded / end-of-life optical properties where reference data support it;
- reduced effective radiator deep-space view factor, if included;
- heater disabled unless explicitly required.

Primary acceptance criterion:

\[
T_{i,\max}^{predicted} < T_{i,\max}^{limit}
\]

### 6.3 Bounding cold case

Purpose: identify minimum temperatures and heater adequacy.

Use conservative cold conditions, such as:

- low solar flux during sunlit segments;
- eclipse period;
- low internal dissipation / payload off;
- low Earth IR;
- albedo set to zero during eclipse;
- battery thermostat heater active;
- high outward radiative effectiveness if treated as a conservative cold assumption.

Primary acceptance criterion:

\[
T_{i,\min}^{predicted} > T_{i,\min}^{limit}
\]

---

## 7. Heater control logic

Implement a thermostat with hysteresis for the battery node.

Example initial logic:

```text
if T_battery <= T_on:
    heater = ON
elif T_battery >= T_off:
    heater = OFF
else:
    retain previous heater state
```

Use configurable parameters:

- `heater_power_w`
- `heater_on_c`
- `heater_off_c`

Suggested initial placeholder thresholds for implementation testing only:

- Heater ON below `5 °C`
- Heater OFF above `10 °C`

These must be stored as assumptions unless later replaced by a selected public battery data sheet.

The simulation should record:

- heater ON/OFF state;
- heater power versus time;
- heater duty cycle;
- total heater energy per orbit.

---

## 8. External-environment model

### 8.1 Required input variables

Create a scenario-level environment config with:

- `altitude_m`
- `orbit_period_s`
- `sunlit_duration_s`
- `eclipse_duration_s`
- `solar_flux_w_m2`
- `albedo`
- `earth_ir_w_m2`
- `space_temperature_k`
- `beta_angle_deg` (documented but optional in v1 behavior)
- `attitude_label`
- per-node or per-surface:
  - `solar_exposure_factor`
  - `earth_view_factor`
  - `space_view_factor`

### 8.2 Simplified orbit schedule

Version 1 should use a square-wave orbit schedule:

```text
sunlit: direct solar enabled; albedo enabled
eclipse: direct solar = 0; albedo = 0; Earth IR remains active
```

Earth IR should remain active in eclipse for Earth-facing / Earth-viewing surfaces.

Version 2 optional extension:
- smooth transition at eclipse entry/exit;
- beta-angle-dependent eclipse duration;
- orbit-anomaly calculation.

### 8.3 Unit conventions

- Temperature state vector: Kelvin internally.
- User-readable plot labels: Celsius.
- Areas: m².
- Power: W.
- Heat capacity: J/K.
- Conductance: W/K.
- Time: s internally; minutes or orbit fraction in plots.

Add assertions / validation checks to prevent Celsius use in `T^4` radiation terms.

---

## 9. Materials and data provenance

All physical parameters must be data-driven and traceable.

### 9.1 Required data files

Create:

```text
data/
  materials.csv
  components.csv
  thermal_links.csv
  scenario_nominal.yaml
  scenario_hot.yaml
  scenario_cold.yaml
  assumptions_register.csv
```

Suggested `materials.csv` columns:

```text
material_id
manufacturer
product_name
category
alpha_s_bol
epsilon_ir_bol
alpha_s_eol
epsilon_ir_eol
temperature_min_c
temperature_max_c
proposed_use
source_title
source_url
source_page_or_table
source_date
data_quality
notes
```

Suggested `components.csv` columns:

```text
node_id
description
mass_kg
cp_j_kgk
thermal_capacitance_j_k
temperature_min_c
temperature_max_c
nominal_dissipation_w
hot_dissipation_w
cold_dissipation_w
duty_cycle_definition
external_area_m2
alpha_s
epsilon_ir
earth_view_factor
space_view_factor
solar_exposure_factor
data_status
source_or_assumption_id
notes
```

Suggested `thermal_links.csv` columns:

```text
node_i
node_j
conductance_w_k
link_type
basis
source_or_assumption_id
notes
```

Suggested `assumptions_register.csv` columns:

```text
assumption_id
parameter
value
unit
classification
rationale
source_or_method
impact_if_wrong
revision_status
```

Allowed `classification` values:

- `public_reference`
- `derived_from_public_reference`
- `engineering_assumption`
- `sensitivity_parameter`
- `placeholder_for_testing`

### 9.2 Important interpretation rule

Do not silently use an EOL property as a BOL property, or vice versa.

Each scenario should explicitly select a property set, for example:

```text
nominal -> BOL or nominal public value
hot -> EOL / conservative optical properties where available
cold -> declared conservative cold property selection
```

---

## 10. Solver requirements

### 10.1 Recommended implementation

Use Python with:

- `numpy`
- `pandas`
- `scipy`
- `matplotlib`
- `pyyaml`
- optional `plotly`

Use `scipy.integrate.solve_ivp` or a robust fixed-step integrator. Since thermostat logic introduces discontinuities, a fixed-step RK4 or semi-implicit scheme may be easier to debug and reproduce.

Preferred initial approach:

- fixed timestep: 1–10 s;
- simulate multiple full orbits;
- implement heater state update at every timestep;
- validate energy signs carefully.

### 10.2 Minimum API

Suggested functions:

```python
load_project_data(...)
build_thermal_network(...)
build_environment_schedule(...)
compute_external_loads(...)
compute_internal_dissipation(...)
compute_heater_power(...)
thermal_rhs(...)
simulate_case(...)
compute_temperature_margins(...)
run_trade_study(...)
generate_all_figures(...)
```

### 10.3 Validation requirements

Add at least these checks:

1. **No forcing sanity test**
   - no internal power;
   - no solar/albedo/Earth IR;
   - node with deep-space view should cool monotonically.

2. **Steady-state radiation sanity test**
   - one isolated radiator node with constant internal dissipation;
   - compare numerical steady state with:
     \[
     T \approx \left(\frac{Q}{\epsilon\sigma A}\right)^{1/4}
     \]
     when deep-space term is negligible.

3. **Heater hysteresis test**
   - verify no rapid switching at a single threshold;
   - heater should turn on/off only at configured limits.

4. **Energy bookkeeping diagnostic**
   - save component-wise power terms over time;
   - provide optional total-energy / residual plot.

5. **Physical limits**
   - no negative area, mass, capacitance, emissivity, absorptivity, or conductance;
   - enforce `0 <= alpha <= 1`, `0 <= epsilon <= 1`;
   - enforce nonnegative view factors.

---

## 11. Required outputs and visualizations

All outputs should be saved in `outputs/<scenario_or_trade_name>/`.

### 11.1 Essential figures

1. **Thermal architecture schematic**
   - Can be a generated node/link diagram.
   - Show battery, avionics, payload, structure, radiator, external panel.
   - Label major conductive links and heater.

2. **Orbit heat-load timeline**
   - Direct solar, albedo, Earth IR, internal dissipation, heater power.
   - Clearly shade or annotate sunlit versus eclipse.

3. **Temperature time history**
   - Battery, avionics, payload, structure, radiator.
   - Plot in °C.
   - Add component temperature-limit lines.
   - Mark eclipse intervals.
   - Mark heater ON intervals.

4. **Temperature margin summary**
   - Per component:
     - lower margin;
     - upper margin;
     - pass/fail.
   - A clean horizontal bar chart or table.

5. **Radiator-area trade study**
   - x-axis: radiator area [m²].
   - y-axis: hot-case peak avionics / structure temperature.
   - Include upper temperature limit.

6. **Heater-power trade study**
   - x-axis: heater power [W].
   - y-axis: cold-case battery minimum temperature and/or heater duty cycle.
   - Include lower battery temperature limit.

7. **Material trade plot**
   - x-axis: solar absorptivity \(\alpha_s\).
   - y-axis: IR emissivity \(\epsilon_{IR}\).
   - Plot all material candidates.
   - Highlight selected radiator and exterior material.
   - Include a note that radiator desirability is generally low-\(\alpha\), high-\(\epsilon\).

### 11.2 Optional advanced figures

- Sankey-style average heat-flow diagram.
- Surface/face exposure diagram for 6U bus.
- 2D sensitivity heatmap:
  - radiator area vs thermal-strap conductance;
  - color = hot-case peak avionics temperature.
- Heater duty cycle versus eclipse duration.
- Multi-orbit convergence plot.

### 11.3 Style constraints

- Clean publication/portfolio style.
- No decorative 3D effects.
- Use clear labels, units, legends, and concise captions.
- Use a consistent palette across figures.
- Save both `.png` and `.svg` where practical.

---

## 12. Trade studies

Implement the following in priority order.

### Trade study A: radiator area

Sweep a configurable radiator area range, for example:

\[
0.005 \text{ to } 0.040\ \mathrm{m^2}
\]

Output:
- peak radiator temperature;
- peak avionics temperature;
- peak structure temperature;
- pass/fail against hot-case limits.

Identify the smallest candidate area that meets all declared hot-case requirements with margin.

### Trade study B: battery heater power

Sweep a configurable heater range, e.g.:

\[
0,\ 2,\ 5,\ 8,\ 10,\ 12,\ 15\ \mathrm{W}
\]

Output:
- cold-case minimum battery temperature;
- heater duty cycle;
- heater energy consumption per orbit;
- pass/fail.

### Trade study C: radiator material / surface property

Use candidate material properties from `materials.csv`.

Output:
- maximum hot-case temperature;
- radiator operating temperature;
- thermal margin;
- comparative \(\alpha_s\)–\(\epsilon_{IR}\) visualization.

### Trade study D: avionics-to-radiator thermal conductance

Sweep thermal strap / path conductance.

Output:
- avionics peak temperature;
- radiator peak temperature;
- temperature drop from avionics to radiator;
- practical diminishing-return region.

---

## 13. Reporting logic

For every scenario, generate a machine-readable summary:

```json
{
  "scenario": "hot_case",
  "result": "PASS/FAIL",
  "periodic_orbits_simulated": 5,
  "battery": {
    "min_c": ...,
    "max_c": ...,
    "lower_margin_c": ...,
    "upper_margin_c": ...
  },
  "avionics": {},
  "payload": {},
  "radiator": {},
  "heater": {
    "duty_cycle": ...,
    "energy_per_orbit_wh": ...
  },
  "selected_assumption_ids": []
}
```

Also generate a concise Markdown report fragment that can be inserted into the final technical note.

The report should always distinguish:

- **model prediction**;
- **component limit**;
- **temperature margin**;
- **input/source status**;
- **limitations**.

Never present model output as flight-qualified verification.

---

## 14. Recommended repository structure

```text
cubesat_thermal/
├── README.md
├── pyproject.toml
├── requirements.txt
├── data/
│   ├── materials.csv
│   ├── components.csv
│   ├── thermal_links.csv
│   ├── assumptions_register.csv
│   └── scenarios/
│       ├── nominal.yaml
│       ├── hot.yaml
│       └── cold.yaml
├── src/
│   └── cubesat_thermal/
│       ├── __init__.py
│       ├── config.py
│       ├── data_io.py
│       ├── environment.py
│       ├── network.py
│       ├── controls.py
│       ├── solver.py
│       ├── analysis.py
│       ├── plotting.py
│       └── validation.py
├── scripts/
│   ├── run_case.py
│   ├── run_all_cases.py
│   ├── run_trade_studies.py
│   └── build_report_assets.py
├── tests/
│   ├── test_environment.py
│   ├── test_radiation.py
│   ├── test_thermostat.py
│   └── test_sanity_cases.py
├── notebooks/
│   └── exploratory_analysis.ipynb
├── outputs/
└── docs/
    ├── scope.md
    ├── data_provenance.md
    ├── modeling_assumptions.md
    └── verification_matrix.md
```

---

## 15. Development milestones

### Milestone 0 — repository and data skeleton

Create project structure, config parsing, placeholder data files, and assumptions register.

### Milestone 1 — single-node validation model

Implement isolated radiator node:
- constant dissipation;
- deep-space radiation;
- analytical steady-state comparison.

### Milestone 2 — six-node network, no orbit forcing

Implement conductive network and internal dissipation only.

### Milestone 3 — nominal orbit forcing

Add direct solar, albedo, Earth IR, sunlit/eclipse schedule, and multi-orbit simulation.

### Milestone 4 — heater control

Add thermostat hysteresis and cold-case analysis.

### Milestone 5 — hot/cold cases and margins

Add scenario configs, temperature-limit checks, summaries, and pass/fail logic.

### Milestone 6 — trade studies and polished plots

Implement radiator area, heater power, material selection, and thermal-strap conductance sweeps.

### Milestone 7 — report assets

Generate clean figures, tables, and Markdown results summaries for technical report / GitHub README.

---

## 16. Important engineering language to use in documentation

Use these terms accurately:

- `preliminary thermal design`
- `reference-informed`
- `lumped-parameter thermal network`
- `bounding hot case`
- `bounding cold case`
- `stacked worst-case assumptions`
- `temperature margin`
- `thermal-control architecture`
- `survival heater`
- `thermostat hysteresis`
- `radiative heat rejection`
- `data provenance`
- `engineering assumption`
- `analysis-based verification concept`
- `not flight-qualified`
- `requires future correlation with detailed model and TVAC / thermal-balance test`

Avoid claims such as:
- “flight-ready”
- “MDA-based design”
- “validated spacecraft model”
- “flight-qualified”
unless actual supporting evidence exists.

---

## 17. Immediate next actions for the coding agent

1. Create the repository structure and installable Python package.
2. Add YAML scenario parsing and CSV data loaders.
3. Create placeholder-but-clearly-labeled `engineering_assumption` data records so the code can run before the real material database is complete.
4. Implement a single-node radiator validation case and tests.
5. Implement the six-node data model and thermal RHS.
6. Implement nominal sunlit/eclipse schedule.
7. Generate first temperature time-history plot and power-term diagnostic.
8. Do not hardcode source values in solver functions.
9. Provide a small CLI command for:
   ```bash
   python scripts/run_case.py --scenario data/scenarios/nominal.yaml
   ```
10. Produce a short `README.md` that explains setup, run commands, limitations, and the source/assumption convention.

---

## 18. Definition of done for first usable version

The first usable version is complete when:

- A nominal six-node model runs for at least five orbits.
- Sunlit/eclipsed heat-load changes visibly affect temperatures.
- Battery heater hysteresis activates correctly in cold case.
- Direct solar and albedo are zero during eclipse.
- Earth IR remains active during eclipse.
- The model saves a temperature plot, a heat-load plot, a margin table, and a JSON summary.
- A radiator-area sweep and heater-power sweep run from configuration files.
- All model inputs are traceable either to a public-reference entry or an explicit engineering-assumption entry.
- The README explicitly says this is a preliminary, simplified, reference-informed thermal model rather than a flight-qualified design.
