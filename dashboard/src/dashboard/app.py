"""Streamlit dashboard UI."""

from __future__ import annotations

from datetime import timedelta

import psycopg
import redis
import streamlit as st

from dashboard import queries
from dashboard.charts import (
    editor_share_figure,
    hourly_activity_figure,
    sparkline_figure,
    top_pages_dataframe,
)
from dashboard.config import Settings, get_settings
from dashboard.live import edits_last_minute, sparkline_last_60_minutes


def _postgres_connection(settings: Settings) -> psycopg.Connection:
    return psycopg.connect(settings.postgres_dsn)


@st.cache_resource
def _redis_client(redis_url: str) -> redis.Redis:
    return redis.from_url(redis_url, decode_responses=True)


@st.cache_data(ttl=60, show_spinner=False)
def _load_hourly_activity(dsn: str) -> list[dict] | None:
    try:
        with _postgres_connection(get_settings()) as conn:
            if not queries.marts_available(conn):
                return None
            return queries.fetch_hourly_activity(conn)
    except psycopg.Error:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def _load_editor_activity(dsn: str) -> list[dict] | None:
    try:
        with _postgres_connection(get_settings()) as conn:
            if not queries.marts_available(conn):
                return None
            return queries.fetch_editor_activity(conn)
    except psycopg.Error:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def _load_top_pages(dsn: str) -> list[dict] | None:
    try:
        with _postgres_connection(get_settings()) as conn:
            if not queries.marts_available(conn):
                return None
            return queries.fetch_top_pages_today(conn)
    except psycopg.Error:
        return None


def _empty_message() -> None:
    st.info(
        "Mart tables are empty or not built yet. "
        "Wait for the hourly **dbt** run in Airflow, or trigger `dbt_hourly` manually."
    )


@st.fragment(run_every=timedelta(seconds=10))
def _live_block(redis_url: str) -> None:
    client = _redis_client(redis_url)
    last_minute = edits_last_minute(client)
    sparkline = sparkline_last_60_minutes(client)

    col_metric, col_chart = st.columns([1, 3])
    with col_metric:
        st.metric("Edits in the last minute", f"{last_minute:,}")
        st.caption("Refreshes every ~10 seconds from Redis live counters")
    with col_chart:
        st.plotly_chart(sparkline_figure(sparkline), use_container_width=True)


def main() -> None:
    settings = get_settings()

    st.set_page_config(
        page_title="Wiki Stream Analytics",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    header_left, header_right = st.columns([4, 1])
    with header_left:
        st.title("Wiki Stream Analytics")
        st.markdown(
            "Live view of Wikipedia edit activity: minute-by-minute volume, hourly trends "
            "by wiki, editor mix, and today's most-edited pages. Data flows from Wikimedia "
            "EventStreams through Kafka and Postgres; aggregates are built with dbt."
        )
        st.caption("Designed and built by [Evgeny Kren](https://github.com/TikshiKE).")
        st.markdown(f"[Source code]({settings.github_repo_url})")
    with header_right:
        st.markdown("")
        st.success("● Live data")

    st.subheader("Live activity")
    _live_block(settings.redis_url)

    st.divider()
    st.subheader("Hourly edits by wiki (last 7 days)")
    hourly = _load_hourly_activity(settings.postgres_dsn)
    if hourly is None:
        _empty_message()
    elif not hourly:
        st.info("No hourly aggregates yet — check back after the next dbt run.")
    else:
        st.plotly_chart(hourly_activity_figure(hourly), use_container_width=True)

    st.subheader("Editor mix by day")
    editors = _load_editor_activity(settings.postgres_dsn)
    if editors is None:
        _empty_message()
    elif not editors:
        st.info("No daily editor breakdown yet.")
    else:
        st.plotly_chart(editor_share_figure(editors), use_container_width=True)

    st.subheader("Top pages today")
    pages = _load_top_pages(settings.postgres_dsn)
    if pages is None:
        _empty_message()
    elif not pages:
        st.info("No page rankings for today yet.")
    else:
        df = top_pages_dataframe(pages)
        st.dataframe(
            df,
            column_config={
                "wiki": "Wiki",
                "title": "Page",
                "edit_count": st.column_config.NumberColumn("Edits", format="%d"),
                "url": st.column_config.LinkColumn("Link", display_text="Open ↗"),
            },
            hide_index=True,
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
