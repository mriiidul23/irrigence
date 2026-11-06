"""
Task 3: Streamlit Operational GIS Dashboard for Irrigence Platform.
North East Seva First Innovation Challenge (NESFIC) 2026.
Digital Spatial Decision-Support System for Irrigation Canal Condition Monitoring (DPS 2).
"""

import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium

from config import (
    CANAL_SEGMENTS,
    MAP_CENTER_LAT,
    MAP_CENTER_LON,
    MAP_ZOOM_START,
    SENSOR_LIMITS,
    RISK_LEVELS
)
from data_generator import generate_synthetic_telemetry, get_canal_geojson
from predictive_model import CanalPredictiveEngine

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Irrigence | Canal Condition Monitoring",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0d47a1;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #546e7a;
        margin-top: 0px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 14px 18px;
        border-left: 5px solid #0d47a1;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #607d8b;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #263238;
    }
    .badge-low { background-color: #28a745; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .badge-mod { background-color: #ffc107; color: #212529; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .badge-high { background-color: #fd7e14; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .badge-critical { background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_trained_engine() -> CanalPredictiveEngine:
    """Initializes and trains the baseline surrogate ML model on normal operational history."""
    engine = CanalPredictiveEngine(random_state=42)
    # Generate 14 days of normal historical telemetry
    baseline_df = generate_synthetic_telemetry(days=14, scenario="normal", random_seed=42)
    engine.fit_baseline(baseline_df)
    return engine


# ---------------- SIDEBAR CONTROLS ----------------
st.sidebar.image("https://img.icons8.com/color/96/dam.png", width=64)
st.sidebar.title("Irrigence Control Panel")
st.sidebar.caption("NESFIC 2026 Simulation Environment")

st.sidebar.markdown("### 1. Simulation Scenario")
scenario_choice = st.sidebar.selectbox(
    "Operational Scenario",
    options=[
        "Normal Operations (Baseline)",
        "Embankment Seepage / Piping Defect (SEG-03 & 04)",
        "Monsoon High-Stage Surge",
        "Siltation & Backwater Choking (SEG-02)",
        "Custom Parameter Tuning"
    ],
    index=1
)

scenario_map = {
    "Normal Operations (Baseline)": "normal",
    "Embankment Seepage / Piping Defect (SEG-03 & 04)": "seepage_piping",
    "Monsoon High-Stage Surge": "monsoon_surge",
    "Siltation & Backwater Choking (SEG-02)": "siltation_choking",
    "Custom Parameter Tuning": "custom"
}
selected_scenario = scenario_map[scenario_choice]

st.sidebar.markdown("### 2. Live Parameter Tweaks")
inflow_scale = st.sidebar.slider(
    "Headworks Inflow Multiplier",
    min_value=0.5,
    max_value=1.6,
    value=1.0,
    step=0.05,
    help="Scales base diversion inflow at Kopili Headworks (32 m³/s baseline)."
)

rain_input = st.sidebar.slider(
    "Ambient Rainfall Intensity (mm/hr)",
    min_value=0.0,
    max_value=60.0,
    value=0.0 if selected_scenario != "monsoon_surge" else 25.0,
    step=2.5,
    help="Simulates localized monsoonal precipitation."
)

defect_severity = 0.0
if selected_scenario in ["seepage_piping", "custom"]:
    defect_severity = st.sidebar.slider(
        "Embankment Defect Severity",
        min_value=0.0,
        max_value=1.0,
        value=0.75,
        step=0.05,
        help="Simulates severity of piping/lining seepage void in canal bank."
    )

noise_level = st.sidebar.slider(
    "Sensor Measurement Noise (%)",
    min_value=1.0,
    max_value=15.0,
    value=4.0,
    step=0.5,
    help="Simulates environmental acoustic/radar instrument uncertainty."
) / 100.0

time_window_days = st.sidebar.select_slider(
    "Simulation Horizon (Days)",
    options=[3, 7, 14, 21],
    value=7
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Region:** Kopili-Jamuna Basin, Assam")
st.sidebar.markdown("**Network Length:** 42.5 km (6 Reaches)")
st.sidebar.markdown("**Model:** Random Forest + GBDT")


# ---------------- DATA GENERATION & ML INFERENCE ----------------
engine = get_trained_engine()

# Generate current scenario telemetry
with st.spinner("Simulating multi-sensor canal telemetry and running ML inference..."):
    current_telemetry = generate_synthetic_telemetry(
        days=time_window_days,
        freq_minutes=60,
        scenario=selected_scenario,
        inflow_scale=inflow_scale,
        rain_mm=rain_input,
        defect_severity=defect_severity,
        noise_factor=noise_level,
        random_seed=77
    )
    assessed_df, summary_metrics = engine.evaluate_telemetry(current_telemetry)

# Extract latest segment snapshots (last timestep)
latest_df = assessed_df.groupby("segment_id").last().reset_index()


# ---------------- DASHBOARD HEADER ----------------
st.markdown("<h1 class='main-title'>🌊 Irrigence: Digital Spatial Decision-Support Platform</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Real-Time Irrigation Canal Condition Monitoring, Water Balance Anomaly Detection & Geotechnical Risk Prediction | <b>NESFIC 2026</b></p>", unsafe_allow_html=True)


# ---------------- TOP KPI CARDS ----------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

avg_risk = latest_df["risk_score"].mean()
critical_count = (latest_df["risk_tier"] == "Critical").sum()
high_count = (latest_df["risk_tier"] == "High").sum()

# Conveyance efficiency = tail-end outflow / headworks inflow * 100
total_inflow = latest_df[latest_df["segment_id"] == "SEG-01"]["inflow_cms"].values[0]
tail_outflow = latest_df[latest_df["segment_id"] == "SEG-06"]["outflow_cms"].values[0]
conveyance_eff = (tail_outflow / max(total_inflow, 1.0)) * 100.0

with kpi1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Mean Network Risk</div>
        <div class="metric-value">{avg_risk:.1f} <span style="font-size:0.9rem; color:#888;">/ 100</span></div>
        <div style="margin-top:6px;">
            <span class="{'badge-critical' if avg_risk >= 75 else ('badge-high' if avg_risk >= 50 else ('badge-mod' if avg_risk >= 25 else 'badge-low'))}">
                {'CRITICAL' if avg_risk >= 75 else ('HIGH RISK' if avg_risk >= 50 else ('MODERATE' if avg_risk >= 25 else 'NORMAL'))}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {'#dc3545' if critical_count > 0 else '#28a745'};">
        <div class="metric-title">Critical Reaches</div>
        <div class="metric-value" style="color: {'#dc3545' if critical_count > 0 else '#28a745'};">{critical_count} <span style="font-size:0.9rem; color:#888;">/ 6 seg</span></div>
        <div style="font-size:0.8rem; color:#78909c; margin-top:6px;">High Risk Alerts: <b>{high_count}</b></div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #00897b;">
        <div class="metric-title">Conveyance Efficiency</div>
        <div class="metric-value">{conveyance_eff:.1f}%</div>
        <div style="font-size:0.8rem; color:#78909c; margin-top:6px;">Head: {total_inflow:.1f} m³/s | Tail: {tail_outflow:.1f} m³/s</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    flow_drift = summary_metrics["flow_rmse_drift_factor"]
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {'#dc3545' if flow_drift > 2.0 else '#1e88e5'};">
        <div class="metric-title">Flow Balance RMSE</div>
        <div class="metric-value">{summary_metrics['overall_flow_rmse']:.3f} <span style="font-size:0.8rem; color:#888;">m³/s</span></div>
        <div style="font-size:0.8rem; color:{'#d32f2f' if flow_drift > 2.0 else '#388e3c'}; margin-top:6px;">
            Baseline: {summary_metrics['baseline_flow_rmse']:.3f} (<b>{flow_drift}x</b> drift)
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    pore_drift = summary_metrics["pore_rmse_drift_factor"]
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: {'#dc3545' if pore_drift > 2.0 else '#673ab7'};">
        <div class="metric-title">Pore Pressure RMSE</div>
        <div class="metric-value">{summary_metrics['overall_pore_rmse']:.2f} <span style="font-size:0.8rem; color:#888;">kPa</span></div>
        <div style="font-size:0.8rem; color:{'#d32f2f' if pore_drift > 2.0 else '#388e3c'}; margin-top:6px;">
            Baseline: {summary_metrics['baseline_pore_rmse']:.2f} (<b>{pore_drift}x</b> drift)
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# ---------------- MAIN CONTENT: MAP & CHARTS ----------------
tab_map, tab_rmse, tab_telemetry, tab_spatial = st.tabs([
    "🗺️ Interactive GIS Risk Map",
    "📈 AI/ML Model Validation & RMSE Tracker",
    "🔬 Sensor Telemetry Deep Dive",
    "💾 PostGIS / GeoServer Data Export"
])


# ---------------- TAB 1: INTERACTIVE GIS RISK MAP ----------------
with tab_map:
    col_map, col_table = st.columns([7, 5])

    with col_map:
        st.subheader("Spatial Canal Condition & Risk Overview")
        st.caption("Leaflet / PostGIS compatible GIS layer. Canal segments are color-coded dynamically by calculated Risk Score.")

        # Build Folium Map
        m = folium.Map(
            location=[MAP_CENTER_LAT, MAP_CENTER_LON],
            zoom_start=MAP_ZOOM_START,
            tiles="CartoDB positron"
        )
        folium.TileLayer("OpenStreetMap").add_to(m)

        # Helper for color mapping
        def get_risk_color(score: float) -> str:
            if score < 25.0:
                return "#28a745"  # Green
            elif score < 50.0:
                return "#ffc107"  # Yellow
            elif score < 75.0:
                return "#fd7e14"  # Orange
            else:
                return "#dc3545"  # Red

        # Add canal segments to map
        for seg in CANAL_SEGMENTS:
            seg_id = seg["segment_id"]
            seg_data = latest_df[latest_df["segment_id"] == seg_id].iloc[0]
            risk_score = float(seg_data["risk_score"])
            color = get_risk_color(risk_score)
            weight = 7 if risk_score >= 50 else 5

            popup_html = f"""
            <div style="font-family: Arial, sans-serif; min-width: 210px; font-size: 13px;">
                <h4 style="margin: 0 0 6px 0; color: #0d47a1;">{seg_id}: {seg['name']}</h4>
                <b>Chainage:</b> RD {seg['chainage_start_km']} - {seg['chainage_end_km']} km ({seg['length_km']} km)<br>
                <b>Lining:</b> {seg['lining_type']}<br>
                <hr style="margin: 6px 0;">
                <b>Stage (Radar):</b> {seg_data['ultrasonic_stage_m']:.2f} m<br>
                <b>Velocity (ADV):</b> {seg_data['doppler_velocity_mps']:.2f} m/s<br>
                <b>Pore Pressure:</b> {seg_data['piezometer_pressure_kpa']:.1f} kPa<br>
                <b>Soil Moisture:</b> {seg_data['soil_moisture_pct']:.1f}%<br>
                <hr style="margin: 6px 0;">
                <b>Failure Likelihood (Pf):</b> {seg_data['likelihood_of_failure_pct']:.1f}%<br>
                <b>Failure Consequence (Cf):</b> {seg_data['consequence_of_failure']:.2f} / 5<br>
                <div style="margin-top: 6px; padding: 4px; background-color: {color}; color: white; text-align: center; font-weight: bold; border-radius: 4px;">
                    RISK SCORE: {risk_score:.1f} ({seg_data['risk_tier'].upper()})
                </div>
            </div>
            """

            # Draw segment polyline
            folium.PolyLine(
                locations=seg["path"],
                color=color,
                weight=weight,
                opacity=0.9,
                tooltip=f"{seg_id} | Risk Score: {risk_score:.1f} ({seg_data['risk_tier']})",
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)

            # Add sensor station icon marker at segment midpoint
            mid_pt = seg["path"][len(seg["path"]) // 2]
            icon_color = "red" if risk_score >= 75 else ("orange" if risk_score >= 50 else "blue")
            folium.CircleMarker(
                location=mid_pt,
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                tooltip=f"Sensor Station {seg_id}"
            ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, width="100%", height=480)

        # Legend
        st.markdown("""
        <div style="display:flex; justify-content:space-around; background:#f1f5f9; padding:8px; border-radius:6px; font-size:0.85rem;">
            <span><span style="color:#28a745; font-size:1.2rem;">■</span> Low Risk (0–25)</span>
            <span><span style="color:#ffc107; font-size:1.2rem;">■</span> Moderate (25–50)</span>
            <span><span style="color:#fd7e14; font-size:1.2rem;">■</span> High Risk (50–75)</span>
            <span><span style="color:#dc3545; font-size:1.2rem;">■</span> Critical Threat (75–100)</span>
        </div>
        """, unsafe_allow_html=True)

    with col_table:
        st.subheader("Reach Condition Scorecard")
        st.caption("Live assessment matrix generated by the AI/ML predictive model.")

        display_df = latest_df[[
            "segment_id", "risk_score", "risk_tier", "likelihood_of_failure_pct",
            "consequence_of_failure", "ultrasonic_stage_m", "piezometer_pressure_kpa"
        ]].copy()
        display_df.columns = [
            "Reach ID", "Risk Score", "Status", "Likelihood (Pf %)",
            "Consequence (Cf)", "Stage (m)", "Pore Press (kPa)"
        ]

        st.dataframe(
            display_df,
            column_config={
                "Risk Score": st.column_config.ProgressColumn(
                    "Risk Score",
                    help="Calculated composite Risk Score (0–100)",
                    format="%.1f",
                    min_value=0,
                    max_value=100
                ),
                "Likelihood (Pf %)": st.column_config.NumberColumn(
                    "Likelihood (Pf %)",
                    format="%.1f%%"
                ),
                "Stage (m)": st.column_config.NumberColumn(
                    "Stage (m)",
                    format="%.2f m"
                ),
                "Pore Press (kPa)": st.column_config.NumberColumn(
                    "Pore Press (kPa)",
                    format="%.1f kPa"
                )
            },
            use_container_width=True,
            height=340
        )

        st.info("""
        **Risk Formulation (DPS 2):**  
        $$\\text{Risk Score} = \\text{Likelihood of Failure } (P_f) \\times \\frac{\\text{Consequence of Failure } (C_f)}{5.0}$$
        - **$P_f$** is computed by the predictive engine from water balance residuals & pore pressure spikes.  
        - **$C_f$** accounts for downstream tea estates, paddy acreage, and village population proximity.
        """)


# ---------------- TAB 2: AI/ML MODEL VALIDATION & RMSE TRACKER ----------------
with tab_rmse:
    st.subheader("AI/ML Predictive Model Accuracy & Continuous RMSE Tracking")
    st.markdown("""
    The surrogate AI/ML model predicts expected hydrodynamic discharge ($Q_{pred}$) and pore pressure ($u_{pred}$) 
    under normal operating laws. **Root Mean Square Error (RMSE)** is tracked continuously against the simulated 
    historical baseline to validate model accuracy and immediately identify structural drift or seepage voids.
    """)

    rmse_col1, rmse_col2 = st.columns(2)

    with rmse_col1:
        # Segment-wise RMSE comparison bar chart
        seg_rmse_data = []
        for seg_id, mdict in summary_metrics["segment_metrics"].items():
            seg_rmse_data.append({
                "Segment": seg_id,
                "Observed Flow RMSE (m³/s)": mdict["flow_rmse"],
                "Baseline Flow RMSE (m³/s)": summary_metrics["baseline_flow_rmse"],
                "Observed Pore RMSE (kPa)": mdict["pore_rmse"],
                "Baseline Pore RMSE (kPa)": summary_metrics["baseline_pore_rmse"]
            })
        rmse_plot_df = pd.DataFrame(seg_rmse_data)

        fig_rmse_bar = go.Figure()
        fig_rmse_bar.add_trace(go.Bar(
            x=rmse_plot_df["Segment"],
            y=rmse_plot_df["Observed Flow RMSE (m³/s)"],
            name="Current Observed Flow RMSE",
            marker_color="#1e88e5"
        ))
        fig_rmse_bar.add_trace(go.Scatter(
            x=rmse_plot_df["Segment"],
            y=rmse_plot_df["Baseline Flow RMSE (m³/s)"],
            mode="lines+markers",
            name="Historical Baseline Flow RMSE",
            line=dict(color="#d32f2f", width=2, dash="dash")
        ))
        fig_rmse_bar.update_layout(
            title="<b>Flow Balance RMSE by Canal Reach</b> (Validation against Baseline)",
            xaxis_title="Canal Reach ID",
            yaxis_title="RMSE (m³/s)",
            template="plotly_white",
            height=340,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_rmse_bar, use_container_width=True)

    with rmse_col2:
        # Pore Pressure RMSE Bar Chart
        fig_pore_bar = go.Figure()
        fig_pore_bar.add_trace(go.Bar(
            x=rmse_plot_df["Segment"],
            y=rmse_plot_df["Observed Pore RMSE (kPa)"],
            name="Current Observed Pore RMSE",
            marker_color="#8e24aa"
        ))
        fig_pore_bar.add_trace(go.Scatter(
            x=rmse_plot_df["Segment"],
            y=rmse_plot_df["Baseline Pore RMSE (kPa)"],
            mode="lines+markers",
            name="Historical Baseline Pore RMSE",
            line=dict(color="#d32f2f", width=2, dash="dash")
        ))
        fig_pore_bar.update_layout(
            title="<b>Geotechnical Pore Pressure RMSE by Canal Reach</b>",
            xaxis_title="Canal Reach ID",
            yaxis_title="RMSE (kPa)",
            template="plotly_white",
            height=340,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_pore_bar, use_container_width=True)

    # Time-series validation tracking for a selected reach
    st.markdown("#### Real-time Residual Tracking: Baseline Expected vs. Actual Observed Telemetry")
    focus_seg = st.selectbox("Select Reach for Residual Analysis:", options=[s["segment_id"] for s in CANAL_SEGMENTS], index=2)
    seg_ts = assessed_df[assessed_df["segment_id"] == focus_seg].copy()

    fig_residuals = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=(
            f"<b>{focus_seg}: Hydrodynamic Outflow (Actual vs. ML Baseline Expected)</b>",
            f"<b>{focus_seg}: Piezometer Embankment Pressure (Actual vs. Expected)</b>"
        ),
        vertical_spacing=0.12
    )

    # Row 1: Flow
    fig_residuals.add_trace(
        go.Scatter(x=seg_ts["timestamp"], y=seg_ts["pred_outflow_cms"], name="ML Baseline Outflow", line=dict(color="#00acc1", dash="dash")),
        row=1, col=1
    )
    fig_residuals.add_trace(
        go.Scatter(x=seg_ts["timestamp"], y=seg_ts["outflow_cms"], name="Actual Sensor Outflow", line=dict(color="#1e88e5", width=2)),
        row=1, col=1
    )

    # Row 2: Pore pressure
    fig_residuals.add_trace(
        go.Scatter(x=seg_ts["timestamp"], y=seg_ts["pred_pore_pressure_kpa"], name="ML Baseline Pressure", line=dict(color="#ab47bc", dash="dash")),
        row=2, col=1
    )
    fig_residuals.add_trace(
        go.Scatter(x=seg_ts["timestamp"], y=seg_ts["piezometer_pressure_kpa"], name="Actual Sensor Pressure", line=dict(color="#e91e63", width=2)),
        row=2, col=1
    )

    fig_residuals.update_layout(height=420, template="plotly_white", showlegend=True)
    st.plotly_chart(fig_residuals, use_container_width=True)


# ---------------- TAB 3: SENSOR TELEMETRY DEEP DIVE ----------------
with tab_telemetry:
    st.subheader("Multi-Modal Sensor Telemetry & Geotechnical Thresholds")
    col_sel, col_stat = st.columns([4, 8])

    with col_sel:
        drill_seg = st.selectbox("Inspect Telemetry Reach:", options=[s["segment_id"] for s in CANAL_SEGMENTS], index=2, key="drill_seg")
        seg_meta = next(s for s in CANAL_SEGMENTS if s["segment_id"] == drill_seg)
        st.markdown(f"""
        **Reach Name:** {seg_meta['name']}  
        **Length:** {seg_meta['length_km']} km | **Bed Width:** {seg_meta['bed_width_m']} m  
        **Lining:** {seg_meta['lining_type']}  
        **Downstream Crops:** {seg_meta['crop_type']}  
        **Population Exposure:** {seg_meta['population_density']}  
        """)

    with col_stat:
        seg_sub = assessed_df[assessed_df["segment_id"] == drill_seg].copy()
        m_stage, m_vel, m_pore, m_soil = st.columns(4)
        m_stage.metric("Radar Stage", f"{seg_sub['ultrasonic_stage_m'].iloc[-1]:.2f} m", f"{seg_sub['ultrasonic_stage_m'].iloc[-1] - 2.2:.2f} m vs norm")
        m_vel.metric("Doppler Velocity", f"{seg_sub['doppler_velocity_mps'].iloc[-1]:.2f} m/s")
        m_pore.metric("Pore Pressure", f"{seg_sub['piezometer_pressure_kpa'].iloc[-1]:.1f} kPa", f"{seg_sub['pore_residual_kpa'].iloc[-1]:.1f} kPa excess")
        m_soil.metric("Soil Moisture", f"{seg_sub['soil_moisture_pct'].iloc[-1]:.1f}%")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        # Dual-axis Hydraulic: Stage & Velocity
        fig_hyd = make_subplots(specs=[[{"secondary_y": True}]])
        fig_hyd.add_trace(
            go.Scatter(x=seg_sub["timestamp"], y=seg_sub["ultrasonic_stage_m"], name="Radar Stage (m)", line=dict(color="#0288d1", width=2)),
            secondary_y=False
        )
        fig_hyd.add_trace(
            go.Scatter(x=seg_sub["timestamp"], y=seg_sub["doppler_velocity_mps"], name="Doppler Velocity (m/s)", line=dict(color="#26a69a", width=2, dash="dot")),
            secondary_y=True
        )
        fig_hyd.add_hline(y=SENSOR_LIMITS["stage_m"]["freeboard_alert"], line_dash="dash", line_color="#f57c00", annotation_text="Freeboard Alert", secondary_y=False)
        fig_hyd.update_layout(title="<b>Hydraulic Response (Radar Stage & ADV Flow Velocity)</b>", template="plotly_white", height=350)
        st.plotly_chart(fig_hyd, use_container_width=True)

    with col_chart2:
        # Dual-axis Geotechnical: Pore Pressure & Soil Moisture
        fig_geo = make_subplots(specs=[[{"secondary_y": True}]])
        fig_geo.add_trace(
            go.Scatter(x=seg_sub["timestamp"], y=seg_sub["piezometer_pressure_kpa"], name="Pore Pressure (kPa)", line=dict(color="#d81b60", width=2)),
            secondary_y=False
        )
        fig_geo.add_trace(
            go.Scatter(x=seg_sub["timestamp"], y=seg_sub["soil_moisture_pct"], name="Soil Moisture (%)", line=dict(color="#8d6e63", width=2, dash="dash")),
            secondary_y=True
        )
        fig_geo.add_hline(y=SENSOR_LIMITS["pore_pressure_kpa"]["advisory_threshold"], line_dash="dash", line_color="#f57c00", annotation_text="Piezometer Advisory", secondary_y=False)
        fig_geo.add_hline(y=SENSOR_LIMITS["pore_pressure_kpa"]["critical_threshold"], line_dash="solid", line_color="#d32f2f", annotation_text="Critical Threshold", secondary_y=False)
        fig_geo.update_layout(title="<b>Geotechnical Embankment Stability (Pore Pressure & Soil Moisture)</b>", template="plotly_white", height=350)
        st.plotly_chart(fig_geo, use_container_width=True)


# ---------------- TAB 4: POSTGIS / GEOSERVER DATA EXPORT ----------------
with tab_spatial:
    st.subheader("PostGIS & GeoServer Spatial Integration")
    st.markdown("""
    Irrigence is designed to integrate directly with enterprise spatial data backends 
    (**PostgreSQL with PostGIS extension** and **GeoServer WMS/WFS services**).
    """)

    geojson_data = get_canal_geojson()
    # Inject latest risk score and metrics into GeoJSON properties
    for feat in geojson_data["features"]:
        seg_id = feat["id"]
        row = latest_df[latest_df["segment_id"] == seg_id].iloc[0]
        feat["properties"]["risk_score"] = float(row["risk_score"])
        feat["properties"]["risk_tier"] = str(row["risk_tier"])
        feat["properties"]["likelihood_of_failure_pct"] = float(row["likelihood_of_failure_pct"])
        feat["properties"]["ultrasonic_stage_m"] = float(row["ultrasonic_stage_m"])
        feat["properties"]["piezometer_pressure_kpa"] = float(row["piezometer_pressure_kpa"])

    col_json, col_sql = st.columns(2)

    with col_json:
        st.markdown("#### PostGIS-Ready GeoJSON Payload")
        geojson_str = json.dumps(geojson_data, indent=2)
        st.download_button(
            label="📥 Download GeoJSON FeatureCollection",
            data=geojson_str,
            file_name="irrigence_canal_network.geojson",
            mime="application/geo+json"
        )
        st.code(geojson_str[:800] + "\n  ...\n}", language="json")

    with col_sql:
        st.markdown("#### PostGIS DDL & Ingestion Query")
        postgis_sql = """-- Irrigence PostGIS Schema Definition
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS canal_segments (
    segment_id VARCHAR(16) PRIMARY KEY,
    name VARCHAR(128),
    chainage_start_km NUMERIC(5,2),
    chainage_end_km NUMERIC(5,2),
    length_km NUMERIC(5,2),
    bed_width_m NUMERIC(4,2),
    lining_type VARCHAR(64),
    crop_value_factor NUMERIC(3,1),
    population_factor NUMERIC(3,1),
    geom GEOMETRY(LineString, 4326)
);

CREATE TABLE IF NOT EXISTS canal_telemetry_live (
    telemetry_id BIGSERIAL PRIMARY KEY,
    segment_id VARCHAR(16) REFERENCES canal_segments(segment_id),
    recorded_at TIMESTAMPTZ NOT NULL,
    ultrasonic_stage_m NUMERIC(5,2),
    doppler_velocity_mps NUMERIC(5,2),
    piezometer_pressure_kpa NUMERIC(6,2),
    soil_moisture_pct NUMERIC(5,2),
    inflow_cms NUMERIC(6,2),
    outflow_cms NUMERIC(6,2),
    rmse_flow NUMERIC(6,4),
    risk_score NUMERIC(5,2),
    risk_tier VARCHAR(16)
);

CREATE INDEX idx_canal_segments_geom ON canal_segments USING GIST(geom);
"""
        st.download_button(
            label="📥 Download PostGIS DDL Script (.sql)",
            data=postgis_sql,
            file_name="irrigence_postgis_schema.sql",
            mime="text/plain"
        )
        st.code(postgis_sql, language="sql")
