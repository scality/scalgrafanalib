from typing import Any, Dict, List, TypeVar
import attr
from grafanalib import core  # type: ignore

Json = Dict[str, Any]
Self = TypeVar("Self")


@attr.s
class PieChart(core.PieChartv2):
    """PieChart: Allow settings displayLabels"""

    displayLabels: List[str] = attr.ib(  # pylint: disable=invalid-name
        default=[], validator=attr.validators.instance_of(list)
    )

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.displayLabels:
            json["options"]["displayLabels"] = self.displayLabels
        return json


@attr.s
class Tooltip(core.Tooltip):
    """SimpleTooltip : simple, "modern" tooltip configuration
    Inherit from Tooltip to allow using in place of "usual" tooltip class"""

    show: bool = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    showHistogram: bool = attr.ib(  # pylint: disable=invalid-name
        default=True, validator=attr.validators.instance_of(bool)
    )

    def to_json_data(self) -> Json:
        return {"show": self.show, "showHistogram": self.showHistogram}


class Target(core.Target):
    """Target: set default `intervalFactor` mode to 1"""

    def to_json_data(self) -> Json:
        self.intervalFactor = 1
        return super().to_json_data()


@attr.s
class TimeSeries(core.TimeSeries):
    """TimeSeries: Allow settings decimals"""

    decimals: int = attr.ib(default=0, validator=attr.validators.instance_of(int))

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.decimals:
            json["options"]["decimals"] = self.decimals
        return json


def _simplify(json: Json) -> Json:
    return {key: value for key, value in json.items() if value is not None}


class Dashboard(core.Dashboard):
    """Dashboard: extension to make the dashboard a bit less verbose"""

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        # Remove 'null' values from panels
        json["panels"] = [_simplify(panel.to_json_data()) for panel in json["panels"]]
        # But do not remove null values from dashboard itself, this would fields
        # we kind of use (uid)
        return json

    def verify_datasources(self) -> Self:
        datasources = {
            "${" + input.name + "}"
            for input in self.inputs
            if isinstance(input, core.DataSourceInput)
        }
        for panel in self.panels:
            if isinstance(panel, core.RowPanel):
                assert panel.dataSource is None
            else:
                assert panel.dataSource in datasources
        return self
