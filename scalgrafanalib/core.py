from typing import Any, Dict, List, TypeVar, Union
import attr
from grafanalib import core  # type: ignore

Json = Dict[str, Any]
Self = TypeVar("Self")


@attr.s
class GaugePanel(core.GaugePanel):
    """GaugePanel: Allow settings noValue"""

    noValue: str = attr.ib(default=None)  # pylint: disable=invalid-name

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.noValue:
            json["fieldConfig"]["defaults"]["noValue"] = self.noValue
        if self.calc:
            json["options"] = {"reduceOptions": {"calcs": [self.calc]}}
        return json


@attr.s
class BarGauge(core.BarGauge):
    """BarGauge: Allow settings noValue"""

    noValue: str = attr.ib(default=None)  # pylint: disable=invalid-name

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.noValue:
            json["options"]["fieldOptions"]["defaults"]["noValue"] = self.noValue
        return json


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
class Stat(core.Stat):
    """Stat: Allow settings minValue and maxValue"""

    minValue = attr.ib(default=None)  # pylint: disable=invalid-name
    maxValue = attr.ib(default=None)  # pylint: disable=invalid-name

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.minValue:
            json["fieldConfig"]["defaults"]["min"] = self.minValue
        if self.maxValue:
            json["fieldConfig"]["defaults"]["max"] = self.maxValue
        return json


@attr.s
class StatSpecialMapping:
    """
    Generates json structure for the special mappings for the StatPanel:

    :param text: Sting that will replace input value
    :param match: Special value to match, one of "nan", "null", "null+nan", "true", "false", "empty"
    :param color: How to color the text if mapping occurs
    :param index: index
    """

    text = attr.ib(default="", validator=attr.validators.instance_of(str))
    match = attr.ib(
        default="",
        validator=attr.validators.in_(
            ["nan", "null", "null+nan", "true", "false", "empty"]
        ),
    )
    color = attr.ib(default="", validator=attr.validators.instance_of(str))
    index = attr.ib(default=None)

    def to_json_data(self):
        return {
            "type": "special",
            "options": {
                "match": self.match,
                "result": {
                    "text": self.text,
                    "index": self.index,
                },
            },
        }


@attr.s
class StateTimeline(core.StateTimeline):
    """StateTimeline: Allow settings minValue and maxValue"""

    minValue = attr.ib(default=None)  # pylint: disable=invalid-name
    maxValue = attr.ib(default=None)  # pylint: disable=invalid-name

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.minValue:
            json["fieldConfig"]["defaults"]["min"] = self.minValue
        if self.maxValue:
            json["fieldConfig"]["defaults"]["max"] = self.maxValue
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
    """TimeSeries: Allow settings decimals & legend values"""

    decimals: int = attr.ib(default=0, validator=attr.validators.instance_of(int))
    legendValues: List[str] = attr.ib(  # pylint: disable=invalid-name
        default=[], validator=attr.validators.instance_of(list)
    )
    spanNulls: Union[int, bool] = attr.ib(  # pylint: disable=invalid-name
        default=False, validator=attr.validators.instance_of((int, bool))
    )

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.decimals:
            json["options"]["decimals"] = self.decimals
        if self.legendValues:
            json["options"]["legend"]["calcs"] = self.legendValues
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
