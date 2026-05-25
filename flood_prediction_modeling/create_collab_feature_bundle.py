from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


SITE_ID = "01013500"
SITE_USGS = f"USGS-{SITE_ID}"
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
BUNDLE_DIR = BASE_DIR / "data" / "collab_feature_bundle"


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


def ensure_dir() -> None:
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)


def save_daily_discharge() -> Path:
    source = RAW_DIR / "usgs" / "daily_discharge.csv"
    df = pd.read_csv(source)
    df = df[df["site_id"].astype(str).str.zfill(8) == SITE_ID].copy()
    out = BUNDLE_DIR / "01_usgs_daily_discharge.csv"
    df.to_csv(out, index=False)
    return out


def _parse_iv(parameter_code: str, filename: str) -> tuple[Path, pd.DataFrame]:
    url = (
        "https://waterservices.usgs.gov/nwis/iv/?format=json"
        f"&sites={SITE_ID}&parameterCd={parameter_code}&period=P7D"
    )
    payload = fetch_json(url)
    series = payload["value"]["timeSeries"][0]
    variable_name = series["variable"]["variableName"]
    unit = (
        series["variable"]
        .get("unit", {})
        .get("unitCode")
    )
    rows = []
    for item in series["values"][0]["value"]:
        rows.append(
            {
                "site_id": SITE_ID,
                "parameter_code": parameter_code,
                "variable_name": variable_name,
                "unit": unit,
                "date_time": item.get("dateTime"),
                "value": pd.to_numeric(item.get("value"), errors="coerce"),
                "qualifiers": ",".join(item.get("qualifiers", [])),
            }
        )
    df = pd.DataFrame(rows)
    out = BUNDLE_DIR / filename
    df.to_csv(out, index=False)
    return out, df


def save_stage_discharge_pairs(q_df: pd.DataFrame, stage_df: pd.DataFrame) -> Path:
    merged = q_df.merge(
        stage_df[["date_time", "value"]].rename(columns={"value": "gage_height_ft"}),
        on="date_time",
        how="inner",
    ).rename(columns={"value": "discharge_cfs"})
    out = BUNDLE_DIR / "04_usgs_iv_stage_discharge_pairs.csv"
    merged.to_csv(out, index=False)
    return out


def save_ts_metadata() -> Path:
    params = urllib.parse.urlencode(
        {
            "monitoring_location_id": SITE_USGS,
            "parameter_code": "00060",
        }
    )
    url = f"https://api.waterdata.usgs.gov/ogcapi/v0/collections/time-series-metadata/items?{params}"
    payload = fetch_json(url)
    rows = []
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        rows.append(props)
    df = pd.DataFrame(rows)
    out = BUNDLE_DIR / "05_usgs_time_series_metadata_discharge.csv"
    df.to_csv(out, index=False)
    return out


def save_site_metadata() -> Path:
    url = (
        "https://waterservices.usgs.gov/nwis/site/?format=rdb"
        f"&sites={SITE_ID}&siteOutput=expanded"
    )
    text = fetch_text(url)
    lines = [line for line in text.splitlines() if line and not line.startswith("#")]
    header = lines[0].split("\t")
    values = lines[2].split("\t") if len(lines) > 2 else []
    out = BUNDLE_DIR / "06_usgs_site_metadata.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow(values)
    return out


def save_rating_curves() -> tuple[Path, list[Path]]:
    filter_expr = urllib.parse.quote(f"monitoring_location_id = '{SITE_USGS}'")
    url = (
        "https://api.waterdata.usgs.gov/stac/v0/search?collections=ratings"
        f"&filter={filter_expr}&filter-lang=cql2-text&limit=20"
    )
    payload = fetch_json(url)
    manifest_rows = []
    raw_files = []
    for feature in payload.get("features", []):
        props = feature.get("properties", {})
        href = feature.get("assets", {}).get("data", {}).get("href")
        item_id = feature.get("id")
        file_text = fetch_text(href) if href else ""
        local_name = f"07_rating_{item_id}.rdb"
        local_path = BUNDLE_DIR / local_name
        local_path.write_text(file_text, encoding="utf-8")
        raw_files.append(local_path)
        manifest_rows.append(
            {
                "item_id": item_id,
                "datetime": props.get("datetime"),
                "file_type": props.get("file_type"),
                "agency_code": props.get("agency_code"),
                "monitoring_location_id": props.get("monitoring_location_id"),
                "monitoring_location_number": props.get("monitoring_location_number"),
                "asset_href": href,
                "local_file": local_name,
            }
        )
    manifest = pd.DataFrame(manifest_rows)
    manifest_path = BUNDLE_DIR / "07_usgs_rating_curve_manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    return manifest_path, raw_files


