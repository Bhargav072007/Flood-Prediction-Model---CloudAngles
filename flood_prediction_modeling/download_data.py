from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
CAMELS_DIR = RAW_DIR / "camels"
USGS_DIR = RAW_DIR / "usgs"
NASA_DIR = RAW_DIR / "nasa"

CAMELS_FILES = {
    "camels_name.txt": "https://zenodo.org/records/15529996/files/camels_name.txt?download=1",
    "camels_topo.txt": "https://zenodo.org/records/15529996/files/camels_topo.txt?download=1",
    "camels_clim.txt": "https://zenodo.org/records/15529996/files/camels_clim.txt?download=1",
    "camels_hydro.txt": "https://zenodo.org/records/15529996/files/camels_hydro.txt?download=1",
    "readme.txt": "https://zenodo.org/records/15529996/files/readme.txt?download=1",
}

DEFAULT_SITE = "01646500"
USGS_START = "2000-01-01"
USGS_END = "2024-12-31"

CMR_URL = (
    "https://cmr.earthdata.nasa.gov/search/granules.json?"
    "short_name=GPM_3IMERGDE&version=07&page_size=5"
)


def ensure_dirs() -> None:
    for path in (CAMELS_DIR, USGS_DIR, NASA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def download_text(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as response:
        dest.write_bytes(response.read())


def download_camels_files() -> None:
    for name, url in CAMELS_FILES.items():
        dest = CAMELS_DIR / name
        print(f"Downloading CAMELS file: {name}")
        download_text(url, dest)


def resolve_site_id() -> str:
    name_df = pd.read_csv(CAMELS_DIR / "camels_name.txt", sep=";")
    gauge_ids = name_df["gauge_id"].astype(str).str.zfill(8)
    if DEFAULT_SITE in set(gauge_ids):
        return DEFAULT_SITE
    return gauge_ids.iloc[0]


def fetch_usgs_daily(site_id: str) -> None:
    base_params = {
        "monitoring_location_id": f"USGS-{site_id}",
        "parameter_code": "00060",
        "time": f"{USGS_START}/{USGS_END}",
        "limit": "10000",
    }
    print(f"Downloading USGS daily discharge for site {site_id}")

    features = []
    offset = 0
    payload = None
    while True:
        params = urllib.parse.urlencode({**base_params, "offset": str(offset)})
        url = f"https://api.waterdata.usgs.gov/ogcapi/v0/collections/daily/items?{params}"
        with urllib.request.urlopen(url, timeout=60) as response:
            page_payload = json.load(response)

        page_features = page_payload.get("features", [])
        if payload is None:
            payload = page_payload
        features.extend(page_features)

        if len(page_features) < int(base_params["limit"]):
            break
        offset += len(page_features)

    rows = []
    for feature in features:
        props = feature.get("properties", {})
        rows.append(
            {
                "site_id": props.get("monitoring_location_id", "").replace("USGS-", ""),
                "date": props.get("time"),
                "value": props.get("value"),
                "unit": props.get("unit_of_measure"),
                "approval_status": props.get("approval_status"),
                "qualifier": ",".join(props.get("qualifier", []) or []),
                "parameter_code": props.get("parameter_code"),
                "time_series_id": props.get("time_series_id"),
            }
        )

    df = pd.DataFrame(rows)
    df = df.sort_values("date").reset_index(drop=True)
    df.to_csv(USGS_DIR / "daily_discharge.csv", index=False)
    (USGS_DIR / "daily_discharge_response.json").write_text(json.dumps(payload, indent=2))


def fetch_nasa_metadata() -> None:
    print("Downloading NASA IMERG granule metadata from CMR")
    with urllib.request.urlopen(CMR_URL, timeout=60) as response:
        payload = json.load(response)

    entries = payload.get("feed", {}).get("entry", [])
    metadata_rows = []
    direct_download_status = {
        "attempted": False,
        "status": None,
        "reason": None,
        "href": None,
    }

    if entries:
        first_links = entries[0].get("links", [])
        direct_link = next(
            (link.get("href") for link in first_links if link.get("title", "").startswith("Download ")),
            None,
        )
        direct_download_status["href"] = direct_link

        if direct_link:
            direct_download_status["attempted"] = True
            try:
                req = urllib.request.Request(direct_link, headers={"Range": "bytes=0-127"})
                with urllib.request.urlopen(req, timeout=60) as response:
                    _ = response.read(64)
                    direct_download_status["status"] = response.status
            except urllib.error.HTTPError as exc:
                direct_download_status["status"] = exc.code
                direct_download_status["reason"] = str(exc)
            except Exception as exc:  # noqa: BLE001
                direct_download_status["reason"] = repr(exc)

    for entry in entries:
        links = entry.get("links", [])
        download_link = next(
            (link.get("href") for link in links if link.get("title", "").startswith("Download ")),
            None,
        )
        opendap_link = next(
            (link.get("href") for link in links if "OPeNDAP request URL" in link.get("title", "")),
            None,
        )
        metadata_rows.append(
            {
                "title": entry.get("title"),
                "updated": entry.get("updated"),
                "time_start": entry.get("time_start"),
                "time_end": entry.get("time_end"),
                "download_link": download_link,
                "opendap_link": opendap_link,
            }
        )

    (NASA_DIR / "imerg_granules.json").write_text(json.dumps(payload, indent=2))
    pd.DataFrame(metadata_rows).to_csv(NASA_DIR / "imerg_granules.csv", index=False)
    (NASA_DIR / "imerg_download_attempt.json").write_text(
        json.dumps(direct_download_status, indent=2)
    )


def main() -> int:
    ensure_dirs()
    download_camels_files()
    site_id = resolve_site_id()
    fetch_usgs_daily(site_id)
    fetch_nasa_metadata()
    print(f"Complete. Using CAMELS/USGS site: {site_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
