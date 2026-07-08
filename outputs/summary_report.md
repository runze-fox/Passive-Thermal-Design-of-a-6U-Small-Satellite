# Passive Thermal Design of a Small Satellite Under a High-Beta Bounding Hot Case - Summary Report

> [!IMPORTANT]
> **Analysis Status:** Preliminary reference-informed thermal design. Not flight-qualified. This analysis serves as a verification concept and requires future correlation with detailed geometric models and TVAC / thermal-balance test.

## 1. Case Simulation Results

| Case | Status | Orbits Simulated | Battery Temp [°C] | Avionics Temp [°C] | Payload Temp [°C] | Structure Temp [°C] | Heater Duty Cycle | Heater Energy [Wh/orbit] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `nominal` | **robust pass** | 13 | 14.8 to 15.1 | 16.4 to 17.1 | 14.1 to 17.7 | 13.2 to 14.2 | 0.0% | 0.00 |
| `bounding_hot` | **robust pass** | 8 | 35.0 to 35.4 | 38.1 to 39.2 | 34.0 to 40.3 | 33.5 to 34.8 | 0.0% | 0.00 |
| `bounding_cold` | **robust pass** | 15 | 5.0 to 10.0 | -0.8 to 0.8 | -1.7 to -0.5 | -2.2 to -0.1 | 36.7% | 5.92 |
| `cold_stress` | **FAIL** | 15 | -0.2 to 0.0 | -19.1 to -18.6 | -20.3 to -20.0 | -20.5 to -19.9 | 100.0% | 16.12 |

## 2. Trade Studies Summary

### Trade A: Radiator Area Sweep (Hot Case)

| radiator_area_m2 | peak_radiator_temp_c | peak_avionics_temp_c | peak_structure_temp_c | avionics_margin_c | status |
| --- | --- | --- | --- | --- | --- |
| 0.00500 | 45.99 | 46.74 | 41.21 | 13.26 | acceptable preliminary pass |
| 0.01000 | 43.02 | 43.93 | 38.83 | 16.07 | robust pass |
| 0.01500 | 40.33 | 41.40 | 36.69 | 18.60 | robust pass |
| 0.02000 | 37.95 | 39.17 | 34.82 | 20.83 | robust pass |
| 0.02500 | 35.60 | 36.94 | 32.92 | 23.06 | robust pass |
| 0.03000 | 33.41 | 34.87 | 31.16 | 25.13 | robust pass |
| 0.03500 | 31.37 | 32.96 | 29.52 | 27.04 | robust pass |
| 0.04000 | 29.46 | 31.15 | 27.98 | 28.85 | robust pass |

### Trade A2: System-Level Radiator Sizing Trade-Off (Hot vs. Cold Performance)

| radiator_area_m2 | hot_peak_avionics_c | hot_peak_battery_c | nom_peak_avionics_c | nom_peak_battery_c | cold_min_avionics_c | cold_min_battery_c | cold_heater_duty_cycle | cold_heater_energy_wh |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.02000 | 39.17 | 35.39 | 17.08 | 15.08 | -0.82723 | 5.00 | 0.36733 | 5.92 |
| 0.03000 | 34.87 | 31.73 | 13.67 | 12.13 | -2.43 | 5.00 | 0.41489 | 6.69 |
| 0.04000 | 31.15 | 28.55 | 10.63 | 9.50 | -3.93 | 5.00 | 0.49001 | 7.90 |
| 0.05000 | 27.80 | 25.68 | 7.91 | 7.14 | -5.34 | 5.00 | 0.63611 | 10.26 |
| 0.06000 | 24.81 | 23.13 | 6.15 | 10.00 | -6.55 | 4.99 | 0.60855 | 9.81 |

### Trade B: Battery Survival Heater Power (Cold Case)

