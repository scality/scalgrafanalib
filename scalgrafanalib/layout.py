from typing import List, Union
import attr
from grafanalib.core import GridPos, Panel, RowPanel  # type: ignore

PanelList = List[Panel]
PanelRow = PanelList
PanelColumn = List[Union[Panel, PanelRow]]
PanelOrList = Union[Panel, PanelList]

ROW_HEIGHT = 1  # height of a 'row' panel
GRID_WIDTH = 24  # Width of the Grafana layout grid


def get_x(panel: Panel) -> int:
    return panel.gridPos.x if panel.gridPos is not None else 0


def get_y(panel: Panel) -> int:
    return panel.gridPos.y if panel.gridPos is not None else 0


def get_height(panel: PanelOrList) -> int:
    """Return the height of the panel"""
    if isinstance(panel, RowPanel):
        return ROW_HEIGHT
    if isinstance(panel, list):
        return max([get_y(p) + get_height(p) for p in panel])
    if panel.gridPos is None:
        return 0  # unknown height
    return panel.gridPos.h


def get_width(panel: PanelOrList) -> int:
    """Return the width of the panel"""
    if isinstance(panel, RowPanel):
        return GRID_WIDTH
    if isinstance(panel, list):
        return max([get_x(p) + get_width(p) for p in panel])
    if panel.gridPos is None:
        return 0  # unknown width
    return panel.gridPos.w


def reposition(
    panel: Panel, offset_x: int = 0, offset_y: int = 0, height: int = 0, width: int = 0
) -> Panel:
    if isinstance(panel, RowPanel):
        assert offset_x == 0  # cannot move a RowPanel laterally!
    grid_pos = GridPos(
        x=offset_x + get_x(panel),
        y=offset_y + get_y(panel),
        h=get_height(panel) or height,
        w=get_width(panel) or width,
    )
    return attr.evolve(panel, gridPos=grid_pos)


def row(panels: PanelList, height: int, width: int = 0) -> PanelRow:
    """Resize panels so they are evenly spaced."""
    if width == 0:
        alloted_widths = list(filter(None, [get_width(panel) for panel in panels]))
        width = (GRID_WIDTH - sum(alloted_widths)) // (
            len(panels) - len(alloted_widths) or 1
        )
    res = []
    pos = 0
    for panel in panels:
        assert not isinstance(panel, RowPanel)
        if isinstance(panel, list):
            res += [
                reposition(p, offset_x=pos, height=height, width=width) for p in panel
            ]
        else:
            assert isinstance(panel, Panel)
            res += [reposition(panel, offset_x=pos, height=height, width=width)]
        pos = get_width(res)
    return res


def column(panels: PanelColumn, height: int = 0, width: int = 0) -> PanelList:
    """Position panels/rows on top of each other, optionally setting the height"""
    res = []
    pos = 0
    for panel in panels:  # pylint: disable=redefined-outer-name
        if isinstance(panel, list):
            res += [
                reposition(p, offset_y=pos, height=height, width=width) for p in panel
            ]
        else:
            res += [reposition(panel, offset_y=pos, height=height, width=width)]
        pos = get_height(res)
    return res


def resize(panels: PanelList, height: int = 0, width: int = 0) -> PanelList:
    return [
        attr.evolve(
            panel,
            gridPos=GridPos(
                x=0,
                y=0,
                h=height if height else get_height(panel),
                w=width if width else get_width(panel),
            ),
        )
        for panel in panels
    ]
