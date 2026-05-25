from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = BASE_DIR / "data" / "collab_feature_bundle"
OUTPUT_PATH = BUNDLE_DIR / "master_flood_feature_table.csv"


def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(BUNDLE_DIR / name)


def flatten_single_row(df: pd.DataFrame, prefix: str) -> dict:
    if df.empty:
        return {}
    row = df.iloc[0].to_dict()
    return {f"{prefix}{key}": value for key, value in row.items()}


def build_daily_base() -> pd.DataFrame:
    daily = load_csv("01_usgs_daily_discharge.csv").copy()
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    daily = daily.sort_values("date").reset_index(drop=True)
    daily = daily.rename(
        columns={
            "value": "daily_discharge_cfs",
            "unit": "daily_discharge_unit",
            "approval_status": "daily_discharge_approval_status",
            "qualifier": "daily_discharge_qualifier",
            "time_series_id": "daily_discharge_time_series_id",
        }
    )
    return daily


def build_iv_daily_summary(filename: str, value_column: str, prefix: str) -> pd.DataFrame:
    df = load_csv(filename).copy()
    df["date_time"] = pd.to_datetime(df["date_time"], errors="coerce")
    df["date"] = df["date_time"].dt.strftime("%Y-%m-%d")
    grouped = (
        df.groupby("date")[value_column]
        .agg(["mean", "min", "max", "std", "count"])
        .reset_index()
        .rename(
            columns={
                "mean": f"{prefix}_mean",
                "min": f"{prefix}_min",
                "max": f"{prefix}_max",
                "std": f"{prefix}_std",
                "count": f"{prefix}_count",
            }
        )
    )
    return grouped


def build_stage_discharge_summary() -> pd.DataFrame:
    df = load_csv("04_usgs_iv_stage_discharge_pairs.csv").copy()
    df["date_time"] = pd.to_datetime(df["date_time"], errors="coerce")
    df["date"] = df["date_time"].dt.strftime("%Y-%m-%d")
    grouped = (
        df.groupby("date")
        .agg(
            paired_obs_count=("discharge_cfs", "count"),
            paired_discharge_mean=("discharge_cfs", "mean"),
            paired_stage_mean=("gage_height_ft", "mean"),
            paired_stage_max=("gage_height_ft", "max"),
            paired_discharge_max=("discharge_cfs", "max"),
        )
        .reset_index()
    )
    return grouped


def parse_site_metadata() -> dict:
    site_df = load_csv("06_usgs_site_metadata.csv")
    return flatten_single_row(site_df, "site_")


def parse_ts_metadata() -> dict:
    ts_df = load_csv("05_usgs_time_series_metadata_discharge.csv")
    return flatten_single_row(ts_df, "tsmeta_")


def parse_camels_attributes() -> dict:
    attrs = {}
    attrs.update(flatten_single_row(load_csv("09_camels_topography_attributes.csv"), "camels_topo_"))
    attrs.update(flatten_single_row(load_csv("10_camels_climate_attributes.csv"), "camels_clim_"))
    attrs.update(flatten_single_row(load_csv("11_camels_hydrology_attributes.csv"), "camels_hydro_"))
    return attrs


def parse_rating_manifest() -> dict:
    ratings = load_csv("07_usgs_rating_curve_manifest.csv")
    result = {
        "rating_curve_file_count": int(len(ratings)),
        "rating_curve_file_types": ",".join(sorted(ratings["file_type"].dropna().astype(str).unique())),
        "rating_curve_item_ids": ",".join(ratings["item_id"].astype(str).tolist()),
    }
    return result


def parse_nasa_metadata() -> dict:
    nasa = load_csv("12_nasa_imerg_granule_metadata.csv")
    result = {
        "nasa_imerg_granule_count": int(len(nasa)),
    }
    if not nasa.empty:
        result["nasa_imerg_time_start_min"] = nasa["time_start"].min()
        result["nasa_imerg_time_end_max"] = nasa["time_end"].max()
        result["nasa_imerg_first_title"] = nasa["title"].iloc[0]
    return result


def parse_basin_geometry() -> dict:
    path = BUNDLE_DIR / "08_usgs_upstream_basin.geojson"
    payload = json.loads(path.read_text(encoding="utf-8"))
    feature_count = len(payload.get("features", []))
    return {
        "basin_feature_count": feature_count,
        "basin_geojson_file": path.name,
    }


def main() -> int:
    master = build_daily_base()

    iv_q = build_iv_daily_summary("02_usgs_iv_discharge.csv", "value", "iv_discharge")
    iv_stage = build_iv_daily_summary("03_usgs_iv_gage_height.csv", "value", "iv_gage_height_ft")
    pairs = build_stage_discharge_summary()

    master = master.merge(iv_q, on="date", how="left")
    master = master.merge(iv_stage, on="date", how="left")
    master = master.merge(pairs, on="date", how="left")

    static_factors = {}
    static_factors.update(parse_site_metadata())
    static_factors.update(parse_ts_metadata())
    static_factors.update(parse_camels_attributes())
    static_factors.update(parse_rating_manifest())
    static_factors.update(parse_nasa_metadata())
    static_factors.update(parse_basin_geometry())

    for key, value in static_factors.items():
        master[key] = value

    master.to_csv(OUTPUT_PATH, index=False)
    print(f"Created master feature CSV: {OUTPUT_PATH}")
    print(f"Rows: {len(master)}, Columns: {len(master.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
