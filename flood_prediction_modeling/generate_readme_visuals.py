from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
BUNDLE_DIR = BASE_DIR / "data" / "collab_feature_bundle"
OUTPUT_DIR = BASE_DIR / "assets" / "readme"
MASTER_PATH = BUNDLE_DIR / "master_flood_feature_table.csv"
METRICS_PATH = BASE_DIR / "outputs" / "metrics.json"


def ensure_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_svg(path: Path, width: int, height: int, body: list[str]) -> None:
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs>',
        '<linearGradient id="bg" x1="0" x2="0" y1="0" y2="1">',
        '<stop offset="0%" stop-color="#0b1822"/>',
        '<stop offset="100%" stop-color="#102636"/>',
        '</linearGradient>',
        '<filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">',
        '<feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000000" flood-opacity="0.22"/>',
        '</filter>',
        '</defs>',
        f'<rect width="{width}" height="{height}" rx="24" fill="url(#bg)"/>',
        *body,
        '</svg>',
    ]
    path.write_text("\n".join(svg), encoding="utf-8")


def timeline_svg() -> None:
    width, height = 1400, 340
    steps = [
        ("1", "Procurement", "Identified credible USGS, CAMELS, and NASA sources."),
        ("2", "Download", "Loaded CAMELS attributes and USGS discharge records."),
        ("3", "Database", "Built a local SQLite hydrology dataset workspace."),
        ("4", "Model", "Trained a next-day discharge baseline model."),
        ("5", "Evaluation", "Generated metrics and multi-graph diagnostics."),
        ("6", "Collab", "Prepared notebook, bundle, and master CSV for Gemini/Colab."),
    ]
    xs = np.linspace(120, width - 120, len(steps))
    body = [
        '<text x="60" y="60" fill="#eef7fb" font-size="30" font-family="Segoe UI" font-weight="700">Project Timeline</text>',
        '<text x="60" y="92" fill="#9eb7c5" font-size="16" font-family="Segoe UI">Step-by-step progression from dataset sourcing to collaboration-ready assets.</text>',
        f'<line x1="{xs[0]}" y1="180" x2="{xs[-1]}" y2="180" stroke="#39d0ff" stroke-width="5" stroke-linecap="round"/>',
    ]
    for x, (idx, title, desc) in zip(xs, steps):
        body.extend(
            [
                f'<circle cx="{x:.1f}" cy="180" r="28" fill="#102b3d" stroke="#43f0c7" stroke-width="4" filter="url(#shadow)"/>',
                f'<text x="{x:.1f}" y="188" text-anchor="middle" fill="#eef7fb" font-size="18" font-family="Segoe UI" font-weight="700">{idx}</text>',
                f'<rect x="{x-85:.1f}" y="218" width="170" height="86" rx="16" fill="#0f2130" stroke="#27495e"/>',
                f'<text x="{x:.1f}" y="246" text-anchor="middle" fill="#43f0c7" font-size="16" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
                f'<text x="{x:.1f}" y="268" text-anchor="middle" fill="#bdd0db" font-size="12" font-family="Segoe UI">{esc(desc[:40])}</text>',
                f'<text x="{x:.1f}" y="284" text-anchor="middle" fill="#bdd0db" font-size="12" font-family="Segoe UI">{esc(desc[40:80])}</text>',
            ]
        )
    write_svg(OUTPUT_DIR / "timeline.svg", width, height, body)


