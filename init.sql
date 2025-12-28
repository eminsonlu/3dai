-- Enable PostGIS extension for GPS/geometry support
CREATE EXTENSION IF NOT EXISTS postgis;

-- Vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    vehicle_name VARCHAR(50),
    vehicle_type VARCHAR(50),
    capacity_m3 DECIMAL(5,2),
    capacity_ton DECIMAL(5,2)
);

-- Routes table
CREATE TABLE IF NOT EXISTS routes (
    route_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    route_date DATE,

    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER,

    start_lat DECIMAL(10,6),
    start_lon DECIMAL(10,6),
    end_lat DECIMAL(10,6),
    end_lon DECIMAL(10,6),

    -- GPS path as LineString geometry
    route_line GEOMETRY(LINESTRING, 4326),

    total_distance_km DECIMAL(10,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_routes_vehicle ON routes(vehicle_id, route_date);
CREATE INDEX IF NOT EXISTS idx_routes_date ON routes(route_date);
CREATE INDEX IF NOT EXISTS idx_route_line ON routes USING GIST(route_line);