def save_upstream_basin() -> Path:
    url = f"https://api.water.usgs.gov/nldi/linked-data/nwissite/{SITE_USGS}/basin?f=json"
    payload = fetch_json(url)
    out = BUNDLE_DIR / "08_usgs_upstream_basin.geojson"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


def _save_camels_row(source_name: str, filename: str) -> Path:
    source = RAW_DIR / "camels" / source_name
    df = pd.read_csv(source, sep=";")
    row = df[df["gauge_id"].astype(str).str.zfill(8) == SITE_ID].copy()
    if "gauge_id" in row.columns:
        row["gauge_id"] = row["gauge_id"].astype(str).str.zfill(8)
    out = BUNDLE_DIR / filename
    row.to_csv(out, index=False)
    return out


def save_nasa_metadata() -> Path:
    source = RAW_DIR / "nasa" / "imerg_granules.csv"
    df = pd.read_csv(source)
    out = BUNDLE_DIR / "12_nasa_imerg_granule_metadata.csv"
    df.to_csv(out, index=False)
    return out


def save_manifest(files: list[tuple[str, str, str, str]]) -> Path:
    manifest = pd.DataFrame(
        files,
        columns=["layer_name", "local_file", "source", "notes"],
    )
    out = BUNDLE_DIR / "00_feature_bundle_manifest.csv"
    manifest.to_csv(out, index=False)
    return out


def main() -> int:
    ensure_dir()
    manifest_rows: list[tuple[str, str, str, str]] = []

    p1 = save_daily_discharge()
    manifest_rows.append(("USGS daily discharge", p1.name, "USGS Water Data API", "Daily discharge observations"))

    p2, q_df = _parse_iv("00060", "02_usgs_iv_discharge.csv")
    manifest_rows.append(("USGS instantaneous discharge", p2.name, "USGS IV service", "Recent 15-minute discharge values"))

    p3, stage_df = _parse_iv("00065", "03_usgs_iv_gage_height.csv")
    manifest_rows.append(("USGS instantaneous gage height", p3.name, "USGS IV service", "Recent 15-minute water level / stage values"))

    p4 = save_stage_discharge_pairs(q_df, stage_df)
    manifest_rows.append(("Observed stage-discharge pairs", p4.name, "Derived from USGS IV", "Paired stage/discharge points for curve analysis"))

    p5 = save_ts_metadata()
    manifest_rows.append(("USGS time-series metadata", p5.name, "USGS Water Data API", "Metadata for discharge time series"))

    p6 = save_site_metadata()
    manifest_rows.append(("USGS site metadata", p6.name, "USGS site service", "Station metadata including location and attributes"))

    p7, _ = save_rating_curves()
    manifest_rows.append(("USGS rating curve manifest", p7.name, "USGS STAC ratings", "Manifest for site-specific rating curve files"))

    p8 = save_upstream_basin()
    manifest_rows.append(("USGS upstream basin geometry", p8.name, "USGS NLDI", "Watershed polygon for the gauge"))

    p9 = _save_camels_row("camels_topo.txt", "09_camels_topography_attributes.csv")
    manifest_rows.append(("CAMELS topography attributes", p9.name, "CAMELS-US", "Static topographic basin features"))

    p10 = _save_camels_row("camels_clim.txt", "10_camels_climate_attributes.csv")
    manifest_rows.append(("CAMELS climate attributes", p10.name, "CAMELS-US", "Static climatology basin features"))

    p11 = _save_camels_row("camels_hydro.txt", "11_camels_hydrology_attributes.csv")
    manifest_rows.append(("CAMELS hydrology attributes", p11.name, "CAMELS-US", "Hydrologic signatures and basin metrics"))

    p12 = save_nasa_metadata()
    manifest_rows.append(("NASA IMERG granule metadata", p12.name, "NASA CMR / GES DISC", "Public metadata for precipitation granules"))

    save_manifest(manifest_rows)
    print(f"Created feature bundle at: {BUNDLE_DIR}")
    for row in manifest_rows:
        print("-", row[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
