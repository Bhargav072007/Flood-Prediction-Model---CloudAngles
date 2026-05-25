from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "data" / "flood_model.db"


def load_camels_attributes() -> pd.DataFrame:
    name_df = pd.read_csv(RAW_DIR / "camels" / "camels_name.txt", sep=";")
    topo_df = pd.read_csv(RAW_DIR / "camels" / "camels_topo.txt", sep=";")
    clim_df = pd.read_csv(RAW_DIR / "camels" / "camels_clim.txt", sep=";")
    hydro_df = pd.read_csv(RAW_DIR / "camels" / "camels_hydro.txt", sep=";")

    merged = name_df.merge(topo_df, on="gauge_id", how="left")
    merged = merged.merge(clim_df, on="gauge_id", how="left")
    merged = merged.merge(hydro_df, on="gauge_id", how="left")
    merged["gauge_id"] = merged["gauge_id"].astype(str).str.zfill(8)
    return merged


def load_usgs() -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / "usgs" / "daily_discharge.csv")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["site_id"] = df["site_id"].astype(str).str.zfill(8)
    return df


def load_nasa() -> tuple[pd.DataFrame, dict]:
    granules = pd.read_csv(RAW_DIR / "nasa" / "imerg_granules.csv")
    attempt = json.loads((RAW_DIR / "nasa" / "imerg_download_attempt.json").read_text())
    return granules, attempt


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    camels = load_camels_attributes()
    usgs = load_usgs()
    nasa, nasa_attempt = load_nasa()

    with sqlite3.connect(DB_PATH) as conn:
        pd.DataFrame(
            [
                {
                    "source_name": "CAMELS-US",
                    "provider": "NSF NCAR / USGS / DOI",
                    "notes": "Static attributes from Zenodo CAMELS release",
                },
                {
                    "source_name": "USGS Water Data API",
                    "provider": "USGS",
                    "notes": "Daily discharge via api.waterdata.usgs.gov",
                },
                {
                    "source_name": "NASA GPM IMERG Early V07",
                    "provider": "NASA GES DISC / CMR",
                    "notes": "Public granule metadata; direct file download unauthorized anonymously",
                },
            ]
        ).to_sql("dataset_source", conn, index=False, if_exists="replace")

        camels.to_sql("camels_attributes", conn, index=False, if_exists="replace")
        usgs.to_sql("usgs_daily_discharge", conn, index=False, if_exists="replace")
        nasa.to_sql("nasa_imerg_granules", conn, index=False, if_exists="replace")
        pd.DataFrame([nasa_attempt]).to_sql(
            "nasa_imerg_download_attempt", conn, index=False, if_exists="replace"
        )

    print(f"Built database: {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
