# Flood Prediction Modeling Workspace

This workspace downloads a practical subset of flood-relevant data, stores it locally, and trains a baseline one-day-ahead discharge prediction model.

## What this pipeline uses

- **CAMELS-US** static basin attributes from the official Zenodo-hosted CAMELS release
- **USGS Water Data API** daily discharge data from the modern `api.waterdata.usgs.gov` endpoint
- **NASA GPM IMERG Early V07** public granule metadata from NASA CMR

## Important NASA note

This pipeline can download **public IMERG metadata** and verify the official granule download URL. In this environment, direct IMERG file download from GES DISC returns `401 Unauthorized`, which is consistent with NASA Earthdata-protected access.

That means:

- metadata download works
- official file URL discovery works
- anonymous binary granule download does **not** work here

## Files

- [download_data.py](/C:/Users/msrib/OneDrive/Documents%20-%20OneDrive/Playground/flood_prediction_modeling/download_data.py)
- [build_database.py](/C:/Users/msrib/OneDrive/Documents%20-%20OneDrive/Playground/flood_prediction_modeling/build_database.py)
- [train_model.py](/C:/Users/msrib/OneDrive/Documents%20-%20OneDrive/Playground/flood_prediction_modeling/train_model.py)
- [model_flow.mmd](/C:/Users/msrib/OneDrive/Documents%20-%20OneDrive/Playground/flood_prediction_modeling/model_flow.mmd)

## Run order

```powershell
& "C:\Users\msrib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" download_data.py
& "C:\Users\msrib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" build_database.py
& "C:\Users\msrib\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" train_model.py
```

## Model choice

The baseline model is a **linear autoregressive discharge forecast** using:

- lagged discharge features
- rolling discharge means
- calendar seasonality
- selected CAMELS static catchment attributes

This is a baseline, not a production flood warning model. It is intended to give you a working starting point quickly.
