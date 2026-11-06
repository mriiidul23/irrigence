# Irrigence: Digital Spatial Decision-Support Platform (DPS 2)
### North East Seva First Innovation Challenge (NESFIC) 2026
**Irrigation Canal Condition Monitoring, Water Balance Anomaly Detection & Geotechnical Risk Prediction**

---

##  Overview
**Irrigence** is a digital spatial decision-support system designed to monitor irrigation canal embankment integrity and hydraulic conveyance efficiency across regional gravity irrigation schemes in North East India (simulated for the Kopili-Jamuna canal corridor in Assam).

Because physical IoT sensors are still being procured, Irrigence features a comprehensive physics-grounded synthetic telemetry generator and an AI/ML predictive surrogate engine that detects seepage anomalies and calculates reach-by-reach failure risk in real time.

---

##  Architecture & Tech Stack

```
irrigence/
├── config.py                   # Geographic coordinates, canal reach geometry & sensor bounds
├── data_generator.py           # Task 1: Synthetic GIS & multi-sensor time-series engine
├── predictive_model.py         # Task 2: Hydrodynamic & geotechnical ML models, RMSE tracker & Risk engine
├── app.py                      # Task 3: Streamlit operational GIS dashboard
├── interact_and_screenshot.py  # Automated browser verification script (Playwright)
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

- **Frontend / GIS Dashboard:** Streamlit, Folium / Leaflet, Streamlit-Folium, Plotly Express & Graph Objects.
- **Machine Learning & Analytics:** Scikit-Learn (Random Forest Regressor, Gradient Boosting Regressor), NumPy, Pandas, SciPy.
- **Spatial Logic:** GeoJSON FeatureCollections, PostGIS DDL schema, EPSG:4326 WGS-84 coordinates.

---

##  Mathematical Formulations

### 1. Model Accuracy & Validation (RMSE)
The ML surrogate models learn the physical hydrodynamic and geotechnical equilibrium during normal operations:
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (y_{\text{actual}, i} - \hat{y}_{\text{pred}, i})^2}$$
- **Flow Balance RMSE:** Quantifies unmetered conveyance deficits $(\Delta Q = \hat{Q}_{out} - Q_{out})$.
- **Pore Pressure RMSE:** Quantifies abnormal phreatic head spikes $(u - \hat{u})$ that indicate internal embankment piping or geomembrane failure.

### 2. Composite Risk Score Formula (DPS 2)
$$\text{Risk Score} = \text{Likelihood of Failure } (P_f) \times \frac{\text{Consequence of Failure } (C_f)}{5.0}$$
- **Likelihood of Failure ($P_f \in [0, 100]\%$):**  
  $$P_f = 0.45 \cdot \text{SeepageLossIndex} + 0.35 \cdot \text{PorePressureStress} + 0.20 \cdot \text{SoilMoistureSaturation}$$
- **Consequence of Failure ($C_f \in [1.0, 5.0]$):**  
  $$C_f = 0.40 \cdot \text{CropValue} + 0.40 \cdot \text{PopulationProximity} + 0.20 \cdot \text{CriticalInfrastructure}$$

### 3. Risk Tiers
-  **Low Risk (0–25):** Normal operational condition.
-  **Moderate Risk (25–50):** Routine advisory / scheduled surveillance.
-  **High Risk (50–75):** Structural stress detected — maintenance intervention recommended.
-  **Critical Threat (75–100):** Imminent embankment breach or high-volume piping void.

---

## Running the Platform

1. **Activate Environment & Install Dependencies:**
   ```powershell
   cd C:\Users\user\.gemini\antigravity\scratch\irrigence
   py -m pip install -r requirements.txt
   ```

2. **Launch Streamlit Dashboard:**
   ```powershell
   py -m streamlit run app.py --server.port 8501
   ```
   Open your browser at `http://localhost:8501`.

3. **Run Autonomous Verification & Capture Screenshots:**
   ```powershell
   py interact_and_screenshot.py

   <img width="1907" height="912" alt="image" src="https://github.com/user-attachments/assets/27a1630f-1736-4e68-ba34-17bc62e4f512" />

   ```
