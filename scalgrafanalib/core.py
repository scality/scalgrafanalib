from typing import Any, Dict, List, Union, Optional
import attr
from grafanalib import core  # type: ignore

Json = Dict[str, Any]


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
class Stat(core.Stat):  # pylint: disable=too-many-instance-attributes
    """Stat: Allow settings minValue and maxValue, plus accept 'unit' as alias for 'format'"""

    minValue = attr.ib(default=None)  # pylint: disable=invalid-name
    maxValue = attr.ib(default=None)  # pylint: disable=invalid-name
    # alias: Grafanalib 0.7 uses 'format', our older code used 'unit'
    unit = attr.ib(default=None, metadata={"alias": "format"})
    # Advanced options for version panel and others
    reduceOptions = attr.ib(default=None)  # pylint: disable=invalid-name
    graphMode = attr.ib(default=None)  # pylint: disable=invalid-name
    justifyMode = attr.ib(default=None)  # pylint: disable=invalid-name
    textSize = attr.ib(default=None)  # pylint: disable=invalid-name
    wideLayout = attr.ib(default=None)  # pylint: disable=invalid-name

    def __attrs_post_init__(self):  # type: ignore
        # Map unit -> format if provided
        if self.unit is not None:
            # 'format' attribute is defined in parent via attrs; set it
            setattr(self, "format", self.unit)

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.minValue is not None:
            json["fieldConfig"]["defaults"]["min"] = self.minValue
        if self.maxValue is not None:
            json["fieldConfig"]["defaults"]["max"] = self.maxValue

        # Ensure options structure exists
        if "options" not in json:
            json["options"] = {}

        # Add advanced options
        if self.reduceOptions is not None:
            json["options"]["reduceOptions"] = self.reduceOptions
        if self.graphMode is not None:
            json["options"]["graphMode"] = self.graphMode
        if self.justifyMode is not None:
            json["options"]["justifyMode"] = self.justifyMode
        if self.wideLayout is not None:
            json["options"]["wideLayout"] = self.wideLayout
        if self.textSize is not None:
            if "text" not in json["options"]:
                json["options"]["text"] = {}
            json["options"]["text"]["valueSize"] = self.textSize

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
class StateMapping:
    """
    Represents a state mapping for StateTimeline panels with color and text
    """

    value: Union[int, str, None] = attr.ib()
    text: str = attr.ib()
    color: Optional[str] = attr.ib(default=None)
    index: int = attr.ib(default=0)

    def to_json_data(self) -> Dict[str, Any]:
        result = {
            "index": self.index,
            "text": self.text,
        }
        if self.color:
            result["color"] = self.color
        return result


@attr.s
class StateTimeline(core.StateTimeline):
    """StateTimeline: Allow settings minValue, maxValue, and color mappings for MongoDB states"""

    minValue = attr.ib(default=None)  # pylint: disable=invalid-name
    maxValue = attr.ib(default=None)  # pylint: disable=invalid-name
    colorMode: str = attr.ib(default="palette-classic")  # pylint: disable=invalid-name
    mappings: List[Union[StateMapping, Dict[str, Any]]] = attr.ib(
        default=None
    )  # pylint: disable=invalid-name

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.minValue:
            json["fieldConfig"]["defaults"]["min"] = self.minValue
        if self.maxValue:
            json["fieldConfig"]["defaults"]["max"] = self.maxValue

        # Set color mode
        if "fieldConfig" not in json:
            json["fieldConfig"] = {}
        if "defaults" not in json["fieldConfig"]:
            json["fieldConfig"]["defaults"] = {}
        if "color" not in json["fieldConfig"]["defaults"]:
            json["fieldConfig"]["defaults"]["color"] = {}
        json["fieldConfig"]["defaults"]["color"]["mode"] = self.colorMode

        # Add mappings if provided
        if self.mappings:
            if "mappings" not in json["fieldConfig"]["defaults"]:
                json["fieldConfig"]["defaults"]["mappings"] = []

            # Create value mapping options
            value_options = {}
            for mapping in self.mappings:
                # Handle both StateMapping objects and dictionaries
                if isinstance(mapping, StateMapping):
                    # StateMapping object
                    key = str(mapping.value) if mapping.value is not None else "null"
                    value_options[key] = mapping.to_json_data()
                else:
                    # Dictionary - convert to StateMapping format
                    value = mapping.get("value")
                    key = str(value) if value is not None else "null"
                    result = {
                        "index": mapping.get("index", 0),
                        "text": mapping.get("text", ""),
                    }
                    if mapping.get("color"):
                        result["color"] = mapping["color"]
                    value_options[key] = result

            # Add the value mapping
            json["fieldConfig"]["defaults"]["mappings"].append(
                {"type": "value", "options": value_options}
            )

            # Add range mapping for N/A values
            json["fieldConfig"]["defaults"]["mappings"].append(
                {
                    "type": "range",
                    "options": {
                        "from": 0,
                        "to": 1,
                        "result": {"index": 0, "text": "N/A"},
                    },
                }
            )

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
    """TimeSeries: Allow settings decimals & legend values and backward-compat for showLegend"""

    decimals: int = attr.ib(default=0, validator=attr.validators.instance_of(int))
    legendValues: List[str] = attr.ib(  # pylint: disable=invalid-name
        default=[], validator=attr.validators.instance_of(list)
    )
    spanNulls: Union[int, bool] = attr.ib(
        default=False, validator=attr.validators.instance_of((int, bool))
    )
    showLegend: bool = attr.ib(  # pylint: disable=invalid-name
        default=True, validator=attr.validators.instance_of(bool)
    )

    minValue = attr.ib(default=None)  # pylint: disable=invalid-name
    maxValue = attr.ib(default=None)  # pylint: disable=invalid-name

    def __attrs_post_init__(self):  # type: ignore
        # If showLegend is False, hide legend via legendDisplayMode
        if not self.showLegend:
            # legendDisplayMode is an attribute on parent class
            setattr(self, "legendDisplayMode", "hidden")

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.decimals:
            json["options"]["decimals"] = self.decimals
        if self.legendValues:
            json["options"]["legend"]["calcs"] = self.legendValues
        if self.minValue is not None:
            json["fieldConfig"]["defaults"]["min"] = self.minValue
        if self.maxValue is not None:
            json["fieldConfig"]["defaults"]["max"] = self.maxValue
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

    def verify_datasources(self) -> "Dashboard":
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


@attr.s
class RawPanel(core.Panel):
    """Wrap an existing panel JSON for passthrough."""

    rawJson: dict = attr.ib(kw_only=True, factory=dict)  # pylint: disable=invalid-name

    def to_json_data(self):  # type: ignore
        return self.rawJson
