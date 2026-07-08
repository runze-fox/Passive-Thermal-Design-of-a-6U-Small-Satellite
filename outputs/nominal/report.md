# Thermal Simulation Report: nominal

- **Description**: Nominal scenario evaluating average performance under representative 6U dawn-dusk SSO orbit (65 deg beta)
- **Converged**: True
- **Orbits Simulated**: 13
- **Overall Verdict**: **robust pass**

## Component Temperatures and Margins

| Component | Min Temp [°C] | Max Temp [°C] | Lower Limit [°C] | Upper Limit [°C] | Lower Margin [°C] | Upper Margin [°C] | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `battery` | 14.84 | 15.08 | -10.00 | 45.00 | 24.84 | 29.92 | **robust pass** |
| `avionics` | 16.39 | 17.08 | -20.00 | 60.00 | 36.39 | 42.92 | **robust pass** |
| `payload` | 14.08 | 17.71 | -10.00 | 50.00 | 24.08 | 32.29 | **robust pass** |
| `structure` | 13.17 | 14.17 | -40.00 | 80.00 | 53.17 | 65.83 | **robust pass** |
| `radiator` | 15.57 | 16.24 | -100.00 | 100.00 | 115.57 | 83.76 | **robust pass** |
| `external_shell` | -0.04 | 8.02 | -100.00 | 100.00 | 99.96 | 91.98 | **robust pass** |

## Thermal Control Performance

- **Heater Duty Cycle**: 0.00%
- **Heater Energy Consumption per Orbit**: 0.000 Wh

## Energy Bookkeeping Balance check

- **Thermal Energy Change (dE)**: -66026.20 J
- **Internal Dissipation Energy Input**: 909093.00 J
- **Environmental Heat Input**: 2859010.81 J
- **Heater Heat Input**: 0.00 J
- **Deep Space Radiation Output**: 3834162.05 J
- **Energy Balance Residual**: 32.04 J (Relative Error: 4.85e-04)

> [!NOTE]
> This is a preliminary, simplified, reference-informed thermal model rather than a flight-qualified design.
> It requires future correlation with detailed models and TVAC / thermal-balance test.
