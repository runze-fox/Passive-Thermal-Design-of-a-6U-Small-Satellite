# Thermal Simulation Report: cold_stress

- **Description**: Cold stress case to trigger battery survival heater cycling under representative low-beta dawn-dusk SSO equinox and standby power
- **Converged**: False
- **Orbits Simulated**: 15
- **Overall Verdict**: **FAIL**

## Component Temperatures and Margins

| Component | Min Temp [°C] | Max Temp [°C] | Lower Limit [°C] | Upper Limit [°C] | Lower Margin [°C] | Upper Margin [°C] | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `battery` | -0.23 | 0.00 | -10.00 | 45.00 | 9.77 | 45.00 | **robust pass** |
| `avionics` | -19.13 | -18.63 | -20.00 | 60.00 | 0.87 | 78.63 | **marginal pass** |
| `payload` | -20.32 | -19.99 | -10.00 | 50.00 | -10.32 | 69.99 | **FAIL** |
| `structure` | -20.49 | -19.86 | -40.00 | 80.00 | 19.51 | 99.86 | **robust pass** |
| `radiator` | -19.61 | -19.12 | -100.00 | 100.00 | 80.39 | 119.12 | **robust pass** |
| `external_shell` | -34.01 | -29.90 | -100.00 | 100.00 | 65.99 | 129.90 | **robust pass** |

## Thermal Control Performance

- **Heater Duty Cycle**: 100.00%
- **Heater Energy Consumption per Orbit**: 16.122 Wh

## Energy Bookkeeping Balance check

- **Thermal Energy Change (dE)**: -179930.55 J
- **Internal Dissipation Energy Input**: 435150.00 J
- **Environmental Heat Input**: 1137795.63 J
- **Heater Heat Input**: 838700.00 J
- **Deep Space Radiation Output**: 2591589.93 J
- **Energy Balance Residual**: 13.74 J (Relative Error: 7.64e-05)

> [!NOTE]
> This is a preliminary, simplified, reference-informed thermal model rather than a flight-qualified design.
> It requires future correlation with detailed models and TVAC / thermal-balance test.
