# Thermal Simulation Report: bounding_cold

- **Description**: Low-beta dawn-dusk SSO bounding cold case: maximum eclipse duration, minimum solar flux, minimum thermal loading
- **Converged**: False
- **Orbits Simulated**: 15
- **Overall Verdict**: **robust pass**

## Component Temperatures and Margins

| Component | Min Temp [°C] | Max Temp [°C] | Lower Limit [°C] | Upper Limit [°C] | Lower Margin [°C] | Upper Margin [°C] | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `battery` | 5.00 | 10.01 | -10.00 | 45.00 | 15.00 | 34.99 | **robust pass** |
| `avionics` | -0.83 | 0.83 | -20.00 | 60.00 | 19.17 | 59.17 | **robust pass** |
| `payload` | -1.72 | -0.53 | -10.00 | 50.00 | 8.28 | 50.53 | **robust pass** |
| `structure` | -2.18 | -0.10 | -40.00 | 80.00 | 37.82 | 80.10 | **robust pass** |
| `radiator` | -1.36 | 0.26 | -100.00 | 100.00 | 98.64 | 99.74 | **robust pass** |
| `external_shell` | -15.55 | -3.50 | -100.00 | 100.00 | 84.45 | 103.50 | **robust pass** |

## Thermal Control Performance

- **Heater Duty Cycle**: 36.73%
- **Heater Energy Consumption per Orbit**: 5.922 Wh

## Energy Bookkeeping Balance check

- **Thermal Energy Change (dE)**: -62302.79 J
- **Internal Dissipation Energy Input**: 435150.00 J
- **Environmental Heat Input**: 2754820.96 J
- **Heater Heat Input**: 346780.00 J
- **Deep Space Radiation Output**: 3599054.56 J
- **Energy Balance Residual**: 0.81 J (Relative Error: 1.30e-05)

> [!NOTE]
> This is a preliminary, simplified, reference-informed thermal model rather than a flight-qualified design.
> It requires future correlation with detailed models and TVAC / thermal-balance test.
