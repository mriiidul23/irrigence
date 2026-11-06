"""
Configuration and spatial topology for the Irrigence Canal Condition Monitoring Platform.
Targeted for North East Seva First Innovation Challenge (NESFIC) 2026.
Regional focus: Kopili - Jamuna Canal System, Brahmaputra Valley, Assam (approx 26.0°N, 92.9°E).
"""

from typing import Dict, Any, List

# Regional Map Center (Assam / Brahmaputra Valley)
MAP_CENTER_LAT: float = 26.065
MAP_CENTER_LON: float = 92.935
MAP_ZOOM_START: int = 11

# Canal Segments Topology (contiguous 5-8 km segments, ~42 km total network)
CANAL_SEGMENTS: List[Dict[str, Any]] = [
    {
        "segment_id": "SEG-01",
        "name": "Headworks Reach (Kopili Diversion)",
        "chainage_start_km": 0.0,
        "chainage_end_km": 6.8,
        "length_km": 6.8,
        "bed_width_m": 7.5,
        "side_slope": 1.5,
        "bed_slope": 0.00025,
        "lining_type": "Concrete Paver Lined",
        "start_coords": [26.152, 92.845],
        "end_coords": [26.128, 92.885],
        "path": [
            [26.1520, 92.8450],
            [26.1450, 92.8560],
            [26.1380, 92.8710],
            [26.1280, 92.8850]
        ],
        "crop_type": "Paddy & Agroforestry",
        "crop_value_factor": 3.2,
        "population_density": "Moderate (Village clusters, Kampur outskirts)",
        "population_proximity_factor": 3.0,
        "infrastructure_proximity_factor": 3.5,  # Near district link road
    },
    {
        "segment_id": "SEG-02",
        "name": "Upper Jamuna Transition Reach",
        "chainage_start_km": 6.8,
        "chainage_end_km": 14.2,
        "length_km": 7.4,
        "bed_width_m": 7.0,
        "side_slope": 1.5,
        "bed_slope": 0.00024,
        "lining_type": "Trapezoidal Stone Pitching",
        "start_coords": [26.128, 92.885],
        "end_coords": [26.095, 92.922],
        "path": [
            [26.1280, 92.8850],
            [26.1180, 92.8980],
            [26.1070, 92.9110],
            [26.0950, 92.9220]
        ],
        "crop_type": "Assam Orthodox Tea Estates & Paddy",
        "crop_value_factor": 4.5,
        "population_density": "High (Tea worker settlements)",
        "population_proximity_factor": 3.8,
        "infrastructure_proximity_factor": 4.0,  # Crosses Railway embankment
    },
    {
        "segment_id": "SEG-03",
        "name": "Middle Embankment & Aqueduct Reach",
        "chainage_start_km": 14.2,
        "chainage_end_km": 21.0,
        "length_km": 6.8,
        "bed_width_m": 6.5,
        "side_slope": 1.75,
        "bed_slope": 0.00022,
        "lining_type": "Compacted Earth with Geomembrane",
        "start_coords": [26.095, 92.922],
        "end_coords": [26.062, 92.952],
        "path": [
            [26.0950, 92.9220],
            [26.0840, 92.9340],
            [26.0730, 92.9440],
            [26.0620, 92.9520]
        ],
        "crop_type": "High-Value Organic Tea & Sali Rice",
        "crop_value_factor": 4.8,
        "population_density": "Very High (Dense settlements near Lanka town)",
        "population_proximity_factor": 4.6,
        "infrastructure_proximity_factor": 4.5,  # State Highway SH-19 culvert
    },
    {
        "segment_id": "SEG-04",
        "name": "Central Alluvial Floodplain Reach",
        "chainage_start_km": 21.0,
        "chainage_end_km": 28.5,
        "length_km": 7.5,
        "bed_width_m": 6.0,
        "side_slope": 2.0,
        "bed_slope": 0.00020,
        "lining_type": "Unlined Silt Embankment",
        "start_coords": [26.062, 92.952],
        "end_coords": [26.028, 92.981],
        "path": [
            [26.0620, 92.9520],
            [26.0500, 92.9630],
            [26.0390, 92.9720],
            [26.0280, 92.9810]
        ],
        "crop_type": "Boro Rice & Winter Mustard",
        "crop_value_factor": 3.6,
        "population_density": "Moderate-High (Rural agricultural villages)",
        "population_proximity_factor": 3.7,
        "infrastructure_proximity_factor": 3.0,
    },
    {
        "segment_id": "SEG-05",
        "name": "Lower Branching & Offtake Reach",
        "chainage_start_km": 28.5,
        "chainage_end_km": 35.5,
        "length_km": 7.0,
        "bed_width_m": 5.5,
        "side_slope": 1.75,
        "bed_slope": 0.00020,
        "lining_type": "Precast Concrete Slabs",
        "start_coords": [26.028, 92.981],
        "end_coords": [25.992, 93.010],
        "path": [
            [26.0280, 92.9810],
            [26.0150, 92.9910],
            [26.0040, 93.0010],
            [25.9920, 93.0100]
        ],
        "crop_type": "Jute, Pulses & Horticulture",
        "crop_value_factor": 3.0,
        "population_density": "Moderate (Semi-rural markets)",
        "population_proximity_factor": 2.8,
        "infrastructure_proximity_factor": 2.5,
    },
    {
        "segment_id": "SEG-06",
        "name": "Tail-End Distribution Reach",
        "chainage_start_km": 35.5,
        "chainage_end_km": 42.5,
        "length_km": 7.0,
        "bed_width_m": 5.0,
        "side_slope": 1.5,
        "bed_slope": 0.00018,
        "lining_type": "Unlined Earthen Canal",
        "start_coords": [25.992, 93.010],
        "end_coords": [25.955, 93.035],
        "path": [
            [25.9920, 93.0100],
            [25.9800, 93.0180],
            [25.9680, 93.0260],
            [25.9550, 93.0350]
        ],
        "crop_type": "Subsistence Paddy & Fisheries",
        "crop_value_factor": 2.5,
        "population_density": "Low-Moderate (Dispersed habitations)",
        "population_proximity_factor": 2.2,
        "infrastructure_proximity_factor": 2.0,
    }
]

# Baseline Hydraulic & Geotechnical Operational Bounds
SENSOR_LIMITS: Dict[str, Dict[str, float]] = {
    "stage_m": {
        "min_operational": 0.5,
        "design_normal": 2.2,
        "freeboard_alert": 2.9,
        "overtop_danger": 3.3
    },
    "velocity_mps": {
        "siltation_risk": 0.45,
        "design_normal": 1.15,
        "scour_alert": 2.1
    },
    "pore_pressure_kpa": {
        "normal_dry": 14.0,
        "normal_wet": 24.0,
        "advisory_threshold": 32.0,
        "critical_threshold": 42.0
    },
    "soil_moisture_pct": {
        "normal_dry": 18.0,
        "normal_wet": 28.0,
        "saturation_alert": 36.0,
        "liquefaction_danger": 44.0
    }
}

# Risk Thresholds
RISK_LEVELS: Dict[str, Dict[str, Any]] = {
    "Low": {"min": 0.0, "max": 25.0, "color": "#28a745", "label": "Normal Operational State"},
    "Moderate": {"min": 25.0, "max": 50.0, "color": "#ffc107", "label": "Advisory / Regular Watch"},
    "High": {"min": 50.0, "max": 75.0, "color": "#fd7e14", "label": "Elevated Risk - Inspect Reach"},
    "Critical": {"min": 75.0, "max": 100.0, "color": "#dc3545", "label": "Critical Breach / Failure Threat"}
}
