# Flood Prediction Procurement Pack

Validated on 2026-05-25.

## 1) Credible datasets to procure first

### Recommended core stack for a flood prediction model

| Priority | Dataset | Provider | Why it is credible | Best use |
| --- | --- | --- | --- | --- |
| 1 | USGS NWIS | U.S. Geological Survey | Official gauge archive with time-series data for gage height, streamflow, precipitation, and peak flows | Ground-truth labels and gauge features |
| 1 | NASA GPM IMERG | NASA | Official satellite precipitation product with near real-time half-hourly rainfall estimates | Rainfall forcing |
| 1 | NOAA National Water Model (NWM) | NOAA / NWS | Official operational hydrologic model with streamflow guidance over millions of reaches | Baseline forecast features and hydrologic context |
| 2 | USGS 3DEP Seamless 1 m DEM | U.S. Geological Survey | Official high-resolution elevation source explicitly used for flood risk mapping | Terrain, slope, flow accumulation, HAND |
| 2 | Global Flood Database | Cloud to Street + Dartmouth Flood Observatory + Google Earth Engine catalog | Widely cited event-level inundation database with mapped flood extent and duration | Event labels and inundation history |
| 3 | Copernicus GloFAS | Copernicus / ECMWF | Official global river discharge forecasting dataset | Global coverage outside U.S. or for benchmarking |
| 3 | Google GRRR | Google Flood Forecasting | Public historical global river discharge estimates for 1980-2023 | Global reanalysis / reforecast benchmark |

## 2) Source notes you can cite

- **USGS NWIS**: USGS states that NWIS stores site characteristics plus time-series data for "gage height, streamflow, groundwater level, precipitation" and also peak flows.  
  Source: [USGS NWIS](https://www.usgs.gov/centers/new-york-water-science-center/science/nwis-usgs-data-archive)

- **NASA GPM IMERG**: NASA states IMERG is available in near real time and updates precipitation estimates "every half-hour."  
  Source: [NASA IMERG](https://gpm.nasa.gov/data/imerg)

- **NOAA National Water Model**: NOAA states NWM provides streamflow for "over 2.7 million river reaches" and hydrologic information on 1 km and 100 m/250 m grids.  
  Source: [NOAA NWM](https://water.noaa.gov/about/nwm)

- **USGS 3DEP Seamless 1 m DEM**: USGS explicitly lists "flood risk mapping" as a supported use case.  
  Source: [USGS 3DEP S1M](https://www.usgs.gov/3d-elevation-program/new-product-3d-elevation-program-seamless-1-meter-digital-elevation-model-s1m)

- **Global Flood Database**: Google Earth Engine describes 913 mapped flood events from 2000-2018, with maximum flood extent and inundation duration at 250 m resolution.  
  Source: [Global Flood Database](https://developers.google.com/earth-engine/datasets/catalog/GLOBAL_FLOOD_DB_MODIS_EVENTS_V1)

- **Copernicus GloFAS**: Copernicus states the dataset is produced with the LISFLOOD hydrological model at 0.05 degree resolution for current versions.  
  Source: [Copernicus GloFAS seasonal dataset](https://ewds.climate.copernicus.eu/datasets/cems-glofas-seasonal?tab=overview)

- **Google GRRR**: Google lists GRRR as global river discharge estimates for 1980-2023.  
  Source: [Google Flood Forecasting API resources](https://developers.google.com/flood-forecasting)

## 3) Best procurement recommendation

If you need one practical recommendation today, use:

1. **US-focused model**: USGS NWIS + NASA IMERG + NOAA NWM + USGS 3DEP + Global Flood Database
2. **Global model**: NASA IMERG + Copernicus GloFAS + Google GRRR + Global Flood Database + local gauge network where available

Why this stack works:

- It covers the three things a flood model needs: **forcing** (rainfall), **hydrology** (streamflow/water level), and **labels** (historical flood events/inundation).
- It combines **official agencies** with a **widely cited event database**.
- It supports both **time-series forecasting** and **spatial flood mapping**.

## 4) Most appropriate database

**Recommended database**: PostgreSQL with PostGIS  
**Optional extension**: TimescaleDB for large time-series workloads

Why this is the best fit:

- Flood prediction data is both **spatial** and **temporal**
- You will store **gauges**, **river reaches**, **watersheds**, **grid cells**, **flood polygons**, and **time-series observations**
- PostGIS handles geometry well, and PostgreSQL is a strong fit for relational provenance and research traceability

## 5) Logical data model

This package models:

- dataset provenance
- monitoring stations
- watersheds and river reaches
- grid cells for gridded products
- observations and forecasts
- flood events and inundation assets
- model runs and predictions

See:

- [schema.sql](/C:/Users/msrib/OneDrive/Documents%20-%20OneDrive/Playground/flood_prediction_procurement/schema.sql)
- [erd.mmd](/C:/Users/msrib/OneDrive/Documents%20-%20OneDrive/Playground/flood_prediction_procurement/erd.mmd)

## 6) Research papers to start from

1. Priya, R. et al. **Flood Prediction Using Machine Learning Models: Literature Review**. *Water* 2018. DOI: [10.3390/w10111536](https://doi.org/10.3390/w10111536)
2. Johnson, J. M. et al. **An integrated evaluation of the National Water Model (NWM)-HAND flood mapping methodology**. *Natural Hazards and Earth System Sciences* 2019. DOI: [10.5194/nhess-19-2405-2019](https://doi.org/10.5194/nhess-19-2405-2019)
3. Tellman, B. et al. **Satellite imaging reveals increased proportion of population exposed to floods**. *Nature* 2021. DOI: [10.1038/s41586-021-03695-w](https://doi.org/10.1038/s41586-021-03695-w)
4. Moshe, Z. et al. **HydroNets: Leveraging River Structure for Hydrologic Modeling**. ICLR 2020 / Google Research. [Google Research page](https://research.google/pubs/hydronets-leveraging-river-structure-for-hydrologic-modeling/) and [arXiv](https://arxiv.org/abs/2007.00595)
5. Google Research et al. **Global prediction of extreme floods in ungauged watersheds**. *Nature* 2024. DOI: [10.1038/s41586-024-07145-1](https://doi.org/10.1038/s41586-024-07145-1)

## 7) Procurement-ready summary

If you need a fast approval note, use this:

> Procure a spatial-temporal flood prediction data stack anchored on official USGS, NOAA, NASA, and Copernicus sources, with the Global Flood Database as the historical inundation label set. Store the data in PostgreSQL/PostGIS because the workload mixes time-series observations with geospatial entities and flood polygons. This supports both research-grade modeling and future operational deployment.
