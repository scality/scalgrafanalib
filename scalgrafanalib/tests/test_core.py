import pytest

from scalgrafanalib import TimeSeries


def span_nulls(panel):
    return panel.to_json_data()["fieldConfig"]["defaults"]["custom"]["spanNulls"]


def test_span_nulls_defaults_to_false():
    assert span_nulls(TimeSeries(title="One")) is False


def test_span_nulls_accepts_bool():
    assert span_nulls(TimeSeries(title="One", spanNulls=True)) is True


def test_span_nulls_accepts_gap_threshold_in_milliseconds():
    assert span_nulls(TimeSeries(title="One", spanNulls=3 * 60 * 1000)) == 180000


def test_span_nulls_rejects_other_types():
    with pytest.raises(TypeError):
        TimeSeries(title="One", spanNulls="3m")
