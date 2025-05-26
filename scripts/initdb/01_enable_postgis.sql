-- Enable PostGIS extension if it doesn't already exist
CREATE EXTENSION IF NOT EXISTS postgis;

-- Optional: Enable other useful PostGIS extensions if needed later
-- CREATE EXTENSION IF NOT EXISTS postgis_topology;
-- CREATE EXTENSION IF NOT EXISTS postgis_raster; -- If you plan to store rasters directly in DB
-- CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;  -- Often useful with PostGIS
-- CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder; -- For US address geocoding

-- You can also set default privileges or other DB setup here if needed
-- For example, granting usage on the public schema to your app user if not default
-- GRANT USAGE ON SCHEMA public TO your_app_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO your_app_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO your_app_user;