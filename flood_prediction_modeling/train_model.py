from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "flood_model.db"
OUTPUT_DIR = BASE_DIR / "outputs"


STATIC_COLUMNS = [
    "area_gages2",
    "elev_mean",
    "slope_mean",
    "p_mean",
    "frac_snow",
    "runoff_ratio",
    "baseflow_index",
]


def nse(obs: np.ndarray, pred: np.ndarray) -> float:
    denom = np.sum((obs - np.mean(obs)) ** 2)
    if denom == 0:
        return float("nan")
    return float(1 - np.sum((obs - pred) ** 2) / denom)


def rmse(obs: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((obs - pred) ** 2)))


def mae(obs: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean(np.abs(obs - pred)))


def create_features(flow_df: pd.DataFrame, static_row: pd.Series) -> pd.DataFrame:
    df = flow_df.copy()
    df = df.sort_values("date").reset_index(drop=True)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    for lag in (1, 2, 3, 7, 14):
        df[f"lag_{lag}"] = df["value"].shift(lag)

    df["roll_mean_3"] = df["value"].shift(1).rolling(3).mean()
    df["roll_mean_7"] = df["value"].shift(1).rolling(7).mean()
    df["target_next_day"] = df["value"].shift(-1)

    doy = df["date"].dt.dayofyear
    df["sin_doy"] = np.sin(2 * np.pi * doy / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * doy / 365.25)

    for col in STATIC_COLUMNS:
        if col in static_row.index:
            df[col] = pd.to_numeric(static_row[col], errors="coerce")

    df = df.dropna().reset_index(drop=True)
    return df


def fit_linear_regression(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x_design = np.column_stack([np.ones(len(x)), x])
    coefs, _, _, _ = np.linalg.lstsq(x_design, y, rcond=None)
    return coefs


def predict_linear_regression(x: np.ndarray, coefs: np.ndarray) -> np.ndarray:
    x_design = np.column_stack([np.ones(len(x)), x])
    return x_design @ coefs


def write_line_chart_svg(df: pd.DataFrame, path: Path, title: str) -> None:
    width, height = 1100, 420
    left, right, top, bottom = 70, 30, 40, 40
    plot_w = width - left - right
    plot_h = height - top - bottom

    actual = df["actual"].to_numpy()
    predicted = df["predicted"].to_numpy()
    all_values = np.concatenate([actual, predicted])
    y_min = float(np.nanmin(all_values))
    y_max = float(np.nanmax(all_values))
    if math.isclose(y_min, y_max):
        y_max = y_min + 1.0

    def scale_x(i: int) -> float:
        if len(df) == 1:
            return left + plot_w / 2
        return left + (i / (len(df) - 1)) * plot_w

    def scale_y(v: float) -> float:
        return top + (1 - (v - y_min) / (y_max - y_min)) * plot_h

    def polyline(values: np.ndarray, color: str) -> str:
        points = " ".join(
            f"{scale_x(i):.2f},{scale_y(float(v)):.2f}" for i, v in enumerate(values)
        )
        return f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{points}" />'

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff" />',
        f'<text x="{left}" y="24" font-size="18" font-family="Arial">{title}</text>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#333" />',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333" />',
        polyline(actual, "#1f77b4"),
        polyline(predicted, "#d62728"),
        f'<text x="{width-220}" y="24" font-size="12" font-family="Arial" fill="#1f77b4">Actual</text>',
        f'<text x="{width-150}" y="24" font-size="12" font-family="Arial" fill="#d62728">Predicted</text>',
        f'<text x="10" y="{top+10}" font-size="11" font-family="Arial">{y_max:.2f}</text>',
        f'<text x="10" y="{height-bottom}" font-size="11" font-family="Arial">{y_min:.2f}</text>',
        "</svg>",
    ]
    path.write_text("\n".join(svg), encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        flow_df = pd.read_sql_query(
            "SELECT site_id, date, value FROM usgs_daily_discharge ORDER BY date",
            conn,
            parse_dates=["date"],
        )
        site_id = flow_df["site_id"].iloc[0]
        static_df = pd.read_sql_query(
            "SELECT * FROM camels_attributes WHERE gauge_id = ?",
            conn,
            params=(site_id,),
        )

    if static_df.empty:
        raise RuntimeError(f"No CAMELS attributes found for site {site_id}")

    feature_df = create_features(flow_df, static_df.iloc[0])

    feature_columns = [
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_7",
        "lag_14",
        "roll_mean_3",
        "roll_mean_7",
        "sin_doy",
        "cos_doy",
    ] + [col for col in STATIC_COLUMNS if col in feature_df.columns]

    split_index = int(len(feature_df) * 0.8)
    train_df = feature_df.iloc[:split_index].copy()
    test_df = feature_df.iloc[split_index:].copy()

    x_train = train_df[feature_columns].to_numpy(dtype=float)
    y_train = train_df["target_next_day"].to_numpy(dtype=float)
    x_test = test_df[feature_columns].to_numpy(dtype=float)
    y_test = test_df["target_next_day"].to_numpy(dtype=float)

    coefs = fit_linear_regression(x_train, y_train)
    preds = predict_linear_regression(x_test, coefs)

    metrics = {
        "site_id": site_id,
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "rmse": rmse(y_test, preds),
        "mae": mae(y_test, preds),
        "nse": nse(y_test, preds),
        "feature_columns": feature_columns,
    }

    pred_df = pd.DataFrame(
        {
            "date": test_df["date"].dt.strftime("%Y-%m-%d"),
            "actual": y_test,
            "predicted": preds,
        }
    )

    pred_df.to_csv(OUTPUT_DIR / "predictions.csv", index=False)
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    write_line_chart_svg(pred_df.tail(180), OUTPUT_DIR / "prediction_plot.svg", f"USGS Site {site_id} Daily Discharge Forecast")

    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
