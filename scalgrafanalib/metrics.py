import re
import typing

class Metric:
    """Base class for prometheus metric, allowing to statically validate the labels"""

    def __init__(self, name: str, *labels: str, **kwargs: str) -> None:
        self.name = name
        self.labels = [*labels, *kwargs.keys()]
        self.default_labels = self.parse_matchers(**kwargs)
        self.description: typing.Optional[str] = None
        self.unit: typing.Optional[str] = None

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

    def with_defaults(self, *args: str, **kwargs: str) -> "Metric":
        self.default_labels += self.parse_matchers(*args, **kwargs)
        return self

    def with_description(self, desc: str) -> "Metric":
        self.description = desc
        return self

    def with_unit(self, unit: str) -> "Metric":
        self.unit = unit
        return self

    def __call__(self, *args: str, **kwargs: str) -> str:
        selector = ", ".join(
            [*self.default_labels, *self.parse_matchers(*args, **kwargs)]
        )
        return self.name + "{" + selector + "}"


class CounterMetric(Metric):
    def __call__(self, *args: str, **kwds: str) -> str:
        return super().__call__(*args, **kwds) + '[$__rate_interval]'


class BucketMetric:
    """Class for prometheus bucket metric"""

    def __init__(self, name: str, *labels: str, **kwargs: str) -> None:
        self.bucket = CounterMetric(name + "_bucket", "le", *labels, **kwargs)
        self.count = CounterMetric(name + "_count", *labels, **kwargs)
        self.sum = CounterMetric(name + "_sum", *labels, **kwargs)
        self.description: typing.Optional[str] = None
        self.unit: typing.Optional[str] = None

    def with_defaults(self, *args: str, **kwargs: str) -> "BucketMetric":
        for metric in [self.bucket, self.count, self.sum]:
            metric.with_defaults(*args, *kwargs)
        return self

    def with_description(self, desc: str) -> "BucketMetric":
        self.description = desc
        return self

    def with_unit(self, unit: str) -> "BucketMetric":
        self.unit = unit
        return self
