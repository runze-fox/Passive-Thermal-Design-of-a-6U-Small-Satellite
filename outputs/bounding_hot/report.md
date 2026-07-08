# Thermal Simulation Report: bounding_hot

- **Description**: High-beta dawn-dusk SSO bounding hot case: continuous sunlight, no umbral eclipse, maximum sustained external heat input
- **Converged**: True
- **Orbits Simulated**: 8
- **Overall Verdict**: **robust pass**

## Component Temperatures and Margins

| Component | Min Temp [°C] | Max Temp [°C] | Lower Limit [°C] | Upper Limit [°C] | Lower Margin [°C] | Upper Margin [°C] | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `battery` | 34.97 | 35.39 | -10.00 | 45.00 | 44.97 | 9.61 | **robust pass** |
| `avionics` | 38.10 | 39.17 | -20.00 | 60.00 | 58.10 | 20.83 | **robust pass** |
| `payload` | 34.01 | 40.30 | -10.00 | 50.00 | 44.01 | 9.70 | **robust pass** |
| `structure` | 33.46 | 34.82 | -40.00 | 80.00 | 73.46 | 45.18 | **robust pass** |
| `radiator` | 36.90 | 37.95 | -100.00 | 100.00 | 136.90 | 62.05 | **robust pass** |
| `external_shell` | 21.98 | 22.59 | -100.00 | 100.00 | 121.98 | 77.41 | **robust pass** |

## Thermal Control Performance

- **Heater Duty Cycle**: 0.00%
- **Heater Energy Consumption per Orbit**: 0.000 Wh

## Energy Bookkeeping Balance check

- **Thermal Energy Change (dE)**: -19650.65 J
- **Internal Dissipation Energy Input**: 863538.00 J
- **Environmental Heat Input**: 2043401.74 J
- **Heater Heat Input**: 0.00 J
- **Deep Space Radiation Output**: 2926576.65 J
- **Energy Balance Residual**: -13.73 J (Relative Error: -6.99e-04)

> [!NOTE]
> This is a preliminary, simplified, reference-informed thermal model rather than a flight-qualified design.
> It requires future correlation with detailed models and TVAC / thermal-balance test.
