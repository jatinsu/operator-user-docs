# Cluster Logging Operator

The Cluster Logging Operator (CLO) manages log collection and forwarding on OpenShift clusters. It deploys and configures Vector as the log collector, supporting complex log routing through inputs, outputs, filters, and pipelines defined via the ClusterLogForwarder custom resource.

## Key Capabilities

- Collects logs from multiple sources: application containers, infrastructure (node/journald), and audit logs (Kubernetes API, OpenShift API, auditd, OVN)
- Transforms and filters logs using configurable pipelines (drop, prune, parse, multiline detection, API audit filtering, OpenShift labels)
- Forwards logs to 13+ destinations: LokiStack, Elasticsearch, Splunk, AWS CloudWatch, AWS S3, Google Cloud Logging, Azure Monitor, Kafka, Syslog, HTTP, OTLP, Loki, and Azure Logs Ingestion
- Manages the full lifecycle of log collectors as Kubernetes DaemonSets
- Provides metrics and observability for the logging infrastructure

## Documentation Index

- [Getting Started](getting-started.md) - Prerequisites, installation, and quickstart
- [Deployment Guide](deployment.md) - Installation via OLM, upgrades, and removal
- [Configuration Reference](configuration-reference.md) - All user-facing configuration options
- [API Reference](api-reference.md) - ClusterLogForwarder and LogFileMetricExporter CRD field reference
- [Troubleshooting](troubleshooting.md) - Common issues, diagnostics, and must-gather
- [Examples](examples/) - Example ClusterLogForwarder configurations

## Architecture Overview

```
ClusterLogForwarder CR
        |
    CLO Reconciler
        |
  Vector Configuration
        |
  Vector Collectors (DaemonSet)
    |         |         |
 Sources   Transforms   Sinks
(app/infra/  (filters,   (output
  audit)    enrichment)  destinations)
```

## Custom Resources

| Resource | API Group | Description |
|----------|-----------|-------------|
| ClusterLogForwarder | observability.openshift.io/v1 | Defines log collection inputs, processing filters, output destinations, and routing pipelines |
| LogFileMetricExporter | logging.openshift.io/v1alpha1 | Exports metrics about log file volumes on each node |

## Key Concepts

- **Inputs**: Define what logs to collect. Built-in input types include application container logs, infrastructure logs (node journals, container platform components), and audit logs (Kubernetes API server, OpenShift API server, auditd, OVN). You can also configure receiver inputs to accept logs sent to the collector over HTTP or Syslog.

- **Outputs**: Specify where to send collected logs. The CLO supports 13+ destination types including LokiStack, Elasticsearch, Splunk, AWS CloudWatch, AWS S3, Google Cloud Logging, Azure Monitor, Kafka, Syslog, HTTP, OTLP, Loki, and Azure Logs Ingestion. Each output type has its own authentication and connection settings.

- **Filters**: Control how logs are transformed as they pass through the pipeline. Available filter types include drop (discard logs matching conditions), prune (remove or keep specific fields), parse (extract structured data from log messages), multiline error detection (reassemble multi-line stack traces), API audit filtering (reduce audit log volume by severity), and OpenShift labels (enrich logs with pod label metadata).

- **Pipelines**: Define routing rules that connect inputs to outputs, optionally passing logs through one or more filters along the way. A single ClusterLogForwarder can define multiple pipelines, allowing different log sources to be processed and routed independently.

- **Service Account**: The collector pods run under a Kubernetes service account that must be configured with appropriate RBAC permissions. The service account controls which log types the collector is authorized to gather. For example, collecting application logs requires `collect-application-logs` permissions, while audit log collection requires `collect-audit-logs` permissions.
