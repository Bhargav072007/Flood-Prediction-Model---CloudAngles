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
        '<defs></defs>',
        f'<rect width="{width}" height="{height}" rx="24" fill="#ffffff"/>',
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
        '<text x="60" y="60" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">Project Timeline</text>',
        '<text x="60" y="92" fill="#4e6678" font-size="16" font-family="Segoe UI">Step-by-step progression from dataset sourcing to collaboration-ready assets.</text>',
        f'<line x1="{xs[0]}" y1="180" x2="{xs[-1]}" y2="180" stroke="#2b6cb0" stroke-width="5" stroke-linecap="round"/>',
    ]
    for x, (idx, title, desc) in zip(xs, steps):
        body.extend(
            [
                f'<circle cx="{x:.1f}" cy="180" r="28" fill="#ffffff" stroke="#2f855a" stroke-width="4"/>',
                f'<text x="{x:.1f}" y="188" text-anchor="middle" fill="#142433" font-size="18" font-family="Segoe UI" font-weight="700">{idx}</text>',
                f'<rect x="{x-85:.1f}" y="218" width="170" height="86" rx="16" fill="#f8fbfd" stroke="#c7d7e2"/>',
                f'<text x="{x:.1f}" y="246" text-anchor="middle" fill="#2f855a" font-size="16" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
                f'<text x="{x:.1f}" y="268" text-anchor="middle" fill="#4e6678" font-size="12" font-family="Segoe UI">{esc(desc[:40])}</text>',
                f'<text x="{x:.1f}" y="284" text-anchor="middle" fill="#4e6678" font-size="12" font-family="Segoe UI">{esc(desc[40:80])}</text>',
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
        '<text x="60" y="60" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">Master CSV Overview</text>',
        '<text x="60" y="92" fill="#4e6678" font-size="16" font-family="Segoe UI">Single-table view of the merged hydrology and basin feature space.</text>',
        '<rect x="60" y="120" width="300" height="120" rx="22" fill="#f8fbfd" stroke="#c7d7e2"/>',
        f'<text x="90" y="165" fill="#2f855a" font-size="18" font-family="Segoe UI" font-weight="700">Rows</text>',
        f'<text x="90" y="205" fill="#142433" font-size="38" font-family="Segoe UI" font-weight="700">{len(df):,}</text>',
        '<rect x="390" y="120" width="300" height="120" rx="22" fill="#f8fbfd" stroke="#c7d7e2"/>',
        f'<text x="420" y="165" fill="#2b6cb0" font-size="18" font-family="Segoe UI" font-weight="700">Columns</text>',
        f'<text x="420" y="205" fill="#142433" font-size="38" font-family="Segoe UI" font-weight="700">{len(df.columns):,}</text>',
        '<rect x="720" y="120" width="620" height="120" rx="22" fill="#f8fbfd" stroke="#c7d7e2"/>',
        '<text x="750" y="165" fill="#b7791f" font-size="18" font-family="Segoe UI" font-weight="700">Core Use</text>',
        '<text x="750" y="198" fill="#142433" font-size="20" font-family="Segoe UI">Daily target + IV summaries + site metadata + CAMELS attributes</text>',
    ]
    chart_x, chart_y, chart_w, chart_h = 80, 300, 1240, 150
    body.append(f'<rect x="{chart_x}" y="{chart_y}" width="{chart_w}" height="{chart_h}" rx="18" fill="#f8fbfd" stroke="#c7d7e2"/>')
    bar_width = chart_w / len(groups) - 14
    x = chart_x + 18
    colors = ["#39d0ff", "#43f0c7", "#ffb562", "#ff7f87"]
    for i, (name, val) in enumerate(groups.items()):
        h = (val / max_val) * 92 if max_val else 0
        y = chart_y + 112 - h
        body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{h:.1f}" rx="8" fill="{colors[i % len(colors)]}"/>')
        body.append(f'<text x="{x + bar_width/2:.1f}" y="{chart_y + 132}" text-anchor="middle" fill="#4e6678" font-size="10" font-family="Segoe UI">{esc(name.replace("_", " "))}</text>')
        body.append(f'<text x="{x + bar_width/2:.1f}" y="{y - 8:.1f}" text-anchor="middle" fill="#142433" font-size="11" font-family="Segoe UI">{val}</text>')
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
        '<text x="60" y="60" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">Discharge Behavior</text>',
        '<text x="60" y="92" fill="#4e6678" font-size="16" font-family="Segoe UI">Long-term daily discharge with monthly mean trend overlay.</text>',
        f'<rect x="{x_left-20}" y="{y_top-20}" width="{plot_w+40}" height="{plot_h+40}" rx="20" fill="#ffffff" stroke="#c7d7e2"/>',
    ]
    for i in range(5):
        y = y_top + (plot_h/4) * i
        body.append(f'<line x1="{x_left}" y1="{y:.1f}" x2="{x_right}" y2="{y:.1f}" stroke="#dbe6ee"/>')
    body += [
        f'<polyline fill="none" stroke="#39d0ff" stroke-width="2.2" points="{pts}"/>',
        f'<polyline fill="none" stroke="#43f0c7" stroke-width="3.2" points="{m_pts}"/>',
        f'<text x="{x_left}" y="{height-28}" fill="#4e6678" font-size="12" font-family="Segoe UI">{esc(str(df["date"].iloc[0]))}</text>',
        f'<text x="{width-145}" y="{height-28}" fill="#4e6678" font-size="12" font-family="Segoe UI">{esc(str(df["date"].iloc[-1]))}</text>',
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
        '<text x="60" y="60" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">Stage-Discharge Relationship</text>',
        '<text x="60" y="92" fill="#4e6678" font-size="16" font-family="Segoe UI">Observed paired water level and discharge values for the target gauge.</text>',
        f'<rect x="{left-24}" y="{top-24}" width="{plot_w+48}" height="{plot_h+48}" rx="20" fill="#ffffff" stroke="#c7d7e2"/>',
        f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#8ba0af"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#8ba0af"/>',
    ]
    for xv, yv in zip(x_vals, y_vals):
        body.append(f'<circle cx="{sx(xv):.2f}" cy="{sy(yv):.2f}" r="3.4" fill="#dd6b20" opacity="0.78"/>')
    body += [
        f'<text x="{width/2:.1f}" y="{height-18}" text-anchor="middle" fill="#4e6678" font-size="13" font-family="Segoe UI">Gage height (ft)</text>',
        f'<text x="24" y="{height/2:.1f}" transform="rotate(-90 24 {height/2:.1f})" fill="#4e6678" font-size="13" font-family="Segoe UI">Discharge (cfs)</text>',
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
            f'<rect x="{x}" y="{y}" width="390" height="230" rx="22" fill="#ffffff" stroke="#c7d7e2"/>',
            f'<text x="{x+28}" y="{y+40}" fill="{color}" font-size="22" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        ]
        vals = list(data.values())
        vmax = max(vals) or 1
        bx = x + 28
        for i, (k, v) in enumerate(data.items()):
            yy = y + 78 + i * 34
            w = (v / vmax) * 220
            block.append(f'<text x="{bx}" y="{yy}" fill="#4e6678" font-size="13" font-family="Segoe UI">{esc(k)}</text>')
            block.append(f'<rect x="{bx+110}" y="{yy-12}" width="230" height="16" rx="8" fill="#e8f0f5"/>')
            block.append(f'<rect x="{bx+110}" y="{yy-12}" width="{w:.1f}" height="16" rx="8" fill="{color}"/>')
            block.append(f'<text x="{bx+350}" y="{yy}" text-anchor="end" fill="#142433" font-size="12" font-family="Segoe UI">{v:.2f}</text>')
        return block

    body = [
        '<text x="60" y="60" fill="#eef7fb" font-size="30" font-family="Segoe UI" font-weight="700">Static Basin Factors</text>',
        '<text x="60" y="92" fill="#9eb7c5" font-size="16" font-family="Segoe UI">Topography, climate, and hydrologic signatures extracted from CAMELS for the target basin.</text>',
        *group_block(60, 150, "Topography", topo, "#39d0ff"),
        *group_block(505, 150, "Climate", clim, "#43f0c7"),
        *group_block(950, 150, "Hydrology", hydro, "#ffb562"),
    ]
    write_svg(OUTPUT_DIR / "attribute_board.svg", width, height, body)


def band_chart_svg(
    path: Path,
    title: str,
    subtitle: str,
    dates: pd.Series,
    mean_vals: np.ndarray,
    min_vals: np.ndarray,
    max_vals: np.ndarray,
    color: str,
    y_label: str,
) -> None:
    width, height = 1400, 520
    sample_idx = np.arange(0, len(mean_vals), max(1, len(mean_vals) // 220))
    mean_vals = mean_vals[sample_idx]
    min_vals = min_vals[sample_idx]
    max_vals = max_vals[sample_idx]
    dates = dates.iloc[sample_idx].reset_index(drop=True)
    left, right, top, bottom = 70, width - 40, 120, height - 70
    plot_w, plot_h = right - left, bottom - top
    all_vals = np.concatenate([mean_vals, min_vals, max_vals])
    vmin, vmax = float(np.nanmin(all_vals)), float(np.nanmax(all_vals))
    def sx(i: int) -> float:
        return left + (i / max(1, len(mean_vals)-1)) * plot_w
    def sy(v: float) -> float:
        return bottom - ((v - vmin) / (vmax - vmin or 1)) * plot_h
    area_points = []
    for i, v in enumerate(max_vals):
        area_points.append(f"{sx(i):.2f},{sy(v):.2f}")
    for i, v in reversed(list(enumerate(min_vals))):
        area_points.append(f"{sx(i):.2f},{sy(v):.2f}")
    mean_points = " ".join(f"{sx(i):.2f},{sy(v):.2f}" for i, v in enumerate(mean_vals))
    body = [
        f'<text x="60" y="60" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        f'<text x="60" y="92" fill="#4e6678" font-size="16" font-family="Segoe UI">{esc(subtitle)}</text>',
        f'<rect x="{left-20}" y="{top-20}" width="{plot_w+40}" height="{plot_h+40}" rx="20" fill="#ffffff" stroke="#c7d7e2"/>',
    ]
    for i in range(5):
        y = top + (plot_h / 4) * i
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#dbe6ee"/>')
    body += [
        f'<polygon points="{" ".join(area_points)}" fill="{color}" opacity="0.18"/>',
        f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{mean_points}"/>',
        f'<text x="{left}" y="{height-28}" fill="#4e6678" font-size="12" font-family="Segoe UI">{esc(str(dates.iloc[0])[:10])}</text>',
        f'<text x="{width-145}" y="{height-28}" fill="#4e6678" font-size="12" font-family="Segoe UI">{esc(str(dates.iloc[len(dates)-1])[:10])}</text>',
        f'<text x="24" y="{height/2:.1f}" transform="rotate(-90 24 {height/2:.1f})" fill="#4e6678" font-size="13" font-family="Segoe UI">{esc(y_label)}</text>',
        f'<text x="{width-230}" y="60" fill="{color}" font-size="13" font-family="Segoe UI">Mean with min/max band</text>',
    ]
    write_svg(path, width, height, body)


def card_svg(path: Path, title: str, subtitle: str, items: list[tuple[str, str]], accent: str = "#39d0ff") -> None:
    width, height = 1100, max(260, 120 + len(items) * 42)
    body = [
        f'<text x="50" y="56" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        f'<text x="50" y="88" fill="#4e6678" font-size="16" font-family="Segoe UI">{esc(subtitle)}</text>',
        f'<rect x="40" y="116" width="{width-80}" height="{height-146}" rx="22" fill="#ffffff" stroke="#c7d7e2"/>',
    ]
    y = 155
    for label, value in items:
        body += [
            f'<text x="70" y="{y}" fill="{accent}" font-size="15" font-family="Segoe UI" font-weight="700">{esc(label)}</text>',
            f'<text x="360" y="{y}" fill="#142433" font-size="14" font-family="Segoe UI">{esc(value)}</text>',
            f'<line x1="65" y1="{y+18}" x2="{width-65}" y2="{y+18}" stroke="#dbe6ee"/>',
        ]
        y += 40
    write_svg(path, width, height, body)


def simple_bar_svg(path: Path, title: str, subtitle: str, data: dict[str, float], color: str) -> None:
    width, height = 1200, 520
    items = list(data.items())
    max_v = max(v for _, v in items) or 1
    left, top = 70, 120
    bar_x = 330
    body = [
        f'<text x="60" y="60" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        f'<text x="60" y="92" fill="#4e6678" font-size="16" font-family="Segoe UI">{esc(subtitle)}</text>',
        f'<rect x="50" y="120" width="{width-100}" height="{height-170}" rx="20" fill="#ffffff" stroke="#c7d7e2"/>',
    ]
    y = top + 42
    for k, v in items:
        w = (v / max_v) * 730
        body += [
            f'<text x="{left}" y="{y}" fill="#4e6678" font-size="14" font-family="Segoe UI">{esc(k)}</text>',
            f'<rect x="{bar_x}" y="{y-13}" width="760" height="18" rx="9" fill="#e8f0f5"/>',
            f'<rect x="{bar_x}" y="{y-13}" width="{w:.1f}" height="18" rx="9" fill="{color}"/>',
            f'<text x="{bar_x+780}" y="{y}" text-anchor="end" fill="#142433" font-size="13" font-family="Segoe UI">{v:.3f}</text>',
        ]
        y += 48
    write_svg(path, width, height, body)


def polygon_svg(path: Path, title: str, subtitle: str, coords: list[list[float]]) -> None:
    width, height = 900, 620
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    def sx(x: float) -> float:
        return 100 + ((x - min_x) / (max_x - min_x or 1)) * 680
    def sy(y: float) -> float:
        return 520 - ((y - min_y) / (max_y - min_y or 1)) * 360
    pts = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in coords)
    body = [
        f'<text x="60" y="60" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        f'<text x="60" y="92" fill="#4e6678" font-size="16" font-family="Segoe UI">{esc(subtitle)}</text>',
        '<rect x="60" y="120" width="780" height="430" rx="22" fill="#ffffff" stroke="#c7d7e2"/>',
        f'<polygon points="{pts}" fill="#39d0ff" opacity="0.22" stroke="#2b6cb0" stroke-width="3"/>',
    ]
    write_svg(path, width, height, body)


def combined_prediction_svg(df: pd.DataFrame) -> None:
    width, height = 1300, 560
    boxes = [
        (80, 180, 280, 140, "Dynamic Signals", ["Daily discharge", "Instantaneous discharge", "Gage height", "Stage-discharge pairs"], "#39d0ff"),
        (500, 180, 280, 140, "Static Basin Factors", ["Topography", "Climate", "Hydrology", "Basin geometry"], "#43f0c7"),
        (920, 180, 280, 140, "Support Context", ["Site metadata", "TS metadata", "Rating curves", "NASA IMERG metadata"], "#ffb562"),
    ]
    body = [
        '<text x="60" y="60" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">Combined Flood-Prediction Stack</text>',
        '<text x="60" y="92" fill="#4e6678" font-size="16" font-family="Segoe UI">How all factor families combine into a stronger prediction workflow.</text>',
    ]
    for x, y, w, h, title, items, color in boxes:
        body += [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="#ffffff" stroke="#c7d7e2"/>',
            f'<text x="{x+24}" y="{y+36}" fill="{color}" font-size="20" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        ]
        yy = y + 64
        for item in items:
            body.append(f'<text x="{x+26}" y="{yy}" fill="#142433" font-size="14" font-family="Segoe UI">• {esc(item)}</text>')
            yy += 22
    body += [
        '<line x1="360" y1="250" x2="500" y2="250" stroke="#5d7a8d" stroke-width="4" marker-end="url(#arrow)"/>',
        '<line x1="780" y1="250" x2="920" y2="250" stroke="#5d7a8d" stroke-width="4" marker-end="url(#arrow)"/>',
        '<rect x="410" y="390" width="480" height="100" rx="26" fill="#edf5fb" stroke="#2b6cb0" stroke-width="2"/>',
        '<text x="650" y="428" text-anchor="middle" fill="#142433" font-size="24" font-family="Segoe UI" font-weight="700">Flood / High-Flow Prediction Layer</text>',
        '<text x="650" y="456" text-anchor="middle" fill="#4e6678" font-size="15" font-family="Segoe UI">Current baseline: next-day discharge forecast</text>',
        '<text x="650" y="478" text-anchor="middle" fill="#4e6678" font-size="15" font-family="Segoe UI">Next upgrade: rainfall-driven model with authenticated precipitation ingestion</text>',
    ]
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#5d7a8d"/></marker></defs>',
        '<rect width="100%" height="100%" rx="24" fill="#ffffff"/>',
        *body,
        '</svg>',
    ]
    (OUTPUT_DIR / "combined_prediction_stack.svg").write_text("\n".join(svg), encoding="utf-8")


def timeline_span_svg(path: Path, title: str, subtitle: str, start: str, end: str, accent: str = "#2b6cb0") -> None:
    width, height = 1100, 280
    body = [
        f'<text x="50" y="56" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        f'<text x="50" y="88" fill="#4e6678" font-size="16" font-family="Segoe UI">{esc(subtitle)}</text>',
        '<rect x="60" y="130" width="980" height="80" rx="18" fill="#ffffff" stroke="#c7d7e2"/>',
        f'<line x1="120" y1="170" x2="980" y2="170" stroke="{accent}" stroke-width="8" stroke-linecap="round"/>',
        f'<circle cx="120" cy="170" r="12" fill="{accent}"/>',
        f'<circle cx="980" cy="170" r="12" fill="{accent}"/>',
        f'<text x="120" y="232" text-anchor="middle" fill="#142433" font-size="14" font-family="Segoe UI">{esc(str(start)[:10])}</text>',
        f'<text x="980" y="232" text-anchor="middle" fill="#142433" font-size="14" font-family="Segoe UI">{esc(str(end)[:10])}</text>',
    ]
    write_svg(path, width, height, body)


def grouped_bars_svg(path: Path, title: str, subtitle: str, labels: list[str], values: list[float], color: str = "#2b6cb0") -> None:
    width, height = 1100, 480
    left, right, top, bottom = 80, 1040, 120, 400
    plot_h = bottom - top
    vmax = max(values) or 1
    bar_w = (right - left) / len(values) - 24
    body = [
        f'<text x="50" y="56" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">{esc(title)}</text>',
        f'<text x="50" y="88" fill="#4e6678" font-size="16" font-family="Segoe UI">{esc(subtitle)}</text>',
        f'<rect x="{left-20}" y="{top-20}" width="{right-left+40}" height="{plot_h+50}" rx="20" fill="#ffffff" stroke="#c7d7e2"/>',
    ]
    for i in range(5):
        y = top + (plot_h / 4) * i
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#dbe6ee"/>')
    x = left + 18
    for label, value in zip(labels, values):
        h = (value / vmax) * (plot_h - 18)
        y = bottom - h
        body += [
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="8" fill="{color}"/>',
            f'<text x="{x + bar_w/2:.1f}" y="{bottom + 24}" text-anchor="middle" fill="#4e6678" font-size="12" font-family="Segoe UI">{esc(label)}</text>',
            f'<text x="{x + bar_w/2:.1f}" y="{y - 8:.1f}" text-anchor="middle" fill="#142433" font-size="12" font-family="Segoe UI">{value:.0f}</text>',
        ]
        x += bar_w + 24
    write_svg(path, width, height, body)


def site_profile_svg(path: Path, row: pd.Series) -> None:
    width, height = 1100, 520
    numeric = {
        "Drain area": float(row["site_drain_area_va"]),
        "Altitude": float(row["site_alt_va"]),
        "Latitude": abs(float(row["site_dec_lat_va"])),
        "Longitude": abs(float(row["site_dec_long_va"])),
    }
    labels = list(numeric.keys())
    vals = list(numeric.values())
    vmax = max(vals) or 1
    body = [
        '<text x="50" y="56" fill="#142433" font-size="30" font-family="Segoe UI" font-weight="700">Factor 5: Site Metadata</text>',
        '<text x="50" y="88" fill="#4e6678" font-size="16" font-family="Segoe UI">Gauge profile shown as numeric site descriptors plus a location point.</text>',
        '<rect x="50" y="120" width="620" height="340" rx="20" fill="#ffffff" stroke="#c7d7e2"/>',
        '<rect x="720" y="120" width="320" height="340" rx="20" fill="#ffffff" stroke="#c7d7e2"/>',
    ]
    y = 170
    for label, value in numeric.items():
        w = (value / vmax) * 360
        body += [
            f'<text x="80" y="{y}" fill="#4e6678" font-size="14" font-family="Segoe UI">{esc(label)}</text>',
            f'<rect x="220" y="{y-12}" width="380" height="16" rx="8" fill="#e8f0f5"/>',
            f'<rect x="220" y="{y-12}" width="{w:.1f}" height="16" rx="8" fill="#2b6cb0"/>',
            f'<text x="615" y="{y}" text-anchor="end" fill="#142433" font-size="13" font-family="Segoe UI">{value:.2f}</text>',
        ]
        y += 58
    cx, cy = 880, 280
    body += [
        '<text x="880" y="156" text-anchor="middle" fill="#2f855a" font-size="18" font-family="Segoe UI" font-weight="700">Gauge Location</text>',
        '<rect x="760" y="190" width="240" height="180" rx="18" fill="#f8fbfd" stroke="#dbe6ee"/>',
        f'<circle cx="{cx}" cy="{cy}" r="58" fill="#edf5fb" stroke="#2b6cb0" stroke-width="2"/>',
        f'<circle cx="{cx + float(row["site_dec_long_va"]) * 0.35 + 20:.1f}" cy="{cy - float(row["site_dec_lat_va"]) * 0.35 + 20:.1f}" r="7" fill="#dd6b20"/>',
        f'<text x="880" y="396" text-anchor="middle" fill="#4e6678" font-size="13" font-family="Segoe UI">{esc(str(row["site_station_nm"]))}</text>',
    ]
    write_svg(path, width, height, body)


def generate_factor_family_visuals(df: pd.DataFrame) -> None:
    iv_path = BUNDLE_DIR / "02_usgs_iv_discharge.csv"
    stage_path = BUNDLE_DIR / "03_usgs_iv_gage_height.csv"
    if iv_path.exists():
        iv_raw = pd.read_csv(iv_path)
        iv_raw["date_time"] = pd.to_datetime(iv_raw["date_time"])
        iv = (
            iv_raw.assign(date=iv_raw["date_time"].dt.strftime("%Y-%m-%d"))
            .groupby("date")["value"]
            .agg(["mean", "min", "max"])
            .reset_index()
            .rename(columns={"mean": "iv_discharge_mean", "min": "iv_discharge_min", "max": "iv_discharge_max"})
        )
        iv["date"] = pd.to_datetime(iv["date"])
        band_chart_svg(
            OUTPUT_DIR / "factor_02_iv_discharge.svg",
            "Factor 2: Instantaneous Discharge",
            "Recent mean/min/max discharge summaries derived from the IV feed.",
            iv["date"],
            iv["iv_discharge_mean"].to_numpy(float),
            iv["iv_discharge_min"].to_numpy(float),
            iv["iv_discharge_max"].to_numpy(float),
            "#43f0c7",
            "Discharge (cfs)",
        )
    if stage_path.exists():
        stage_raw = pd.read_csv(stage_path)
        stage_raw["date_time"] = pd.to_datetime(stage_raw["date_time"])
        stage = (
            stage_raw.assign(date=stage_raw["date_time"].dt.strftime("%Y-%m-%d"))
            .groupby("date")["value"]
            .agg(["mean", "min", "max"])
            .reset_index()
            .rename(columns={"mean": "iv_gage_height_ft_mean", "min": "iv_gage_height_ft_min", "max": "iv_gage_height_ft_max"})
        )
        stage["date"] = pd.to_datetime(stage["date"])
        band_chart_svg(
            OUTPUT_DIR / "factor_03_gage_height.svg",
            "Factor 3: Gage Height / Stage",
            "Recent mean/min/max stage summaries from the USGS IV service.",
            stage["date"],
            stage["iv_gage_height_ft_mean"].to_numpy(float),
            stage["iv_gage_height_ft_min"].to_numpy(float),
            stage["iv_gage_height_ft_max"].to_numpy(float),
            "#ffb562",
            "Gage height (ft)",
        )
    row = df.iloc[0]
    site_profile_svg(OUTPUT_DIR / "factor_05_site_metadata.svg", row)
    timeline_span_svg(
        OUTPUT_DIR / "factor_06_ts_metadata.svg",
        "Factor 6: Time-Series Metadata",
        "Begin/end temporal coverage of the primary discharge time series.",
        str(row["tsmeta_begin"]),
        str(row["tsmeta_end"]),
        "#2f855a",
    )
    topo = {"Elevation": float(row["camels_topo_elev_mean"]), "Slope": float(row["camels_topo_slope_mean"]), "Area": float(row["camels_topo_area_gages2"])}
    simple_bar_svg(OUTPUT_DIR / "factor_07_topography.svg", "Factor 7: CAMELS Topography", "Static terrain descriptors for the basin.", topo, "#39d0ff")
    clim = {
        "Mean precip": float(row["camels_clim_p_mean"]),
        "Mean PET": float(row["camels_clim_pet_mean"]),
        "Snow fraction": float(row["camels_clim_frac_snow"]),
        "Aridity": float(row["camels_clim_aridity"]),
    }
    simple_bar_svg(OUTPUT_DIR / "factor_08_climate.svg", "Factor 8: CAMELS Climate", "Climatological basin descriptors used as context features.", clim, "#43f0c7")
    hydro = {
        "Q mean": float(row["camels_hydro_q_mean"]),
        "Runoff ratio": float(row["camels_hydro_runoff_ratio"]),
        "Baseflow index": float(row["camels_hydro_baseflow_index"]),
        "Q95": float(row["camels_hydro_q95"]),
    }
    simple_bar_svg(OUTPUT_DIR / "factor_09_hydrology.svg", "Factor 9: CAMELS Hydrology", "Hydrologic signature features derived from basin response behavior.", hydro, "#ffb562")
    rating_labels = [x.strip() for x in str(row.get("rating_curve_file_types", "")).split(",") if x.strip()]
    grouped_bars_svg(
        OUTPUT_DIR / "factor_10_rating_curves.svg",
        "Factor 10: Rating Curves",
        "Available rating-curve file types for the target site.",
        rating_labels,
        [1.0 for _ in rating_labels],
        "#dd6b20",
    )
    grouped_bars_svg(
        OUTPUT_DIR / "factor_11_nasa_imerg_metadata.svg",
        "Factor 11: NASA IMERG Metadata",
        "Granule-level metadata prepared for the precipitation ingestion path.",
        ["Granule count"],
        [float(row.get("nasa_imerg_granule_count", 0))],
        "#2b6cb0",
    )
    basin_geo = json.loads((BUNDLE_DIR / "08_usgs_upstream_basin.geojson").read_text(encoding="utf-8"))
    coords = basin_geo["features"][0]["geometry"]["coordinates"][0]
    polygon_svg(OUTPUT_DIR / "factor_12_basin_geometry.svg", "Factor 12: Basin Geometry", "Upstream basin polygon used to anchor catchment-level aggregation.", coords)
    combined_prediction_svg(df)


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
    generate_factor_family_visuals(df)
    print(f"Generated README visuals in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate()
