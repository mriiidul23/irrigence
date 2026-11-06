# Irrigence

**A Digital Spatial Decision-Support Platform for Irrigation Canal Monitoring**

Submission for the North East Seva First Innovation Challenge (NESFIC) 2026 · Problem Statement DPS 2

Irrigation canal condition monitoring, water balance anomaly detection and geotechnical risk prediction.

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Screenshots](#screenshots)
4. [System Architecture](#system-architecture)
5. [Technology Stack](#technology-stack)
6. [Mathematical Formulation](#mathematical-formulation)
7. [Installation and Usage](#installation-and-usage)
8. [Automated Verification](#automated-verification)
9. [Project Structure](#project-structure)
10. [Limitations and Future Work](#limitations-and-future-work)
11. [Team](#team)

---

## Overview

Irrigence is a digital spatial decision-support system that monitors the embankment integrity and hydraulic conveyance efficiency of gravity irrigation canals in North East India. The prototype is simulated for the Kopili-Jamuna canal corridor in Assam.

Physical IoT sensors are still being procured. To allow development and validation in the meantime, Irrigence includes:

- A physics-based synthetic telemetry generator for canal reaches and multi-sensor time series.
- A machine learning surrogate engine that learns normal hydraulic and geotechnical behaviour, detects seepage anomalies and computes reach-by-reach failure risk.
- An operational GIS dashboard that presents the results to canal managers.

## Key Features

- **Synthetic GIS and sensor data:** Canal reach geometry, flow, pore pressure and soil moisture series with injectable anomalies.
- **Water balance anomaly detection:** Flags unmetered conveyance losses by comparing predicted and measured outflow.
- **Geotechnical stress detection:** Flags abnormal phreatic head spikes that may indicate internal piping or geomembrane failure.
- **Composite risk scoring:** Combines likelihood and consequence of failure into a single score per reach.
- **Interactive GIS dashboard:** Map view, time-series charts and risk tiers for maintenance planning.
- **Standards-based spatial data:** GeoJSON FeatureCollections, a PostGIS DDL schema and EPSG:4326 (WGS-84) coordinates.

---

## Screenshots

> Place image files in `docs/screenshots/` and update the paths below.

### 1. Dashboard Overview

Main landing view showing the canal corridor, summary indicators and navigation.

<img width="1897" height="902" alt="image" src="https://github.com/user-attachments/assets/e4b01e1f-c199-41b1-b7e4-913dbe8c0ff4" />

### 2. GIS Risk Map

Canal reaches on the map, colour-coded by risk tier.

<img width="752" height="595" alt="image" src="https://github.com/user-attachments/assets/8050d0fc-c259-4681-9a29-00cf30dcaa45" />

<img width="1892" height="891" alt="image" src="https://github.com/user-attachments/assets/10c3b7fb-fe10-4c2b-9a27-93aca43caafd" />



---

## System Architecture

```
Synthetic Data Generator  ->  Predictive Models  ->  Risk Engine  ->  GIS Dashboard
  (data_generator.py)       (predictive_model.py)                        (app.py)
```

1. **Data layer:** Generates canal geometry (GeoJSON) and sensor time series within the bounds set in `config.py`.
2. **Model layer:** Random Forest and Gradient Boosting regressors learn normal operation. Residuals between prediction and observation indicate anomalies.
3. **Risk layer:** Residuals are converted into likelihood and consequence indices, then into a composite risk score and tier.
4. **Presentation layer:** A Streamlit dashboard with a Folium/Leaflet map and Plotly charts.

## Technology Stack

| Area | Tools |
|---|---|
| Dashboard and GIS | Streamlit, Folium, Leaflet, streamlit-folium, Plotly |
| Machine learning and analytics | scikit-learn (Random Forest, Gradient Boosting), NumPy, Pandas, SciPy |
| Spatial data | GeoJSON, PostGIS DDL schema, EPSG:4326 (WGS-84) |
| Testing and capture | Playwright |

---

## Mathematical Formulation

### 1. Model Accuracy (RMSE)

The surrogate models learn physical equilibrium during normal operation. Accuracy is measured by root mean square error:

$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} \left(y_{\text{actual},i} - \hat{y}_{\text{pred},i}\right)^2}$$

- **Flow balance:** The residual $\Delta Q = \hat{Q}_{out} - Q_{out}$ quantifies unmetered conveyance deficits.
- **Pore pressure:** The residual $u - \hat{u}$ quantifies abnormal phreatic head spikes, which may indicate internal piping or geomembrane failure.

### 2. Composite Risk Score

$$\text{Risk Score} = P_f \times \frac{C_f}{5.0}$$

**Likelihood of failure** $P_f \in [0, 100]\%$:

$$P_f = 0.45 \cdot \text{SeepageLossIndex} + 0.35 \cdot \text{PorePressureStress} + 0.20 \cdot \text{SoilMoistureSaturation}$$

**Consequence of failure** $C_f \in [1.0, 5.0]$:

$$C_f = 0.40 \cdot \text{CropValue} + 0.40 \cdot \text{PopulationProximity} + 0.20 \cdot \text{CriticalInfrastructure}$$

### 3. Risk Tiers

| Tier | Score | Meaning |
|---|---|---|
| Low | 0-25 | Normal operating condition |
| Moderate | 25-50 | Routine advisory and scheduled surveillance |
| High | 50-75 | Structural stress detected; maintenance intervention recommended |
| Critical | 75-100 | Imminent embankment breach or high-volume piping void |

---

## Installation and Usage

### Prerequisites

- Python 3.9 or later
- pip

### 1. Install dependencies

```powershell
cd C:\Users\user\.gemini\antigravity\scratch\irrigence
py -m pip install -r requirements.txt
```

### 2. Launch the dashboard

```powershell
py -m streamlit run app.py --server.port 8501
```

Open <http://localhost:8501> in your browser.

## Automated Verification

The script below drives the dashboard in a headless browser and saves screenshots for verification.

```powershell
py interact_and_screenshot.py
```

---

## Project Structure

```
irrigence/
├── config.py                   # Coordinates, canal reach geometry, sensor bounds
├── data_generator.py           # Synthetic GIS and multi-sensor time-series engine
├── predictive_model.py         # Hydrodynamic and geotechnical ML models, RMSE tracking, risk engine
├── app.py                      # Streamlit operational GIS dashboard
├── interact_and_screenshot.py  # Playwright browser verification script
├── requirements.txt            # Python dependencies
├── docs/
│   └── screenshots/            # README images
└── README.md                   # Documentation
```

## Limitations and Future Work

- Telemetry is currently synthetic; models must be recalibrated once real IoT sensor data is available.
- Consequence factors (crop value, population proximity, critical infrastructure) are simulated inputs and should be replaced with field and census data.
- Planned: live sensor ingestion, a PostGIS-backed data store and alert notifications.

## Team

**Irrigence** · NESFIC 2026 applicant
Mridul Hazarika, Department of Civil Engineering, Jorhat Engineering College, Assam