| heater_power_w | min_battery_temp_c | battery_lower_margin_c | heater_duty_cycle | heater_energy_wh | status |
| --- | --- | --- | --- | --- | --- |
| 0.00 | -11.45 | -1.45 | 0.00 | 0.00 | FAIL |
| 2.00 | -2.71 | 7.29 | 1.00 | 3.22 | acceptable preliminary pass |
| 5.00 | 8.74 | 18.74 | 1.00 | 8.06 | robust pass |
| 8.00 | 5.00 | 15.00 | 0.59166 | 7.63 | robust pass |
| 10.00 | 5.00 | 15.00 | 0.36733 | 5.92 | robust pass |
| 12.00 | 5.00 | 15.00 | 0.30048 | 5.81 | robust pass |
| 15.00 | 4.99 | 14.99 | 0.29566 | 7.15 | robust pass |

### Trade C: Radiator Material Coating Performance (Hot Case)

| material_id | alpha_s | epsilon_ir | peak_radiator_temp_c | peak_avionics_temp_c | avionics_margin_c | status |
| --- | --- | --- | --- | --- | --- | --- |
| AZ-93 Silicate | 0.16000 | 0.90000 | 37.14 | 38.40 | 21.60 | robust pass |
| 0.005″ FEP/Ag/Inconel | 0.07000 | 0.79000 | 37.95 | 39.17 | 20.83 | robust pass |
| VDA/200HN/PSA | 0.08000 | 0.03000 | 49.35 | 49.90 | 10.10 | marginal pass |
| Z306 Polyurethane | 0.92000 | 0.89000 | 41.98 | 42.96 | 17.04 | robust pass |
| solar_cell_assembly | 0.73000 | 0.82000 | 41.71 | 42.70 | 17.30 | robust pass |

### Trade D: Avionics-to-Radiator Thermal Strap Conductance (Hot Case)

| strap_conductance_w_k | peak_avionics_temp_c | peak_radiator_temp_c | temp_drop_avionics_to_rad_c | avionics_margin_c | status |
| --- | --- | --- | --- | --- | --- |
| 0.10000 | 42.75 | 30.45 | 12.30 | 17.25 | robust pass |
| 0.50000 | 41.07 | 34.02 | 7.05 | 18.93 | robust pass |
| 1.00 | 40.26 | 35.66 | 4.59 | 19.74 | robust pass |
| 2.00 | 39.65 | 36.94 | 2.71 | 20.35 | robust pass |
| 5.00 | 39.17 | 37.95 | 1.21 | 20.83 | robust pass |
| 10.00 | 38.98 | 38.35 | 0.63205 | 21.02 | robust pass |

### Trade E: Battery-to-Structure Conductive Isolation Sweep

| battery_structure_conductance_w_k | hot_battery_peak_c | cold_battery_min_c | heater_duty_cycle | heater_energy_wh | hot_case_status | cold_case_status |
| --- | --- | --- | --- | --- | --- | --- |
| 0.01000 | 60.14 | 5.00 | 0.10992 | 1.77 | FAIL | FAIL |
| 0.02000 | 53.26 | 5.00 | 0.11647 | 1.88 | FAIL | FAIL |
| 0.05000 | 43.81 | 5.00 | 0.27705 | 4.47 | marginal pass | FAIL |
| 0.10000 | 39.11 | 5.00 | 0.39352 | 6.34 | robust pass | FAIL |
| 0.20000 | 36.79 | 4.99 | 0.75155 | 12.12 | robust pass | FAIL |
| 0.50000 | 35.39 | -0.22822 | 1.00 | 16.12 | robust pass | FAIL |
| 1.00 | 35.01 | -10.15 | 1.00 | 16.12 | robust pass | FAIL |

### Trade F: Payload-to-Radiator Conductive Strap Sweep (Hot Case)

| payload_radiator_conductance_w_k | peak_payload_temp_c | peak_radiator_temp_c | payload_margin_c | status |
| --- | --- | --- | --- | --- |
| 0.00 | 40.30 | 37.95 | 9.70 | robust pass |
| 0.20000 | 40.31 | 37.97 | 9.69 | robust pass |
| 0.50000 | 40.24 | 38.04 | 9.76 | robust pass |
| 1.00 | 40.10 | 38.19 | 9.90 | robust pass |
| 2.00 | 39.88 | 38.46 | 10.12 | robust pass |
| 5.00 | 39.59 | 38.85 | 10.41 | robust pass |

