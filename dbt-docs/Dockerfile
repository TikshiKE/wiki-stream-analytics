# Build from repository root after `dbt docs generate` (CI writes dbt/wiki_analytics/target/).
FROM nginx:1.27-alpine

COPY dbt-docs/nginx.conf /etc/nginx/nginx.conf
COPY dbt/wiki_analytics/target /usr/share/nginx/html

EXPOSE 8080
