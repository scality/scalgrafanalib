import attr
from typing import Any, Dict, TypeVar
from grafanalib import core  # type: ignore

Json = Dict[str, Any]
Self = TypeVar("Self")

# SimpleTooltip : simple, "modern" tooltip configuration
# Inherit from Tooltip to allow using in place of "usual" tooltip class
@attr.s
class Tooltip(core.Tooltip):
    show: bool = attr.ib(default=True, validator=attr.validators.instance_of(bool))
    showHistogram: bool = attr.ib(
        default=True, validator=attr.validators.instance_of(bool)
    )

    def to_json_data(self) -> Json:
        return {"show": self.show, "showHistogram": self.showHistogram}


# Target: set default `intervalFactor` mode to 1
class Target(core.Target):
    def to_json_data(self) -> Json:
        self.intervalFactor = 1
        return super().to_json_data()


# TimeSeries: Allow settings decimals
@attr.s
class TimeSeries(core.TimeSeries):
    decimals: int = attr.ib(default=0, validator=attr.validators.instance_of(int))

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        if self.decimals:
            json["options"]["decimals"] = self.decimals
        return json


# Dashboard: extension to make the dashboard a bit less verbose
class Dashboard(core.Dashboard):
    def __simplify(self, json: Json) -> Json:
        return dict(filter(lambda item: item[1] != None, json.items()))

    def to_json_data(self) -> Json:
        json = super().to_json_data()
        # Remove 'null' values from panels
        json["panels"] = [
            self.__simplify(panel.to_json_data()) for panel in json["panels"]
        ]
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
                assert panel.dataSource == None
            else:
                assert panel.dataSource in datasources
        return self
