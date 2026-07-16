FROM apache/airflow:2.10.4-python3.12

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
USER airflow

COPY airflow/requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir -r /requirements-airflow.txt

COPY --chown=airflow:root dbt/wiki_analytics /opt/airflow/dbt/wiki_analytics
COPY --chown=airflow:root airflow/dags /opt/airflow/dags
COPY --chown=airflow:root airflow/plugins /opt/airflow/plugins
COPY --chown=airflow:root airflow/lib /opt/airflow/lib

ENV DBT_PROFILES_DIR=/opt/airflow/dbt/wiki_analytics
ENV PYTHONPATH=/opt/airflow
ENV PATH="/home/airflow/.local/bin:${PATH}"

# Same as docker-compose; Railway must not rely on an empty default CMD.
CMD ["standalone"]
