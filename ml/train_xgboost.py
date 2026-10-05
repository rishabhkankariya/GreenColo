#!/usr/bin/env python3
"""
GreenColo: XGBoost PUE & Workload Power Prediction Pipeline
Trains an XGBoost regression model on telemetry dataset
and serializes the trained model for serving via FastAPI.
"""

import os
import argparse
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

def train_pue_model(data_path: str = "ml/data/telemetry_dataset.csv", model_dir: str = "ml/models"):
    os.makedirs(model_dir, exist_ok=True)

    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}. Generating now...")
        from ml.dataset_generator import generate_telemetry_dataset
        generate_telemetry_dataset(num_samples=3500, output_path=data_path)

    df = pd.read_csv(data_path)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")

    feature_cols = [
        "hour_of_day",
        "day_of_week",
        "cpu_percent",
        "memory_percent",
        "ambient_temp_c"
    ]

    target_col = "pue"

    X = df[feature_cols]
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Training XGBoost Regressor for {target_col}...")
    model = xgb.XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )

    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\n--- Model Evaluation ---")
    print(f"Target : {target_col.upper()}")
    print(f"MAE    : {mae:.4f}")
    print(f"RMSE   : {rmse:.4f}")
    print(f"R²     : {r2:.4f}")
    print("------------------------\n")

    # Save model
    model_json_path = os.path.join(model_dir, "xgboost_pue_model.json")
    model_joblib_path = os.path.join(model_dir, "xgboost_pue_model.pkl")

    model.save_model(model_json_path)
    joblib.dump(model, model_joblib_path)

    print(f"Successfully saved model to:\n  - {model_json_path}\n  - {model_joblib_path}")

    # Feature Importance
    importance = model.feature_importances_
    for col, imp in zip(feature_cols, importance):
        print(f"Feature '{col:<18}': {imp:.4f}")

    return model

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="ml/data/telemetry_dataset.csv", help="Path to telemetry dataset")
    parser.add_argument("--out", type=str, default="ml/models", help="Destination folder for serialized models")
    args = parser.parse_args()

    train_pue_model(args.data, args.out)
