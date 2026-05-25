# Flood Prediction Modeling Workspace

This folder contains the executable modeling pipeline, the dashboard, the generated outputs, and the cleaned collaboration data bundle.

## Recommended order inside this folder

1. Read the outputs:
   - [`outputs/metrics.json`](./outputs/metrics.json)
   - [`outputs/predictions.csv`](./outputs/predictions.csv)
2. Open the dashboard:
   - [`index.html`](./index.html)
3. Use the collaboration data bundle:
   - [`data/collab_feature_bundle/`](./data/collab_feature_bundle/)
4. Re-run the pipeline only if needed.

## Core scripts

- [`download_data.py`](./download_data.py): downloads CAMELS, USGS, and NASA metadata
- [`build_database.py`](./build_database.py): builds the local SQLite database
- [`train_model.py`](./train_model.py): trains the baseline next-day discharge model
- [`create_collab_feature_bundle.py`](./create_collab_feature_bundle.py): generates the cleaned loaded feature files
- [`build_master_feature_csv.py`](./build_master_feature_csv.py): merges the factors into a single daily CSV

## Model summary

The current model is a **baseline linear autoregressive discharge forecast** using:

- lagged discharge features
- rolling discharge means
- seasonal terms
- CAMELS static catchment attributes

This is a working baseline, not yet a final rainfall-driven flood forecasting system.

## Data products in this folder

### Raw and database artifacts

- `data/raw/`
- `data/flood_model.db`

### Collaboration-ready data

- `data/collab_feature_bundle/00_feature_bundle_manifest.csv`
- `data/collab_feature_bundle/master_flood_feature_table.csv`

### Visual and model outputs

- `outputs/metrics.json`
- `outputs/predictions.csv`
- `outputs/prediction_plot.svg`

## Important note about NASA IMERG

This project includes **real IMERG granule metadata**, but direct authenticated precipitation file ingestion is still the main missing piece. In this environment, anonymous binary access returned `401 Unauthorized`, which is consistent with Earthdata-protected access.
