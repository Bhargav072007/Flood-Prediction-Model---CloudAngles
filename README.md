# Flood Prediction Model - CloudAngles

This repository contains a working local flood-model baseline, the supporting dataset procurement notes, and a team dashboard for reviewing the results.

## What is included

- `flood_prediction_modeling/`
  - dataset downloader
  - SQLite database builder
  - baseline predictive model
  - team dashboard with animated evaluation charts
  - saved outputs and plots
- `flood_prediction_procurement/`
  - dataset shortlist
  - PostGIS schema
  - ER diagram

## Did we build a model?

Yes.

The current implementation includes a working **baseline machine learning / statistical prediction model** for **next-day river discharge forecasting** at USGS site `01013500`.

It uses:

- lagged discharge values
- rolling discharge means
- seasonal encoding
- CAMELS static basin attributes

The model is implemented in:

- [`flood_prediction_modeling/train_model.py`](./flood_prediction_modeling/train_model.py)

This is a real predictive model, not just a mockup. It is a baseline regression-style forecasting model trained locally from downloaded data.

## Current model metrics

From the latest local run:

- `RMSE = 241.44`
- `MAE = 116.61`
- `NSE = 0.9758`

Metrics file:

- [`flood_prediction_modeling/outputs/metrics.json`](./flood_prediction_modeling/outputs/metrics.json)

## How to access the dashboard

### Option 1: Open directly

Open:

- [`flood_prediction_modeling/index.html`](./flood_prediction_modeling/index.html)

This is the team dashboard page with:

- animated forecast tracking
- residual chart
- trend chart
- actual vs predicted scatter plot
- error distribution
- rolling 14-day MAE

### Option 2: Serve locally

From the repository root, run:

```powershell
.\run_dashboard.ps1
```

Then open:

- `http://127.0.0.1:8123/flood_prediction_modeling/index.html`

## How to re-run the model

Use the bundled Python runtime from this environment or your own Python install with `pandas` and `numpy`.

From `flood_prediction_modeling/`:

```powershell
& "C:\Users\msrib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" download_data.py
& "C:\Users\msrib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" build_database.py
& "C:\Users\msrib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" train_model.py
```

## Dataset status

### Fully integrated

- CAMELS-US attributes
- USGS Water Data API daily discharge

### Partially integrated

- NASA GPM IMERG Early V07

NASA metadata access works, but direct IMERG file download returned `401 Unauthorized` in this environment, so Earthdata credentials are still needed for full precipitation ingestion.

## Repository map

- [`flood_prediction_modeling/index.html`](./flood_prediction_modeling/index.html)
- [`flood_prediction_modeling/README.md`](./flood_prediction_modeling/README.md)
- [`flood_prediction_modeling/outputs/predictions.csv`](./flood_prediction_modeling/outputs/predictions.csv)
- [`flood_prediction_modeling/outputs/prediction_plot.svg`](./flood_prediction_modeling/outputs/prediction_plot.svg)
- [`flood_prediction_procurement/README.md`](./flood_prediction_procurement/README.md)

## Next recommended upgrade

The next major step is to add authenticated NASA IMERG precipitation ingestion so the system can evolve from a discharge-memory baseline into a stronger rainfall-driven flood prediction workflow.
