"""Plotly chart builders and table formatting."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from dashboard.urls import page_url

TOP_WIKI_COUNT = 10
EDITOR_TYPES = ("bot", "anonymous", "registered")
EDITOR_LABELS = {
    "bot": "Bots",
    "anonymous": "Anonymous",
    "registered": "Registered",
}
EDITOR_COLORS = {
    "bot": "#ff6b6b",
    "anonymous": "#ffd93d",
    "registered": "#6bcb77",
}


def hourly_activity_figure(rows: list[dict[str, Any]]) -> go.Figure:
    """Stacked hourly edits for top wikis + other over the last 7 days."""
    if not rows:
        return _empty_figure("No hourly activity data yet")

    df = pd.DataFrame(rows)
    df["hour_ts"] = pd.to_datetime(df["hour_ts"], utc=True)
    totals = df.groupby("wiki")["edit_count"].sum().sort_values(ascending=False)
    top_wikis = set(totals.head(TOP_WIKI_COUNT).index)
    df["wiki_group"] = df["wiki"].where(df["wiki"].isin(top_wikis), "other")

    grouped = (
        df.groupby(["hour_ts", "wiki_group"], as_index=False)["edit_count"]
        .sum()
        .sort_values("hour_ts")
    )
    pivot = grouped.pivot(index="hour_ts", columns="wiki_group", values="edit_count").fillna(0)
    columns = [c for c in pivot.columns if c != "other"]
    columns.sort(key=lambda w: totals.get(w, 0), reverse=True)
    if "other" in pivot.columns:
        columns.append("other")

    fig = go.Figure()
    for wiki in columns:
        fig.add_trace(
            go.Bar(
                x=pivot.index,
                y=pivot[wiki],
                name=wiki,
                marker_line_width=0,
            )
        )
    fig.update_layout(
        barmode="stack",
        height=380,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis_title="Hour (UTC)",
        yaxis_title="Edits",
    )
    return fig


def editor_share_figure(rows: list[dict[str, Any]]) -> go.Figure:
    """Daily stacked share of bot / anonymous / registered editors."""
    if not rows:
        return _empty_figure("No editor activity data yet")

    df = pd.DataFrame(rows)
    df["edit_date"] = pd.to_datetime(df["edit_date"])
    pivot = (
        df.pivot(index="edit_date", columns="editor_type", values="edit_count")
        .fillna(0)
        .reindex(columns=list(EDITOR_TYPES), fill_value=0)
    )
    totals = pivot.sum(axis=1).replace(0, pd.NA)
    shares = pivot.div(totals, axis=0).fillna(0) * 100

    fig = go.Figure()
    for editor_type in EDITOR_TYPES:
        fig.add_trace(
            go.Bar(
                x=shares.index,
                y=shares[editor_type],
                name=EDITOR_LABELS[editor_type],
                marker_color=EDITOR_COLORS[editor_type],
                marker_line_width=0,
            )
        )
    fig.update_layout(
        barmode="stack",
        height=360,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="Share of edits (%)",
        xaxis_title="Date (UTC)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_yaxes(range=[0, 100])
    return fig


def sparkline_figure(points: list[tuple[Any, int]]) -> go.Figure:
    if not points:
        return _empty_figure("Waiting for live data…")

    times = [p[0] for p in points]
    values = [p[1] for p in points]
    fig = go.Figure(
        go.Scatter(
            x=times,
            y=values,
            mode="lines",
            fill="tozeroy",
            line=dict(color="#4CAF50", width=2),
        )
    )
    fig.update_layout(
        height=120,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def top_pages_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=["wiki", "title", "edit_count", "url"])

    df = pd.DataFrame(rows)
    df["url"] = df.apply(lambda r: page_url(r["wiki"], r["title"]), axis=1)
    return df[["wiki", "title", "edit_count", "url"]]


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14, color="#aaaaaa"),
    )
    fig.update_layout(
        height=200,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig
