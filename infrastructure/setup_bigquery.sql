```sql
-- 1. Crear el Dataset
-- Ejecutar en Cloud Shell o consola de BigQuery
CREATE SCHEMA IF NOT EXISTS dataset_f1;

-- 2. Crear la Tabla Optimizada 
-- Usamos PARTITION BY para optimizar costos y evitar escaneos completos (Full Scans)
CREATE OR REPLACE TABLE `dataset_f1.telemetria` (
  race_id STRING,
  driver STRING,
  event_name STRING,
  lap_number INT64,
  lap_time STRING,
  position INT64,
  session_type STRING,
  driver_number STRING,
  lap_duration_ms INT64,
  compound STRING,
  season INT64,
  speed_kmh FLOAT64,
  rpm INT64,
  gear_selection INT64,
  throttle_application FLOAT64,
  brake_application BOOL,
  timestamp TIMESTAMP
)
PARTITION BY DATE(timestamp);
