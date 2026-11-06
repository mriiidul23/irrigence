"""
Task 2: AI/ML Predictive Model for Canal Condition Monitoring.
Performs:
1. Baseline physical-statistical surrogate modeling (Random Forest & Gradient Boosting).
2. Calculation and tracking of Root Mean Square Error (RMSE) against simulated historical baseline.
3. Water balance anomaly detection (unmetered seepage / conveyance deficit).
4. Structural degradation risk scoring:
   Risk Score = Likelihood of Failure (Pf) * Consequence of Failure (Cf)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import root_mean_squared_error, mean_absolute_error, r2_score


class CanalPredictiveEngine:
    """
    Predictive maintenance and anomaly detection engine for irrigation canal condition monitoring.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        # Flow balance surrogate regressor
        self.flow_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            min_samples_split=4,
            random_state=random_state,
            n_jobs=-1
        )
        # Geotechnical pore pressure surrogate regressor
        self.pore_model = GradientBoostingRegressor(
            n_estimators=80,
            max_depth=4,
            learning_rate=0.08,
            random_state=random_state
        )
        self.is_fitted = False
        self.baseline_flow_rmse = 0.0
        self.baseline_pore_rmse = 0.0
        self.baseline_flow_r2 = 0.0
        self.baseline_pore_r2 = 0.0

    def fit_baseline(self, historical_df: pd.DataFrame) -> Dict[str, float]:
        """
        Trains the surrogate models on historical normal operational baseline data.
        Validates model accuracy using RMSE and R^2 against baseline.
        """
        # Flow prediction feature matrix
        X_flow = historical_df[[
            "inflow_cms",
            "ultrasonic_stage_m",
            "doppler_velocity_mps",
            "length_km",
            "rainfall_mm"
        ]].values
        y_flow = historical_df["outflow_cms"].values

        # Pore pressure prediction feature matrix
        X_pore = historical_df[[
            "ultrasonic_stage_m",
            "soil_moisture_pct",
            "rainfall_mm",
            "length_km"
        ]].values
        y_pore = historical_df["piezometer_pressure_kpa"].values

        # Train models
        self.flow_model.fit(X_flow, y_flow)
        self.pore_model.fit(X_pore, y_pore)
        self.is_fitted = True

        # Baseline predictions & accuracy metrics
        pred_flow_base = self.flow_model.predict(X_flow)
        pred_pore_base = self.pore_model.predict(X_pore)

        self.baseline_flow_rmse = float(root_mean_squared_error(y_flow, pred_flow_base))
        self.baseline_pore_rmse = float(root_mean_squared_error(y_pore, pred_pore_base))
        self.baseline_flow_r2 = float(r2_score(y_flow, pred_flow_base))
        self.baseline_pore_r2 = float(r2_score(y_pore, pred_pore_base))

        return {
            "flow_rmse_cms": round(self.baseline_flow_rmse, 4),
            "flow_r2": round(self.baseline_flow_r2, 4),
            "pore_rmse_kpa": round(self.baseline_pore_rmse, 4),
            "pore_r2": round(self.baseline_pore_r2, 4)
        }

    def evaluate_telemetry(self, current_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Evaluates real-time / scenario telemetry against historical baseline:
        - Calculates Flow & Pore Pressure RMSE against baseline.
        - Identifies hydrodynamic seepage deficits and pore pressure anomalies.
        - Calculates Likelihood of Failure (Pf) and Consequence of Failure (Cf).
        - Computes composite Risk Score: Risk = Pf * Cf.
        """
        if not self.is_fitted:
            raise RuntimeError("Engine must be fitted on baseline data prior to telemetry evaluation.")

        df = current_df.copy()

        # 1. Feature matrices
        X_flow = df[[
            "inflow_cms",
            "ultrasonic_stage_m",
            "doppler_velocity_mps",
            "length_km",
            "rainfall_mm"
        ]].values
        y_flow = df["outflow_cms"].values

        X_pore = df[[
            "ultrasonic_stage_m",
            "soil_moisture_pct",
            "rainfall_mm",
            "length_km"
        ]].values
        y_pore = df["piezometer_pressure_kpa"].values

        # 2. Baseline Model Inferences
        pred_flow = self.flow_model.predict(X_flow)
        pred_pore = self.pore_model.predict(X_pore)

        df["pred_outflow_cms"] = pred_flow
        df["pred_pore_pressure_kpa"] = pred_pore

        # Residuals
        # Flow deficit: expected outflow minus actual outflow (positive = unexplained water loss/seepage)
        df["flow_residual_cms"] = pred_flow - y_flow
        # Pore pressure excess: actual observed pressure minus expected hydrostatic baseline
        df["pore_residual_kpa"] = y_pore - pred_pore

        # 3. Overall RMSE Metrics calculation against baseline
        overall_flow_rmse = float(root_mean_squared_error(y_flow, pred_flow))
        overall_pore_rmse = float(root_mean_squared_error(y_pore, pred_pore))
        overall_flow_mae = float(mean_absolute_error(y_flow, pred_flow))
        overall_pore_mae = float(mean_absolute_error(y_pore, pred_pore))

        # 4. Segment-by-segment RMSE breakdown
        segment_metrics = {}
        for seg_id, group in df.groupby("segment_id"):
            seg_flow_rmse = float(root_mean_squared_error(group["outflow_cms"], group["pred_outflow_cms"]))
            seg_pore_rmse = float(root_mean_squared_error(group["piezometer_pressure_kpa"], group["pred_pore_pressure_kpa"]))
            segment_metrics[seg_id] = {
                "flow_rmse": round(seg_flow_rmse, 4),
                "pore_rmse": round(seg_pore_rmse, 4),
                "flow_rmse_ratio": round(seg_flow_rmse / max(self.baseline_flow_rmse, 1e-4), 2),
                "pore_rmse_ratio": round(seg_pore_rmse / max(self.baseline_pore_rmse, 1e-4), 2)
            }

        # 5. Likelihood of Failure (Pf) calculation [0.0 - 1.0]
        # Component A: Hydraulic Seepage Index (excess water loss relative to flow)
        flow_seepage_index = np.maximum(0.0, df["flow_residual_cms"]) / np.maximum(df["inflow_cms"] * 0.15, 1.0)
        flow_seepage_score = np.clip(flow_seepage_index * 1.5, 0.0, 1.0)

        # Component B: Geotechnical Stress Index (excess pore pressure against embankment stability)
        pore_excess_index = np.maximum(0.0, df["pore_residual_kpa"]) / 12.0
        pore_stress_score = np.clip(pore_excess_index, 0.0, 1.0)

        # Component C: Embankment Saturation Factor (soil moisture exceeding plastic limit)
        soil_sat_score = np.clip((df["soil_moisture_pct"] - 22.0) / 18.0, 0.0, 1.0)

        # Fused Likelihood of Failure: Pf in % (0 - 100)
        # Weights: 45% hydraulic loss, 35% pore pressure, 20% soil moisture
        likelihood_pct = (0.45 * flow_seepage_score + 0.35 * pore_stress_score + 0.20 * soil_sat_score) * 100.0
        df["likelihood_of_failure_pct"] = np.round(np.clip(likelihood_pct, 1.0, 99.5), 1)

        # 6. Consequence of Failure (Cf) calculation [1.0 - 5.0 scale]
        # Multi-factor exposure formula:
        # 40% High-value crops (Tea gardens, Boro/Sali paddy)
        # 40% Downstream rural population proximity & settlement density
        # 20% Critical infrastructure proximity (State Highway, Railway embankments)
        df["consequence_of_failure"] = np.round(
            0.40 * df["crop_value_factor"] +
            0.40 * df["population_proximity_factor"] +
            0.20 * df["infrastructure_proximity_factor"],
            2
        )

        # 7. Composite Risk Score Formula:
        # Risk Score = Likelihood of Failure * Consequence of Failure
        # Normalized onto a clean 0 to 100 index:
        # Risk = Pf (%) * (Cf / 5.0)
        raw_risk = df["likelihood_of_failure_pct"] * (df["consequence_of_failure"] / 5.0)
        df["risk_score"] = np.round(np.clip(raw_risk, 0.0, 100.0), 1)

        # Categorical Risk Tiers
        conditions = [
            df["risk_score"] < 25.0,
            (df["risk_score"] >= 25.0) & (df["risk_score"] < 50.0),
            (df["risk_score"] >= 50.0) & (df["risk_score"] < 75.0),
            df["risk_score"] >= 75.0
        ]
        tier_names = ["Low", "Moderate", "High", "Critical"]
        df["risk_tier"] = np.select(conditions, tier_names, default="Low")

        summary_metrics = {
            "overall_flow_rmse": round(overall_flow_rmse, 4),
            "overall_pore_rmse": round(overall_pore_rmse, 4),
            "overall_flow_mae": round(overall_flow_mae, 4),
            "overall_pore_mae": round(overall_pore_mae, 4),
            "baseline_flow_rmse": round(self.baseline_flow_rmse, 4),
            "baseline_pore_rmse": round(self.baseline_pore_rmse, 4),
            "flow_rmse_drift_factor": round(overall_flow_rmse / max(self.baseline_flow_rmse, 1e-4), 2),
            "pore_rmse_drift_factor": round(overall_pore_rmse / max(self.baseline_pore_rmse, 1e-4), 2),
            "segment_metrics": segment_metrics
        }

        return df, summary_metrics


if __name__ == "__main__":
    from data_generator import generate_synthetic_telemetry

    print("--- Testing CanalPredictiveEngine ---")
    print("1. Generating baseline training dataset...")
    base_df = generate_synthetic_telemetry(days=10, scenario="normal", random_seed=101)

    engine = CanalPredictiveEngine()
    metrics = engine.fit_baseline(base_df)
    print("Baseline Fit Validation Metrics:")
    print(metrics)

    print("\n2. Evaluating Anomaly Scenario (Embankment Seepage / Piping)...")
    anomaly_df = generate_synthetic_telemetry(days=3, scenario="seepage_piping", defect_severity=0.75, random_seed=202)
    assessed_df, summary = engine.evaluate_telemetry(anomaly_df)

    print(f"Overall Flow RMSE under anomaly: {summary['overall_flow_rmse']} cms (Baseline: {summary['baseline_flow_rmse']})")
    print(f"Overall Pore RMSE under anomaly: {summary['overall_pore_rmse']} kPa (Baseline: {summary['baseline_pore_rmse']})")
    print(f"Flow RMSE Drift Factor: {summary['flow_rmse_drift_factor']}x")

    latest_status = assessed_df.groupby("segment_id").last()[["segment_name", "risk_score", "risk_tier", "likelihood_of_failure_pct", "consequence_of_failure"]]
    print("\nSegment Latest Condition Assessment:")
    print(latest_status)
