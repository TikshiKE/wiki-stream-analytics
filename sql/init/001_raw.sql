-- Raw layer: partitioned recentchange events (managed outside dbt).

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.recentchange (
    event_id      uuid        NOT NULL,
    event_ts      timestamptz NOT NULL,
    wiki          text        NOT NULL,
    domain        text        NOT NULL,
    change_type   text        NOT NULL,
    namespace     int,
    title         text,
    user_name     text,
    is_bot        boolean,
    is_anonymous  boolean,
    is_minor      boolean,
    comment       text,
    length_old    int,
    length_new    int,
    inserted_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (event_id, event_ts)
) PARTITION BY RANGE (event_ts);

CREATE TABLE IF NOT EXISTS raw.recentchange_default
    PARTITION OF raw.recentchange DEFAULT;

-- Bootstrap daily partitions: today + 3 days ahead (Airflow maintains these later).
DO $$
DECLARE
    d date;
    part_name text;
    start_ts timestamptz;
    end_ts timestamptz;
BEGIN
    FOR i IN 0..3 LOOP
        d := CURRENT_DATE + i;
        part_name := format('recentchange_%s', to_char(d, 'YYYYMMDD'));
        start_ts := d::timestamptz;
        end_ts := (d + 1)::timestamptz;
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS raw.%I PARTITION OF raw.recentchange '
            'FOR VALUES FROM (%L) TO (%L)',
            part_name, start_ts, end_ts
        );
    END LOOP;
END $$;

CREATE INDEX IF NOT EXISTS idx_recentchange_wiki_ts ON raw.recentchange (wiki, event_ts);
CREATE INDEX IF NOT EXISTS idx_recentchange_event_ts ON raw.recentchange (event_ts);

CREATE TABLE IF NOT EXISTS public.schema_migrations (
    version     text PRIMARY KEY,
    applied_at  timestamptz NOT NULL DEFAULT now()
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'wiki_ro') THEN
        CREATE ROLE wiki_ro LOGIN PASSWORD 'wiki_ro';
    END IF;
END $$;

GRANT USAGE ON SCHEMA raw TO wiki_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA raw TO wiki_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO wiki_ro;
