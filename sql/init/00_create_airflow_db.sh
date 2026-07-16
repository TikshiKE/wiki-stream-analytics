#!/bin/bash
# Creates Airflow metadata database on first Postgres volume init.
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE airflow_meta'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_meta')\gexec
EOSQL
