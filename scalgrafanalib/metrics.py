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

    def is_valid_label(self, label: str) -> bool:
        return not self.labels or label in self.labels

    def is_valid_matcher(self, matcher: str) -> bool:
        match = re.fullmatch('^\\s*([A-Za-z_-]+)\\s*(=|!=|=~|!~)\\s*".*"\\s*$', matcher)
        return match is not None and self.is_valid_label(match.group(1))

    def parse_matchers(self, *args: str, **kwargs: str) -> typing.List[str]:
        for arg in args:
            assert self.is_valid_matcher(
                arg
            ), f"Invalid matcher `{arg}` for {self.name}"
        for kwarg in kwargs:
            assert self.is_valid_label(
                kwarg
            ), f"Invalid label `{kwarg}` for {self.name}"
        return [*args, *[k + '="' + str(v) + '"' for k, v in kwargs.items()]]

    def with_defaults(self: TMetric, *args: str, **kwargs: str) -> TMetric:
        self.default_labels += self.parse_matchers(*args, **kwargs)
        return self

    def __call__(self, *args: str, **kwargs: str) -> str:
        selector = ", ".join(
            [*self.default_labels, *self.parse_matchers(*args, **kwargs)]
        )
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
