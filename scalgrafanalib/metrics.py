import re
import typing

TMetricMetadata = typing.TypeVar(  # pylint: disable=invalid-name
    "TMetricMetadata", bound="MetricMetadata"
)


class MetricMetadata:
    """Base class for storing metric-related metadata"""

    def __init__(self):
        self.description: typing.Optional[str] = None
        self.unit: typing.Optional[str] = None

    def with_description(self: TMetricMetadata, desc: str) -> TMetricMetadata:
        self.description = desc
        return self

    def with_unit(self: TMetricMetadata, unit: str) -> TMetricMetadata:
        self.unit = unit
        return self


TMetric = typing.TypeVar("TMetric", bound="Metric")  # pylint: disable=invalid-name


class Metric(MetricMetadata):
    """Base class for prometheus metric, allowing to statically validate the labels"""

    LABEL_EXPR = re.compile('^\\s*([A-Za-z_-]+)\\s*(=|!=|=~|!~)\\s*".*"\\s*$')

    def __init__(self, name: str, *labels: str, **kwargs: str) -> None:
        super().__init__()
        self.name = name
        self.labels = [*labels, *kwargs.keys()]
        self.default_labels = self.parse_matchers(**kwargs)

    def check_label(self, label: str) -> str:
        """Return the label if valid"""
        if self.labels and label not in self.labels:
            raise ValueError(f"Invalid label `{label}` for {self.name}")
        return label

    def extract_label(self, expr: str) -> str:
        """Return the label of the matcher, if valid"""
        match = self.LABEL_EXPR.fullmatch(expr)
        if match is None:
            raise ValueError(f"Invalid matcher `{expr}` for {self.name}")
        return self.check_label(match.group(1))

    def parse_matchers(self, *args: str, **kwargs: str) -> typing.Dict[str, str]:
        return {self.extract_label(arg): arg for arg in args} | {
            self.check_label(label): f'{label}="{expr}"'
            for label, expr in kwargs.items()
        }

    def with_defaults(self: TMetric, *args: str, **kwargs: str) -> TMetric:
        self.default_labels |= self.parse_matchers(*args, **kwargs)
        return self

    def __call__(self, *args: str, **kwargs: str) -> str:
        matchers = self.default_labels | self.parse_matchers(*args, **kwargs)
        selector = ", ".join([expr for _, expr in matchers.items()])
        return self.name + "{" + selector + "}"


class CounterMetric(Metric):
    """Class for prometheus counter metric"""

    def __call__(self, *args: str, **kwargs: str) -> str:
        return self.raw(*args, **kwargs) + "[$__rate_interval]"

    def raw(self, *args: str, **kwargs: str) -> str:
        return super().__call__(*args, **kwargs)


class BucketMetric(MetricMetadata):
    """Class for prometheus bucket metric"""

    def __init__(self, name: str, *labels: str, **kwargs: str) -> None:
        super().__init__()
        self.bucket = CounterMetric(name + "_bucket", "le", *labels, **kwargs)
        self.count = CounterMetric(name + "_count", *labels, **kwargs)
        self.sum = CounterMetric(name + "_sum", *labels, **kwargs)

    def with_defaults(self, *args: str, **kwargs: str) -> "BucketMetric":
        for metric in [self.bucket, self.count, self.sum]:
            metric.with_defaults(*args, *kwargs)
        return self
