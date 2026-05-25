# Collaboration Feature Bundle

This folder is intended to give Gemini or any collaborator **loaded data files**, not placeholders.

Primary manifest:

- `00_feature_bundle_manifest.csv`

Core loaded layers:

1. `01_usgs_daily_discharge.csv`
2. `02_usgs_iv_discharge.csv`
3. `03_usgs_iv_gage_height.csv`
4. `04_usgs_iv_stage_discharge_pairs.csv`
5. `05_usgs_time_series_metadata_discharge.csv`
6. `06_usgs_site_metadata.csv`
7. `07_usgs_rating_curve_manifest.csv`
8. `08_usgs_upstream_basin.geojson`
9. `09_camels_topography_attributes.csv`
10. `10_camels_climate_attributes.csv`
11. `11_camels_hydrology_attributes.csv`
12. `12_nasa_imerg_granule_metadata.csv`

Notes:

- The rating-curve manifest points to downloaded `.rdb` rating files in this same folder.
- The gauge used for this bundle is USGS site `01013500`.
- Gage height is included as the closest immediately accessible official river-depth-like signal for this site.
