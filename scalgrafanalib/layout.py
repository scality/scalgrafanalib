from operator import floordiv
from typing import List, Union
import attr
from grafanalib.core import GridPos, Panel, RowPanel  # type: ignore

PanelList = List[Panel]
PanelRow = PanelList
PanelColumn = List[Union[Panel, PanelRow]]

ROW_HEIGHT = 1  # height of a 'row' panel
GRID_WIDTH = 24  # Width of the Grafana layout grid


def get_height(panel: Panel) -> int:
    """Return the height of the panel"""
    if isinstance(panel, RowPanel):
        return ROW_HEIGHT
    if panel.gridPos is None:
        return 0  # unknown height
    return panel.gridPos.h


def get_width(panel: Panel) -> int:
    """Return the width of the panel"""
    if isinstance(panel, RowPanel):
        return GRID_WIDTH
    if panel.gridPos is None:
        return 0  # unknown width
    return panel.gridPos.w


def row(panels: PanelList, h: int, w: int = 0) -> PanelRow:
    """Resize panels so they are evenly spaced."""
    if w == 0:
        alloted_widths = list(filter(None, [get_width(panel) for panel in panels]))
        w = floordiv(24 - sum(alloted_widths), len(panels) - len(alloted_widths) or 1)
    res = []
    pos = 0
    for panel in panels:
        assert isinstance(panel, Panel)
        assert not isinstance(panel, RowPanel)
        width = get_width(panel) or w
        res += [attr.evolve(panel, gridPos=GridPos(x=pos, y=0, h=h, w=width))]
        pos += width
    return res


def column(panels: PanelColumn, h: int = 0) -> PanelList:
    """Position panels/rows on top of each other, optionally setting the height"""
    res = []
    pos = 0
    for row in panels:
        if isinstance(row, list):
            max_height = 0
            for panel in row:
                assert isinstance(panel, Panel)
                height = get_height(panel) or h
                res += [
                    attr.evolve(
                        panel, gridPos=attr.evolve(panel.gridPos, y=pos, h=height)
                    )
                ]
                max_height = max(height, max_height)
            pos += max_height
        else:
            assert isinstance(row, Panel)
            height = get_height(row) or h
            width = get_width(row) or GRID_WIDTH
            res += [attr.evolve(row, gridPos=GridPos(x=0, y=pos, w=width, h=height))]
            pos += height
    return res


def resize(panels: PanelList, h: int = 0, w: int = 0) -> PanelList:
    return [
        attr.evolve(
            panel,
            gridPos=GridPos(
                x=0,
                y=0,
                h=h if h else get_height(panel),
                w=w if w else get_width(panel),
            ),
        )
        for panel in panels
    ]
