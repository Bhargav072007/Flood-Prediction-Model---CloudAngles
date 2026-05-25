CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE dataset_source (
    dataset_source_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    category TEXT NOT NULL,
    geographic_scope TEXT,
    temporal_coverage TEXT,
    spatial_resolution TEXT,
    temporal_resolution TEXT,
    license_name TEXT,
    source_url TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE watershed (
    watershed_id BIGSERIAL PRIMARY KEY,
    external_code TEXT UNIQUE,
    name TEXT NOT NULL,
    country_code CHAR(2),
    area_sq_km NUMERIC(12, 2),
    geom GEOMETRY(MULTIPOLYGON, 4326)
);

CREATE TABLE river_reach (
    river_reach_id BIGSERIAL PRIMARY KEY,
    watershed_id BIGINT REFERENCES watershed(watershed_id),
    external_code TEXT UNIQUE,
    name TEXT,
    stream_order INTEGER,
    length_km NUMERIC(10, 2),
    slope NUMERIC(10, 5),
    geom GEOMETRY(MULTILINESTRING, 4326)
);

CREATE TABLE station (
    station_id BIGSERIAL PRIMARY KEY,
    dataset_source_id BIGINT NOT NULL REFERENCES dataset_source(dataset_source_id),
    watershed_id BIGINT REFERENCES watershed(watershed_id),
    river_reach_id BIGINT REFERENCES river_reach(river_reach_id),
    provider_station_code TEXT NOT NULL,
    station_type TEXT NOT NULL,
    name TEXT NOT NULL,
    river_name TEXT,
    elevation_m NUMERIC(8, 2),
    installed_on DATE,
    retired_on DATE,
    geom GEOMETRY(POINT, 4326),
    UNIQUE (dataset_source_id, provider_station_code)
);

CREATE TABLE grid_cell (
    grid_cell_id BIGSERIAL PRIMARY KEY,
    dataset_source_id BIGINT NOT NULL REFERENCES dataset_source(dataset_source_id),
    external_code TEXT NOT NULL,
    resolution_m NUMERIC(10, 2),
    centroid GEOMETRY(POINT, 4326),
    geom GEOMETRY(POLYGON, 4326),
    UNIQUE (dataset_source_id, external_code)
);

CREATE TABLE variable_catalog (
    variable_code TEXT PRIMARY KEY,
    variable_name TEXT NOT NULL,
    unit TEXT NOT NULL,
    description TEXT
);

CREATE TABLE observation (
    observation_id BIGSERIAL PRIMARY KEY,
    dataset_source_id BIGINT NOT NULL REFERENCES dataset_source(dataset_source_id),
    station_id BIGINT REFERENCES station(station_id),
    grid_cell_id BIGINT REFERENCES grid_cell(grid_cell_id),
    river_reach_id BIGINT REFERENCES river_reach(river_reach_id),
    observed_at TIMESTAMPTZ NOT NULL,
    issue_time TIMESTAMPTZ,
    forecast_horizon_hr INTEGER,
    variable_code TEXT NOT NULL REFERENCES variable_catalog(variable_code),
    value NUMERIC(18, 6) NOT NULL,
    qc_flag TEXT,
    CONSTRAINT observation_target_chk CHECK (
        station_id IS NOT NULL OR
        grid_cell_id IS NOT NULL OR
        river_reach_id IS NOT NULL
    )
);

CREATE TABLE flood_event (
    flood_event_id BIGSERIAL PRIMARY KEY,
    dataset_source_id BIGINT NOT NULL REFERENCES dataset_source(dataset_source_id),
    watershed_id BIGINT REFERENCES watershed(watershed_id),
    external_event_id TEXT,
    event_name TEXT,
    event_type TEXT DEFAULT 'riverine',
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    severity_class TEXT,
    peak_discharge_cms NUMERIC(18, 6),
    max_water_level_m NUMERIC(18, 6),
    max_inundation_sq_km NUMERIC(18, 6),
    country_code CHAR(2),
    geom GEOMETRY(MULTIPOLYGON, 4326),
    UNIQUE (dataset_source_id, external_event_id)
);

CREATE TABLE raster_asset (
    raster_asset_id BIGSERIAL PRIMARY KEY,
    dataset_source_id BIGINT NOT NULL REFERENCES dataset_source(dataset_source_id),
    flood_event_id BIGINT REFERENCES flood_event(flood_event_id),
    asset_type TEXT NOT NULL,
    band_name TEXT,
    file_format TEXT,
    storage_uri TEXT NOT NULL,
    spatial_resolution_m NUMERIC(10, 2),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    bbox GEOMETRY(POLYGON, 4326)
);

CREATE TABLE model_run (
    model_run_id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    run_type TEXT NOT NULL,
    issue_time TIMESTAMPTZ NOT NULL,
    training_window_start DATE,
    training_window_end DATE,
    target_horizon_hr INTEGER,
    feature_set_version TEXT,
    notes TEXT
);

CREATE TABLE model_prediction (
    model_prediction_id BIGSERIAL PRIMARY KEY,
    model_run_id BIGINT NOT NULL REFERENCES model_run(model_run_id),
    station_id BIGINT REFERENCES station(station_id),
    grid_cell_id BIGINT REFERENCES grid_cell(grid_cell_id),
    river_reach_id BIGINT REFERENCES river_reach(river_reach_id),
    flood_event_id BIGINT REFERENCES flood_event(flood_event_id),
    predicted_for TIMESTAMPTZ NOT NULL,
    variable_code TEXT NOT NULL REFERENCES variable_catalog(variable_code),
    predicted_value NUMERIC(18, 6),
    exceedance_probability NUMERIC(6, 5),
    predicted_class TEXT,
    observed_value NUMERIC(18, 6),
    residual NUMERIC(18, 6),
    CONSTRAINT model_prediction_target_chk CHECK (
        station_id IS NOT NULL OR
        grid_cell_id IS NOT NULL OR
        river_reach_id IS NOT NULL
    )
);

CREATE INDEX idx_watershed_geom ON watershed USING GIST (geom);
CREATE INDEX idx_river_reach_geom ON river_reach USING GIST (geom);
CREATE INDEX idx_station_geom ON station USING GIST (geom);
CREATE INDEX idx_grid_cell_geom ON grid_cell USING GIST (geom);
CREATE INDEX idx_flood_event_geom ON flood_event USING GIST (geom);
CREATE INDEX idx_raster_asset_bbox ON raster_asset USING GIST (bbox);

CREATE INDEX idx_observation_time ON observation (observed_at);
CREATE INDEX idx_observation_station_time ON observation (station_id, observed_at);
CREATE INDEX idx_observation_grid_time ON observation (grid_cell_id, observed_at);
CREATE INDEX idx_observation_reach_time ON observation (river_reach_id, observed_at);

CREATE INDEX idx_model_prediction_time ON model_prediction (predicted_for);
CREATE INDEX idx_model_prediction_station_time ON model_prediction (station_id, predicted_for);
CREATE INDEX idx_model_prediction_grid_time ON model_prediction (grid_cell_id, predicted_for);
CREATE INDEX idx_model_prediction_reach_time ON model_prediction (river_reach_id, predicted_for);
