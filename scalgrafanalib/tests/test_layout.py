from grafanalib.core import GridPos, Panel  # type: ignore
from scalgrafanalib import layout


def check_panel(panel, **attr):
    for name, value in attr.items():
        if name in ["x", "y", "w", "h"]:
            assert getattr(panel.gridPos, name) == value
        else:
            assert getattr(panel, name) == value


def test_resize_width():
    panels = layout.resize(
        [
            Panel(title="One"),
            Panel(title="Two", gridPos=GridPos(x=None, y=None, w=1, h=None)),
            Panel(title="Three", gridPos=GridPos(x=None, y=None, w=None, h=2)),
        ],
        width=5,
    )
    assert len(panels) == 3
    check_panel(panels[0], title="One", w=5, h=0)
    check_panel(panels[1], title="Two", w=5, h=None)
    check_panel(panels[2], title="Three", w=5, h=2)


def test_resize_height():
    panels = layout.resize(
        [
            Panel(title="One"),
            Panel(title="Two", gridPos=GridPos(x=None, y=None, w=1, h=None)),
            Panel(title="Three", gridPos=GridPos(x=None, y=None, w=None, h=2)),
        ],
        height=7,
    )
    assert len(panels) == 3
    check_panel(panels[0], title="One", w=0, h=7)
    check_panel(panels[1], title="Two", w=1, h=7)
    check_panel(panels[2], title="Three", w=None, h=7)


def test_resize_width_height():
    panels = layout.resize(
        [
            Panel(title="One"),
            Panel(title="Two", gridPos=GridPos(x=None, y=None, w=1, h=None)),
            Panel(title="Three", gridPos=GridPos(x=None, y=None, w=None, h=2)),
        ],
        width=3,
        height=4,
    )
    assert len(panels) == 3
    check_panel(panels[0], title="One", w=3, h=4)
    check_panel(panels[1], title="Two", w=3, h=4)
    check_panel(panels[2], title="Three", w=3, h=4)


def test_column():
    panels = layout.column(
        [
            *layout.resize([Panel(title="One")], height=3),
            *layout.resize([Panel(title="Two")], height=4),
            *layout.resize([Panel(title="Three")], height=2),
        ]
    )
    assert len(panels) == 3
    check_panel(panels[0], title="One", y=0, h=3)
    check_panel(panels[1], title="Two", y=3, h=4)
    check_panel(panels[2], title="Three", y=7, h=2)


def test_column_heigh():
    panels = layout.column(
        [
            Panel(title="One"),
            *layout.resize([Panel(title="Two")], height=2),
            Panel(title="Three"),
        ],
        height=5,
    )
    assert len(panels) == 3
    check_panel(panels[0], title="One", y=0, h=5)
    check_panel(panels[1], title="Two", y=5, h=2)
    check_panel(panels[2], title="Three", y=7, h=5)


def test_column_width():
    panels = layout.column(
        [
            *layout.resize([Panel(title="One")], height=3),
            *layout.resize([Panel(title="Two")], height=4, width=1),
            *layout.resize([Panel(title="Three")], height=2),
        ],
        width=5,
    )
    assert len(panels) == 3
    check_panel(panels[0], title="One", y=0, h=3, w=5)
    check_panel(panels[1], title="Two", y=3, h=4, w=1)
    check_panel(panels[2], title="Three", y=7, h=2, w=5)
