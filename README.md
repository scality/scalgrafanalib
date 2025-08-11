# ScalGrafanaLib

A collection of helpers and utilities to streamline dashboard development with [GrafanaLib](https://github.com/weaveworks/grafanalib), designed to make dashboard creation more efficient, maintainable, and readable.

## Features

- **🚀 Quick Field Extensions**: Easily add missing fields not yet supported by GrafanaLib
- **� Simplified Dashboard Layer**: Intuitive abstraction layer for faster dashboard development
- **�🔒 Safe Metrics Class**: Type-safe and easier-to-use `Metrics` class with enhanced validation
- **📐 Layout Utilities**: Smart layout management for consistent dashboard organization

Future improvement ideas:

- Functions and operators to allow complete validation of PromQL expression when building the
  dashboard
- Automatic generation/detection of metrics from the actual "production" code (e.g. parsing
  node.js or Golang code), to avoid redundancy
- Sharing the metrics defintion (in each project) with other components, so they can be reused
- Library of reusable "standard" panels for common use cases, to reduce redundancy and enforce
  some uniformity accross dashboards. Could be things like "Request rate graph", "Up panel"...
- ...

## Installation

```bash
pip install scalgrafanalib
```

## Quick Start

```python
from scalgrafanalib import Dashboard, Panel, Metrics, layout
from grafanalib.core import Target, Stat, TimeSeries

# Define metrics using typed metric classes
class ServiceMetrics(Metrics):
    # Use CounterMetric for counters with automatic rate() functions
    requests_total = metrics.CounterMetric("http_requests_total", 
        "method", "status", namespace="${namespace}")
    
    # Use BucketMetric for histograms with quantile and rate functions
    request_duration = metrics.BucketMetric("http_request_duration_seconds",
        "method", "path", namespace="${namespace}")
    
    # Use Metric for gauges
    active_connections = metrics.Metric("active_connections_total",
        "service", namespace="${namespace}")

# Create dashboard with layout utilities
dashboard = Dashboard(
    title="Service Monitoring",
    tags=["service", "sli"],
    refresh="30s"
    panels = layout.column([
        layout.row([
            Stat(title="Request Rate", targets=[Target(expr=ServiceMetrics.requests_total.rate())]),
            Stat(title="Active Connections", targets=[Target(expr=ServiceMetrics.active_connections())]),
        ], height=4),
        layout.row([
            TimeSeries(title="Request Duration P95", 
                    targets=[Target(expr=ServiceMetrics.request_duration.quantile(0.95))]),
        ], height=6)
    ),
])
```

## Best Practices

### 1. Organize Metrics with Typed Classes

Define your metrics using typed classes that provide built-in functionality:

- avoid repeatedly referencing the full metrics name
- allows defining default values of labels, which can be overridden
- validates that only valid label names are used (according to the definition of the metrics)
- Implicit use the `[$__rate_interval]` on counters, for simplicity
- Enforce use of "submetrics" for bucket metrics (`xxxx_count`, `xxx_buckets`)
- This allows easily supporting filters, by referencing template parameter in default label value
  (like `namespace` in the examples below)

```python
from scalgrafanalib import metrics

class SorbetMetrics(Metrics):
    """Cold storage service metrics with proper typing"""

    # Counter metrics with automatic rate() and increase() methods
    REQUESTS_TOTAL = metrics.CounterMetric("sorbetd_server_requests_total",
        "method", "action", "result", "service", namespace="${namespace}").with_defaults(
        'service=~"$service"')

    # Bucket metrics for histograms with quantile(), count(), sum() methods
    REQUEST_DURATION = metrics.BucketMetric("sorbetd_server_request_duration_seconds",
        "method", "action", "service", namespace="${namespace}").with_defaults('service=~"$service"')

    JOB_DURATION = metrics.BucketMetric("sorbetd_server_job_duration_seconds",
        "service", "type", "status", namespace="${namespace}").with_defaults('service=~"$service"')

    # Gauge metrics for current values
    ACTIVE_REQUESTS = metrics.Metric("sorbetd_server_active_requests",
        "method", "action", "service", namespace="${namespace}").with_defaults('service=~"$service"')

    ACTIVE_SESSIONS = metrics.Metric("sorbetd_server_active_sessions",
        "service", namespace="${namespace}").with_defaults('service=~"$service"')

## Usage examples

# rate(sorbetd_server_requests_total{rate="get"}[$__rate_interval])
request_rate = 'rate(' + SorbetMetrics.REQUESTS_TOTAL.rate(method='get') + ')'

# histogram_quantile(0.95, sorbetd_server_request_duration_seconds_bucket)
p95_latency = 'histogram_quantile(0.95, ' + SorbetMetrics.REQUEST_DURATION.bucket() + ')'

# sorbetd_server_job_duration_seconds_count{state="Success"}
job_count = SorbetMetrics.JOB_DURATION.count(status='Success')
```

### 2. Use Layout Utilities for Organized Dashboard Structure

ScalGrafanaLib provides powerful layout utilities for organizing panels efficiently.
This makes the definition easier, by automatically computing the position and distributing the
available size.

```python
from scalgrafanalib import layout
from grafanalib.core import RowPanel, Stat, TimeSeries, Heatmap, GaugePanel

# Create organized dashboard structure using layout.column and layout.row
dashboard.panels = layout.column([
    # Status overview row with stats. The width is automatically computed by distributing the space
    # accross the panels.
    layout.row([
        up_stat, active_sessions, active_requests, active_jobs, success_rate,
        requests_rate, jobs_rate, archive_pack_rate,
    ], height=4),
    
    # Section headers using RowPanel
    RowPanel(title="Jobs"),
    
    # Mixed panel row with resizing
    layout.row([
        jobs_timeseries, # remaining space is distributed to the panels which do not already have a size
        layout.resize([queued_jobs], width=8), 
        layout.resize([jobs_by_type_pie], width=4),
    ], height=8),

    # Heatmap row for detailed analysis
    layout.row([
        archive_duration_heatmap, 
        restore_duration_heatmap, 
        delete_duration_heatmap
    ], height=6),
    
    RowPanel(title="Requests"),
    layout.row([
        layout.resize([request_time_heatmap], width=8), 
        requests_by_action_table
    ], height=6),
])
```

### 3. Create Panels with Type Safety and Metric Functions

Build various panel types using metric methods and built-in helpers.
`grafanalib` provides most types, but some more recent fields may not be supported. In such case,
the type from `scalgrafanalib` may be used as a drop-in replacement, with the extra missing fields.

```python
from grafanalib.core import Stat, TimeSeries, Heatmap
from grafanalib import formatunits as UNITS
from scalgrafanalib import GaugePanel, PieChart, Target

# Stats with thresholds and proper formatting
up_stat = Stat(
    title="Up",
    description="Number of instances running",
    dataSource="${DS_PROMETHEUS}",
    reduceCalc="last",
    targets=[Target(expr='sum(' + Metrics.Up() + ')'],
    thresholds=[
        Threshold("red", 0, 0.0),
        Threshold("green", 1, 1.0),
    ],
)

# Success rate gauge with calculated expressions
success_rate = GaugePanel(
    title='Success rate',
    description="Percentage of successful jobs",
    dataSource='${DS_PROMETHEUS}',
    calc='mean',
    decimals=2,
    format=UNITS.PERCENT_FORMAT,
    min=0,
    max=100,
    targets=[Target(
        expr='\n'.join([
            '100 * sum(rate(' + Metrics.JOB_DURATION.count(status='Success') + '))',
            '      /',
            '      sum(rate(' + Metrics.JOB_DURATION.count() + '))',
            '>= 0 or vector(100)',
        ]),
    )],
    thresholds=[
        Threshold('red',     1, 0.0),
        Threshold('orange',  2, 95.0),
        Threshold('yellow',  3, 99.0),
        Threshold('green',   4, 100.0),
    ],
)

# Heatmaps for duration analysis
job_duration_heatmap = Heatmap(
    title="Archive job duration",
    description="Time to process an archive job",
    dataSource="${DS_PROMETHEUS}",
    dataFormat="tsbuckets",
    maxDataPoints=25,
    yAxis=YAxis(format=UNITS.SECONDS),
    hideZeroBuckets=True,
    targets=[Target(
        expr='sum(rate(' + Metrics.JOB_DURATION.bucket(type='put') + ')) by(le)',
        format="heatmap",
        legendFormat="{{ le }}",
    )],
)

# Time series with legend configuration
jobs_timeseries = TimeSeries(
    title="Jobs over time",
    description="Rate of jobs grouped by type",
    dataSource="${DS_PROMETHEUS}",
    legendPlacement="bottom",
    lineInterpolation="smooth",
    unit=UNITS.OPS_PER_SEC,
    targets=[
        Target(
            expr='sum(rate(' + Metrics.JOB_DURATION.count() + ')) by(type)',
            legendFormat="{{type}}",
        ),
    ],
)

# Pie chart for distribution
jobs_by_type = PieChart(
    title="Job type breakdown",
    description="Job distribution by type",
    dataSource="${DS_PROMETHEUS}",
    displayLabels=['name', 'percent'],
    unit=UNITS.SHORT,
    targets=[
        Target(
            expr='sum(rate(' + Metrics.JOB_DURATION.count() + ')) by(type)',
            legendFormat="{{type}}",
        ),
    ],
)
```

### 4. Generate Panels Dynamically for Different Metrics

Use list comprehensions and generators to create multiple similar panels efficiently:

```python
# Generate heatmaps for different job types
job_durations = [
    Heatmap(
        title=name + " job duration",
        description="Time to process a " + type + " job for each operation",
        dataSource="${DS_PROMETHEUS}",
        dataFormat="tsbuckets",
        maxDataPoints=25,
        tooltip=Tooltip(show=True, showHistogram=True),
        yAxis=YAxis(format=UNITS.SECONDS),
        color=HeatmapColor(mode="opacity"),
        hideZeroBuckets=True,
        targets=[Target(
            expr='sum(rate(' + Metrics.JOB_DURATION.bucket(type=type) + ')) by(le)',
            format="heatmap",
            legendFormat="{{ le }}",
        )],
    )
    for name, type in {
        'Archive': 'put',
        'Restore': 'get',
        'Delete': 'del',
    }.items()
]

# Generate throttling duration heatmaps
throttling_duration = [
    Heatmap(
        title="Throttling " + name + " duration",
        description="Duration of throttling " + name + " operation, for each operation",
        dataSource="${DS_PROMETHEUS}",
        dataFormat="tsbuckets",
        maxDataPoints=25,
        tooltip=Tooltip(show=True, showHistogram=True),
        yAxis=YAxis(format=UNITS.SECONDS),
        color=HeatmapColor(mode="opacity"),
        hideZeroBuckets=True,
        targets=[Target(
            expr='sum(rate(' + metric.bucket() + ')) by(le)',
            format="heatmap",
            legendFormat="{{ le }}",
        )],
    )
    for name, metric in {
        "read": Metrics.THROTTLING_READ_DURATION,
        "write": Metrics.THROTTLING_WRITE_DURATION,
    }.items()
]
```

### 5. Inputs and Template parameters

Create reusable dashboards with proper templating and inputs, which can be set by the operator to
ensure the dashboard does not look farther than its scope.

In development, when manually importing the JSON dashboard in Grafana, Grafana will prompt values
for `input` parameters, and default to the value set in the dashboard. Setting the right default
thus allows to make development loop quite efficient, while the dashboard can also be deployed in
production with the proper scope.

`Templating` on the other hand allows having dynamic filters, based on the metrics and labels, and
which are presented to the user on top of the dashboards.

- For proper scoping, the PromQL expression in the template should typically use the value of some
  input parameters.
- Inputs and templates used for scoping should be set as default values, in the Metrics definitions,
  to avoid redundancy. This also makes refactoring easier, typically when more filtering is needed.
- Grafana uses the same syntax (`${foo}` and `$foo`) for input parameters and dashboard variables.
  By convention, use `${foo}` for inputs and `$foo` for templates, to allow more easily making the
  distinction.

```python
from grafanalib.core import (
    DataSourceInput, ConstantInput, Template, Templating, 
    Dashboard as GrafanaDashboard
)

# Create dashboard with inputs and templating like in sorbetd-dashboard.py
dashboard = GrafanaDashboard(
    title="Cold Storage Backend",
    description="Dashboard for Cold Storage backend",
    editable=True,
    refresh="30s",
    tags=["sorbet"],
    timezone="",
    inputs=[
        DataSourceInput(
            name="DS_PROMETHEUS",
            label="Prometheus",
            pluginId="prometheus",
            pluginName="Prometheus",
        ),
        ConstantInput(
            name="namespace",
            label="namespace",
            description="Namespace associated with the Zenko instance",
            value="zenko",
        ),
        ConstantInput(
            name="job_sorbet_azure",
            label="job",
            description="Name of the Sorbetd Azure job",
            value="artesca-data-cold-sorbet-azure",
        ),
    ],
    templating=Templating([
        Template(
            dataSource='${DS_PROMETHEUS}',
            label='Location',
            multi=True,
            includeAll=True,
            name='service',
            query='label_values(' + Metrics.REQUESTS_TOTAL(job="${job_sorbet_azure}") + '}, service)',
            regex='/(?<value>${job_sorbet_azure}-(?<text>.*))/',
        ),
    ]),
)
```

### 7. Complete Dashboard Example

Here's how to put it all together, following the sorbetd-dashboard.py pattern:

```python
from grafanalib.core import (
    DataSourceInput, ConstantInput, Template, Templating,
    Dashboard as GrafanaDashboard, RowPanel
)
from scalgrafanalib import layout, metrics, GaugePanel, Target

class Metrics:
    """Define all metrics for the dashboard"""
    REQUESTS_TOTAL = metrics.CounterMetric("sorbetd_server_requests_total",
        "method", "action", "result", "service", namespace="${namespace}").with_defaults(
        'service=~"$service"')
    REQUEST_DURATION = metrics.BucketMetric("sorbetd_server_request_duration_seconds",
        "method", "action", "service", namespace="${namespace}").with_defaults('service=~"$service"')
    ACTIVE_REQUESTS = metrics.Metric("sorbetd_server_active_requests",
        "method", "action", "service", namespace="${namespace}").with_defaults('service=~"$service"')
    JOB_DURATION = metrics.BucketMetric("sorbetd_server_job_duration_seconds",
        "service", "type", "status", namespace="${namespace}").with_defaults('service=~"$service"')

# Create individual panels using metric methods
up_stat = Stat(
    title="Up",
    description="Number of instances which are up and running",
    dataSource="${DS_PROMETHEUS}",
    reduceCalc="last",
    targets=[Target(expr='sum(' + Metrics.Up() + ')'],
    thresholds=[
        Threshold("red", 0, 0.0),
        Threshold("green", 1, 1.0),
    ],
)

success_rate = GaugePanel(
    title='Success rate',
    description="Percentage of successful/failed jobs",
    dataSource='${DS_PROMETHEUS}',
    calc='mean',
    decimals=2,
    format=UNITS.PERCENT_FORMAT,
    min=0,
    max=100,
    targets=[Target(
        expr='\n'.join([
            '100 * sum(rate(' + Metrics.JOB_DURATION.count(status='Success') + '))',
            '      /',
            '      sum(rate(' + Metrics.JOB_DURATION.count() + '))',
            '>= 0 or vector(100)',
        ]),
    )],
    thresholds=[
        Threshold('red',     1, 0.0),
        Threshold('orange',  2, 95.0),
        Threshold('yellow',  3, 99.0),
        Threshold('green',   4, 100.0),
    ],
)

# Generate multiple similar panels using list comprehensions
job_durations = [
    Heatmap(
        title=name + " job duration",
        description="Time to process a " + job_type + " job",
        dataSource="${DS_PROMETHEUS}",
        dataFormat="tsbuckets",
        targets=[Target(
            expr='sum(rate(' + Metrics.JOB_DURATION.bucket(type=job_type) + ')) by(le)',
            format="heatmap",
        )],
    )
    for name, job_type in {
        'Archive': 'put',
        'Restore': 'get',
        'Delete': 'del',
    }.items()
]

# Final dashboard assembly
dashboard = GrafanaDashboard(
    title="Cold Storage Backend",
    description="Dashboard for Cold Storage backend",
    editable=True,
    refresh="30s",
    tags=["sorbet"],
    inputs=[
        DataSourceInput(name="DS_PROMETHEUS", label="Prometheus", pluginId="prometheus"),
        ConstantInput(name="namespace", label="namespace", value="zenko"),
    ],
    templating=Templating([
        Template(
            dataSource='${DS_PROMETHEUS}',
            name='service',
            query='label_values(' + Metrics.REQUESTS_TOTAL(job="${job_sorbet_azure}") + '}, service)',
            multi=True,
            includeAll=True,
        ),
    ]),
    panels=layout.column([
        # Overview stats row
        layout.row([
            up_stat, active_sessions_stat, success_rate, requests_rate_stat,
        ], height=4),
        
        # Jobs section
        RowPanel(title="Jobs"),
        layout.row([
            jobs_timeseries,
            layout.resize([jobs_by_type_pie], width=4),
        ], height=8),
        layout.row(job_durations, height=6),
        
        # Requests section
        RowPanel(title="Requests"),
        layout.row([
            layout.resize([request_time_heatmap], width=8),
            requests_by_action_table,
        ], height=6),
    ]),
).auto_panel_ids().verify_datasources()
```

## License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [GrafanaLib](https://github.com/weaveworks/grafanalib) - The core library this project extends
- [Grafana](https://grafana.com/) - The visualization platform
