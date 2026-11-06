"""
Task 1: Synthetic Telemetry and Spatial Data Generator for Irrigence Platform.
Generates multi-sensor time-series for canal reaches spaced 5-10 km apart:
- Ultrasonic / radar water level stage (m)
- Acoustic Doppler flow velocity (m/s)
- Piezometer pore pressure (kPa)
- Capacitance / TDR soil moisture (% volumetric)
Compatible with PostGIS / GeoServer standards and GeoJSON FeatureCollections.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from config import CANAL_SEGMENTS, SENSOR_LIMITS


def get_canal_geojson() -> Dict[str, Any]:
    """
    Generates a PostGIS / GeoServer compatible GeoJSON FeatureCollection
    representing the canal network segments with spatial and vulnerability attributes.
    """
    features = []
    for seg in CANAL_SEGMENTS:
        # GeoJSON uses [longitude, latitude] ordering
        geojson_coords = [[pt[1], pt[0]] for pt in seg["path"]]
        feature = {
            "type": "Feature",
            "id": seg["segment_id"],
            "geometry": {
                "type": "LineString",
                "coordinates": geojson_coords
            },
            "properties": {
                "segment_id": seg["segment_id"],
                "name": seg["name"],
                "chainage_start_km": seg["chainage_start_km"],
                "chainage_end_km": seg["chainage_end_km"],
                "length_km": seg["length_km"],
                "bed_width_m": seg["bed_width_m"],
                "lining_type": seg["lining_type"],
                "crop_type": seg["crop_type"],
                "crop_value_factor": seg["crop_value_factor"],
                "population_density": seg["population_density"],
                "population_proximity_factor": seg["population_proximity_factor"],
                "infrastructure_proximity_factor": seg["infrastructure_proximity_factor"]
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "name": "irrigence_canal_segments",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }


def compute_manning_discharge(stage: float, bed_width: float, side_slope: float, bed_slope: float, manning_n: float = 0.020) -> float:
    """
    Computes theoretical open-channel discharge Q (m^3/s) using Manning's equation
    for a trapezoidal cross-section:
    A = b * y + z * y^2
    P = b + 2 * y * sqrt(1 + z^2)
    R = A / P
    Q = (1/n) * A * R^(2/3) * S_0^(1/2)
    """
    if stage <= 0.05:
        return 0.0
    area = bed_width * stage + side_slope * (stage ** 2)
    wetted_perimeter = bed_width + 2.0 * stage * np.sqrt(1.0 + side_slope ** 2)
    hydraulic_radius = area / max(wetted_perimeter, 0.01)
    velocity = (1.0 / manning_n) * (hydraulic_radius ** (2.0 / 3.0)) * np.sqrt(max(bed_slope, 0.00005))
    discharge = area * velocity
    return float(discharge)


def generate_synthetic_telemetry(
    days: int = 14,
    freq_minutes: int = 60,
    scenario: str = "normal",
    inflow_scale: float = 1.0,
    rain_mm: float = 0.0,
    defect_severity: float = 0.0,
    noise_factor: float = 0.04,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic multi-sensor time-series for all canal segments.

    Parameters:
    - days: duration of historical/live series.
    - freq_minutes: telemetry logging frequency (default 60 mins).
    - scenario: 'normal', 'seepage_piping', 'monsoon_surge', 'siltation_choking', or 'custom'.
    - inflow_scale: multiplier for headworks discharge (default 1.0 = ~30 m3/s).
    - rain_mm: ambient rainfall intensity in mm/hr.
    - defect_severity: 0.0 to 1.0 defect intensity for seepage/piping.
    - noise_factor: relative Gaussian sensor noise scale.
    - random_seed: reproducibility seed.
    """
    np.random.seed(random_seed)
    n_steps = int((days * 24 * 60) / freq_minutes)
    start_time = datetime.now() - timedelta(days=days)
    timestamps = [start_time + timedelta(minutes=i * freq_minutes) for i in range(n_steps)]

    # Diurnal cycle (solar thermal + morning/evening irrigation demand cycles)
    hours = np.array([t.hour + t.minute / 60.0 for t in timestamps])
    diurnal_wave = 0.12 * np.sin(2.0 * np.pi * (hours - 8) / 24.0)

    # Base headworks inflow discharge Q_0 (m3/s)
    base_inflow_nominal = 32.0 * inflow_scale
    inflow_profile = base_inflow_nominal * (1.0 + diurnal_wave + np.random.normal(0, noise_factor, n_steps))
    inflow_profile = np.clip(inflow_profile, 8.0, 55.0)

    # Rainfall simulation (ambient + localized monsoon surge)
    if scenario == "monsoon_surge":
        surge_rain = 35.0 + 20.0 * np.sin(np.linspace(0, 3 * np.pi, n_steps))**2
        rain_profile = np.clip(surge_rain + rain_mm + np.random.exponential(5.0, n_steps), 0.0, 150.0)
    else:
        rain_profile = np.clip(rain_mm + np.random.exponential(1.5 if rain_mm > 0 else 0.1, n_steps), 0.0, 80.0)

    records = []

    # Cascade flow across segments 1 through 6
    curr_inflow = inflow_profile.copy()

    for seg_idx, seg in enumerate(CANAL_SEGMENTS):
        seg_id = seg["segment_id"]
        b = seg["bed_width_m"]
        z = seg["side_slope"]
        s0 = seg["bed_slope"]
        length_km = seg["length_km"]

        # Base Manning's n (lined vs unlined)
        base_n = 0.018 if "Lined" in seg["lining_type"] else 0.024

        # Scenario defect target (SEG-03 is middle embankment with geomembrane, SEG-04 unlined alluvial)
        is_defect_reach = False
        if scenario == "seepage_piping" and seg_id in ["SEG-03", "SEG-04"]:
            is_defect_reach = True
        elif scenario == "siltation_choking" and seg_id == "SEG-02":
            is_defect_reach = True
        elif scenario == "custom" and defect_severity > 0.05 and seg_id in ["SEG-03", "SEG-04"]:
            is_defect_reach = True

        # Calculate normal conveyance loss (evaporation + design canal percolation ~1.5% per 10km)
        design_loss_rate = (0.015 * (length_km / 10.0))
        normal_loss_cms = curr_inflow * design_loss_rate

        # Anomaly loss (unmetered seepage or piping void)
        if is_defect_reach and scenario in ["seepage_piping", "custom"]:
            severity = defect_severity if scenario == "custom" else 0.65
            seepage_anomaly_cms = curr_inflow * (0.08 + 0.18 * severity)
            # Ramp anomaly up in the second half of the time series
            ramp = np.linspace(0.2, 1.0, n_steps)
            anomaly_loss_cms = seepage_anomaly_cms * ramp
        else:
            anomaly_loss_cms = np.zeros(n_steps)

        total_conveyance_loss = normal_loss_cms + anomaly_loss_cms
        outflow_cms = np.clip(curr_inflow - total_conveyance_loss, 0.5, None)

        # Back-calculate stage h from discharge Q and Manning's formula:
        # Approximate invert relationship for trapezoidal section:
        avg_flow = (curr_inflow + outflow_cms) / 2.0

        # Hydraulic stage h (m)
        stage_nominal = (avg_flow * base_n / (b * np.sqrt(s0))) ** (3.0 / 5.0)

        # Siltation choking causes stage swell and reduced velocity
        if is_defect_reach and scenario == "siltation_choking":
            stage_nominal = stage_nominal * 1.35  # backwater swell
            effective_n = base_n * 1.6
        else:
            effective_n = base_n

        # Rainfall runoff addition to canal stage
        rain_stage_bump = (rain_profile / 1000.0) * 0.8
        radar_stage_m = stage_nominal + rain_stage_bump + np.random.normal(0, 0.02 + 0.05 * noise_factor, n_steps)
        radar_stage_m = np.clip(radar_stage_m, 0.3, 4.0)

        # Flow velocity via Acoustic Doppler Velocimeter (m/s)
        # v = Q / A
        wet_area = b * radar_stage_m + z * (radar_stage_m ** 2)
        wet_area = np.maximum(wet_area, 1.0)
        doppler_velocity_mps = avg_flow / wet_area

        if is_defect_reach and scenario == "siltation_choking":
            doppler_velocity_mps = doppler_velocity_mps * 0.65  # sluggish velocity

        doppler_velocity_mps = doppler_velocity_mps + np.random.normal(0, 0.03 * (1.0 + noise_factor), n_steps)
        doppler_velocity_mps = np.clip(doppler_velocity_mps, 0.2, 2.8)

        # Geotechnical telemetry:
        # 1. Piezometer Pore Pressure u (kPa)
        # Governed by hydrostatic phreatic head + soil saturation + defect seepage
        base_pore_pressure = 16.0 + 5.5 * (radar_stage_m - 1.5) + 0.12 * rain_profile

        if is_defect_reach and scenario in ["seepage_piping", "custom"]:
            severity = defect_severity if scenario == "custom" else 0.70
            # Elevated pore pressure indicates high hydraulic gradient and piping risk
            pore_pressure_spike = (12.0 + 18.0 * severity) * np.linspace(0.3, 1.0, n_steps)
            piezometer_pressure_kpa = base_pore_pressure + pore_pressure_spike
        elif scenario == "monsoon_surge":
            piezometer_pressure_kpa = base_pore_pressure + 0.25 * rain_profile
        else:
            piezometer_pressure_kpa = base_pore_pressure

        piezometer_pressure_kpa = piezometer_pressure_kpa + np.random.normal(0, 0.6 * (1.0 + noise_factor), n_steps)
        piezometer_pressure_kpa = np.clip(piezometer_pressure_kpa, 8.0, 65.0)

        # 2. Embankment Soil Moisture θ (% volumetric)
        # Correlated with rainfall, stage infiltration, and piping leaks
        base_soil_moisture = 20.0 + 3.0 * (radar_stage_m - 1.5) + 0.18 * rain_profile

        if is_defect_reach and scenario in ["seepage_piping", "custom"]:
            severity = defect_severity if scenario == "custom" else 0.70
            moisture_spike = (10.0 + 14.0 * severity) * np.linspace(0.4, 1.0, n_steps)
            soil_moisture_pct = base_soil_moisture + moisture_spike
        elif scenario == "monsoon_surge":
            soil_moisture_pct = base_soil_moisture + 0.3 * rain_profile
        else:
            soil_moisture_pct = base_soil_moisture

        soil_moisture_pct = soil_moisture_pct + np.random.normal(0, 0.5 * (1.0 + noise_factor), n_steps)
        soil_moisture_pct = np.clip(soil_moisture_pct, 12.0, 50.0)

        # Anomaly classification label
        anomaly_labels = []
        for i in range(n_steps):
            if is_defect_reach and scenario in ["seepage_piping", "custom"] and i > n_steps // 3:
                anomaly_labels.append("Seepage / Piping Defect")
            elif is_defect_reach and scenario == "siltation_choking":
                anomaly_labels.append("Siltation / Weed Choking")
            elif scenario == "monsoon_surge" and rain_profile[i] > 30.0:
                anomaly_labels.append("Monsoon High Stage")
            else:
                anomaly_labels.append("Normal")

        for i in range(n_steps):
            records.append({
                "timestamp": timestamps[i],
                "segment_id": seg_id,
                "segment_name": seg["name"],
                "chainage_start_km": seg["chainage_start_km"],
                "chainage_end_km": seg["chainage_end_km"],
                "length_km": length_km,
                "lining_type": seg["lining_type"],
                "crop_type": seg["crop_type"],
                "crop_value_factor": seg["crop_value_factor"],
                "population_proximity_factor": seg["population_proximity_factor"],
                "infrastructure_proximity_factor": seg["infrastructure_proximity_factor"],
                "inflow_cms": float(curr_inflow[i]),
                "outflow_cms": float(outflow_cms[i]),
                "conveyance_loss_cms": float(total_conveyance_loss[i]),
                "ultrasonic_stage_m": float(radar_stage_m[i]),
                "doppler_velocity_mps": float(doppler_velocity_mps[i]),
                "piezometer_pressure_kpa": float(piezometer_pressure_kpa[i]),
                "soil_moisture_pct": float(soil_moisture_pct[i]),
                "rainfall_mm": float(rain_profile[i]),
                "anomaly_label": anomaly_labels[i]
            })

        # Downstream cascading: next reach inflow is current reach outflow minus offtake diversion (~1 m3/s)
        curr_inflow = np.maximum(outflow_cms - 0.75, 2.0)

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    print("Testing synthetic telemetry generation...")
    df_test = generate_synthetic_telemetry(days=3, scenario="seepage_piping", defect_severity=0.7)
    print(f"Generated {len(df_test)} sensor records across {df_test['segment_id'].nunique()} segments.")
    print("Sample records:")
    print(df_test[["timestamp", "segment_id", "ultrasonic_stage_m", "doppler_velocity_mps", "piezometer_pressure_kpa", "soil_moisture_pct"]].head())
