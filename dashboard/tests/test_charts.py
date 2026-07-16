"""Tests for Plotly chart builders."""

from dashboard.charts import (
    editor_share_figure,
    hourly_activity_figure,
    sparkline_figure,
    top_pages_dataframe,
)


def test_hourly_activity_top_wiki_grouping() -> None:
    rows = [
        {"hour_ts": "2026-07-16T10:00:00+00:00", "wiki": f"wiki{i}", "edit_count": 100 - i}
        for i in range(12)
    ]
    fig = hourly_activity_figure(rows)
    names = {trace.name for trace in fig.data}
    assert "wiki0" in names
    assert "other" in names


def test_editor_share_figure_has_three_series() -> None:
    rows = [
        {"edit_date": "2026-07-15", "editor_type": "bot", "edit_count": 10},
        {"edit_date": "2026-07-15", "editor_type": "anonymous", "edit_count": 20},
        {"edit_date": "2026-07-15", "editor_type": "registered", "edit_count": 70},
    ]
    fig = editor_share_figure(rows)
    assert len(fig.data) == 3


def test_sparkline_empty_message() -> None:
    fig = sparkline_figure([])
    assert fig.layout.annotations[0].text == "Waiting for live data…"


def test_top_pages_dataframe_adds_url() -> None:
    df = top_pages_dataframe([{"wiki": "enwiki", "title": "Earth", "edit_count": 3}])
    assert "url" in df.columns
    assert df.iloc[0]["url"] == "https://en.wikipedia.org/wiki/Earth"