def master_overview_svg(df: pd.DataFrame) -> None:
    width, height = 1400, 500
    groups = {
        "daily_discharge": len([c for c in df.columns if c.startswith("daily_")]),
        "iv_discharge": len([c for c in df.columns if c.startswith("iv_discharge")]),
        "gage_height": len([c for c in df.columns if c.startswith("iv_gage_height")]),
        "stage_discharge": len([c for c in df.columns if c.startswith("paired_")]),
        "site_meta": len([c for c in df.columns if c.startswith("site_")]),
        "ts_metadata": len([c for c in df.columns if c.startswith("tsmeta_")]),
        "camels_topo": len([c for c in df.columns if c.startswith("camels_topo_")]),
        "camels_climate": len([c for c in df.columns if c.startswith("camels_clim_")]),
        "camels_hydrology": len([c for c in df.columns if c.startswith("camels_hydro_")]),
        "rating_curve": len([c for c in df.columns if c.startswith("rating_")]),
        "nasa_imerg": len([c for c in df.columns if c.startswith("nasa_")]),
        "basin_geometry": len([c for c in df.columns if c.startswith("basin_")]),
    }
    max_val = max(groups.values())
    body = [
        '<text x="60" y="60" fill="#eef7fb" font-size="30" font-family="Segoe UI" font-weight="700">Master CSV Overview</text>',
        '<text x="60" y="92" fill="#9eb7c5" font-size="16" font-family="Segoe UI">Single-table view of the merged hydrology and basin feature space.</text>',
        '<rect x="60" y="120" width="300" height="120" rx="22" fill="#0f2130" stroke="#27495e"/>',
        f'<text x="90" y="165" fill="#43f0c7" font-size="18" font-family="Segoe UI" font-weight="700">Rows</text>',
        f'<text x="90" y="205" fill="#eef7fb" font-size="38" font-family="Segoe UI" font-weight="700">{len(df):,}</text>',
        '<rect x="390" y="120" width="300" height="120" rx="22" fill="#0f2130" stroke="#27495e"/>',
        f'<text x="420" y="165" fill="#39d0ff" font-size="18" font-family="Segoe UI" font-weight="700">Columns</text>',
        f'<text x="420" y="205" fill="#eef7fb" font-size="38" font-family="Segoe UI" font-weight="700">{len(df.columns):,}</text>',
        '<rect x="720" y="120" width="620" height="120" rx="22" fill="#0f2130" stroke="#27495e"/>',
        '<text x="750" y="165" fill="#ffb562" font-size="18" font-family="Segoe UI" font-weight="700">Core Use</text>',
        '<text x="750" y="198" fill="#eef7fb" font-size="20" font-family="Segoe UI">Daily target + IV summaries + site metadata + CAMELS attributes</text>',
    ]
    chart_x, chart_y, chart_w, chart_h = 80, 300, 1240, 150
    body.append(f'<rect x="{chart_x}" y="{chart_y}" width="{chart_w}" height="{chart_h}" rx="18" fill="#0f2130" stroke="#27495e"/>')
    bar_width = chart_w / len(groups) - 14
    x = chart_x + 18
    colors = ["#39d0ff", "#43f0c7", "#ffb562", "#ff7f87"]
    for i, (name, val) in enumerate(groups.items()):
        h = (val / max_val) * 92 if max_val else 0
        y = chart_y + 112 - h
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{h:.1f}" rx="8" fill="{colors[i % len(colors)]}"/>')
        body.append(f'<text x="{x + bar_width/2:.1f}" y="{chart_y + 132}" text-anchor="middle" fill="#c9d9e2" font-size="10" font-family="Segoe UI">{esc(name.replace("_", " "))}</text>')
        body.append(f'<text x="{x + bar_width/2:.1f}" y="{y - 8:.1f}" text-anchor="middle" fill="#eef7fb" font-size="11" font-family="Segoe UI">{val}</text>')
        x += bar_width + 14
    write_svg(OUTPUT_DIR / "master_overview.svg", width, height, body)


def line_chart_svg(df: pd.DataFrame) -> None:
    width, height = 1400, 520
    sample = df.iloc[::max(1, len(df)//240)].copy()
    values = sample["daily_discharge_cfs"].astype(float).to_numpy()
    x_left, x_right, y_top, y_bottom = 70, width - 40, 120, height - 70
    plot_w, plot_h = x_right - x_left, y_bottom - y_top
    vmin, vmax = float(np.nanmin(values)), float(np.nanmax(values))
    def sx(i: int) -> float:
        return x_left + (i / max(1, len(sample)-1)) * plot_w
    def sy(v: float) -> float:
        return y_bottom - ((v - vmin) / (vmax - vmin or 1)) * plot_h
    pts = " ".join(f"{sx(i):.2f},{sy(v):.2f}" for i, v in enumerate(values))
    monthly = df.copy()
    monthly["date"] = pd.to_datetime(monthly["date"])
    monthly = monthly.set_index("date")["daily_discharge_cfs"].resample("ME").mean().reset_index()
    m_vals = monthly["daily_discharge_cfs"].astype(float).to_numpy()
    m_pts = " ".join(
        f"{x_left + (i / max(1, len(monthly)-1)) * plot_w:.2f},{sy(v):.2f}"
        for i, v in enumerate(m_vals)
    )
    body = [
        '<text x="60" y="60" fill="#eef7fb" font-size="30" font-family="Segoe UI" font-weight="700">Discharge Behavior</text>',
        '<text x="60" y="92" fill="#9eb7c5" font-size="16" font-family="Segoe UI">Long-term daily discharge with monthly mean trend overlay.</text>',
        f'<rect x="{x_left-20}" y="{y_top-20}" width="{plot_w+40}" height="{plot_h+40}" rx="20" fill="#0f2130" stroke="#27495e"/>',
    ]
    for i in range(5):
        y = y_top + (plot_h/4) * i
        body.append(f'<line x1="{x_left}" y1="{y:.1f}" x2="{x_right}" y2="{y:.1f}" stroke="#244255"/>')
    body += [
        f'<polyline fill="none" stroke="#39d0ff" stroke-width="2.2" points="{pts}"/>',
        f'<polyline fill="none" stroke="#43f0c7" stroke-width="3.2" points="{m_pts}"/>',
        f'<text x="{x_left}" y="{height-28}" fill="#c9d9e2" font-size="12" font-family="Segoe UI">{esc(str(df["date"].iloc[0]))}</text>',
        f'<text x="{width-145}" y="{height-28}" fill="#c9d9e2" font-size="12" font-family="Segoe UI">{esc(str(df["date"].iloc[-1]))}</text>',
        f'<text x="{width-280}" y="60" fill="#39d0ff" font-size="13" font-family="Segoe UI">Daily discharge</text>',
        f'<text x="{width-150}" y="60" fill="#43f0c7" font-size="13" font-family="Segoe UI">Monthly mean</text>',
    ]
    write_svg(OUTPUT_DIR / "discharge_overview.svg", width, height, body)


def stage_curve_svg(df: pd.DataFrame) -> None:
    width, height = 1000, 560
    pair_path = BUNDLE_DIR / "04_usgs_iv_stage_discharge_pairs.csv"
    if pair_path.exists():
        pairs = pd.read_csv(pair_path)
        pairs = pairs.rename(columns={"gage_height_ft": "paired_stage_mean", "discharge_cfs": "paired_discharge_mean"})
    else:
        pairs = df.dropna(subset=["paired_stage_mean", "paired_discharge_mean"]).copy()
        if pairs.empty:
            pairs = df.dropna(subset=["iv_gage_height_ft_mean", "iv_discharge_mean"]).copy()
            pairs = pairs.rename(columns={"iv_gage_height_ft_mean": "paired_stage_mean", "iv_discharge_mean": "paired_discharge_mean"})
    x_vals = pairs["paired_stage_mean"].astype(float).to_numpy()
    y_vals = pairs["paired_discharge_mean"].astype(float).to_numpy()
    x_min, x_max = float(np.nanmin(x_vals)), float(np.nanmax(x_vals))
    y_min, y_max = float(np.nanmin(y_vals)), float(np.nanmax(y_vals))
    left, right, top, bottom = 90, width - 50, 100, height - 70
    plot_w, plot_h = right - left, bottom - top
    def sx(v: float) -> float:
        return left + ((v - x_min) / (x_max - x_min or 1)) * plot_w
    def sy(v: float) -> float:
        return bottom - ((v - y_min) / (y_max - y_min or 1)) * plot_h
    body = [
        '<text x="60" y="60" fill="#eef7fb" font-size="30" font-family="Segoe UI" font-weight="700">Stage-Discharge Relationship</text>',
        '<text x="60" y="92" fill="#9eb7c5" font-size="16" font-family="Segoe UI">Observed paired water level and discharge values for the target gauge.</text>',
        f'<rect x="{left-24}" y="{top-24}" width="{plot_w+48}" height="{plot_h+48}" rx="20" fill="#0f2130" stroke="#27495e"/>',
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#4a6575"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#4a6575"/>',
    ]
    for xv, yv in zip(x_vals, y_vals):
        body.append(f'<circle cx="{sx(xv):.2f}" cy="{sy(yv):.2f}" r="3.4" fill="#ffb562" opacity="0.72"/>')
    body += [
        f'<text x="{width/2:.1f}" y="{height-18}" text-anchor="middle" fill="#c9d9e2" font-size="13" font-family="Segoe UI">Gage height (ft)</text>',
        f'<text x="24" y="{height/2:.1f}" transform="rotate(-90 24 {height/2:.1f})" fill="#c9d9e2" font-size="13" font-family="Segoe UI">Discharge (cfs)</text>',
    ]
    write_svg(OUTPUT_DIR / "stage_discharge_curve.svg", width, height, body)


def attribute_board_svg(df: pd.DataFrame) -> None:
    width, height = 1400, 620
    row = df.iloc[0]
    topo = {
        "Elevation": float(row["camels_topo_elev_mean"]),
        "Slope": float(row["camels_topo_slope_mean"]),
        "Area": float(row["camels_topo_area_gages2"]),
    }
    clim = {
        "Precip": float(row["camels_clim_p_mean"]),
        "PET": float(row["camels_clim_pet_mean"]),
        "SnowFrac": float(row["camels_clim_frac_snow"]),
        "Aridity": float(row["camels_clim_aridity"]),
    }
    hydro = {
        "Q mean": float(row["camels_hydro_q_mean"]),
        "Runoff": float(row["camels_hydro_runoff_ratio"]),
        "Baseflow": float(row["camels_hydro_baseflow_index"]),
        "Q95": float(row["camels_hydro_q95"]),
    }

    def group_block(x: int, y: int, title: str, data: dict[str, float], color: str) -> list[str]:
        block = [
            f'<rect x="{x}" y="{y}" width="390" height="230" rx="22" fill="#0f2130" stroke="#27495e"/>',
            f'<text x="{x+28}" y="{y+40}" fill="{color}" font-size="22" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        ]
        vals = list(data.values())
        vmax = max(vals) or 1
        bx = x + 28
        for i, (k, v) in enumerate(data.items()):
            yy = y + 78 + i * 34
            w = (v / vmax) * 220
            block.append(f'<text x="{bx}" y="{yy}" fill="#c9d9e2" font-size="13" font-family="Segoe UI">{esc(k)}</text>')
            block.append(f'<rect x="{bx+110}" y="{yy-12}" width="230" height="16" rx="8" fill="#173244"/>')
            block.append(f'<rect x="{bx+110}" y="{yy-12}" width="{w:.1f}" height="16" rx="8" fill="{color}"/>')
            block.append(f'<text x="{bx+350}" y="{yy}" text-anchor="end" fill="#eef7fb" font-size="12" font-family="Segoe UI">{v:.2f}</text>')
        return block

    body = [
        '<text x="60" y="60" fill="#eef7fb" font-size="30" font-family="Segoe UI" font-weight="700">Static Basin Factors</text>',
        '<text x="60" y="92" fill="#9eb7c5" font-size="16" font-family="Segoe UI">Topography, climate, and hydrologic signatures extracted from CAMELS for the target basin.</text>',
        *group_block(60, 150, "Topography", topo, "#39d0ff"),
        *group_block(505, 150, "Climate", clim, "#43f0c7"),
        *group_block(950, 150, "Hydrology", hydro, "#ffb562"),
    ]
    write_svg(OUTPUT_DIR / "attribute_board.svg", width, height, body)


def generate() -> None:
    ensure_dir()
    df = pd.read_csv(MASTER_PATH)
    with METRICS_PATH.open("r", encoding="utf-8") as f:
        _ = json.load(f)
    timeline_svg()
    master_overview_svg(df)
    line_chart_svg(df)
    stage_curve_svg(df)
    attribute_board_svg(df)
    print(f"Generated README visuals in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate()
