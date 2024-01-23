import pytest
import re
from scalgrafanalib.metrics import Metric


def test_metrics_without_label():
    m = Metric("foo_bar")
    assert m() == "foo_bar{}"


def test_metrics_label():
    m = Metric("foo_bar", "label1")
    assert m() == "foo_bar{}"
    assert m(label1="foo") == 'foo_bar{label1="foo"}'
    assert m(label1=["foo", "bar"]) == 'foo_bar{label1=~"foo|bar"}'
    assert m(label1=re.compile("foo.*|bar")) == 'foo_bar{label1=~"foo.*|bar"}'
    assert m(label1=None) == "foo_bar{}"
    assert m('label1=~"foo.*|bar"') == 'foo_bar{label1=~"foo.*|bar"}'


def test_metrics_label_missing():
    m = Metric("foo_bar", "label1")
    with pytest.raises(ValueError):  # Invalid label
        m(label2="foo")


def test_metrics_label_str():
    m = Metric("foo_bar", label1="foo")
    assert m() == 'foo_bar{label1="foo"}'
    assert m(label1="bar") == 'foo_bar{label1="bar"}'
    assert m(label1=None) == "foo_bar{}"


def test_metrics_label_list():
    m = Metric("foo_bar", label1=["foo", "bar"])
    assert m() == 'foo_bar{label1=~"foo|bar"}'
    assert m(label1="bar") == 'foo_bar{label1="bar"}'
    assert m(label1=None) == "foo_bar{}"


def test_metrics_label_regex():
    m = Metric("foo_bar", label1=re.compile("foo.*|bar"))
    assert m() == 'foo_bar{label1=~"foo.*|bar"}'
    assert m(label1=None) == "foo_bar{}"


def test_metrics_with_defaults():
    m = Metric("foo_bar", "label1").with_defaults('label1=~"foo.*|bar"')
    assert m() == 'foo_bar{label1=~"foo.*|bar"}'
    assert m(label1=None) == "foo_bar{}"


def test_metrics_with_defaults_missing():
    m = Metric("foo_bar").with_defaults('label1=~"foo.*|bar"')
    assert m() == 'foo_bar{label1=~"foo.*|bar"}'
    assert m(label1=None) == "foo_bar{}"


def test_metrics_with_defaults_override():
    m = Metric("foo_bar", label1="foo").with_defaults('label1=~"foo.*|bar"')
    assert m() == 'foo_bar{label1=~"foo.*|bar"}'
    assert m(label1=None) == "foo_bar{}"
