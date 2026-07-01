# ClusterLogForwarder Example Configurations

Example `ClusterLogForwarder` resources using the `observability.openshift.io/v1` API.

**Prerequisite:** The Cluster Logging Operator must be installed before applying any of these examples. See [Getting Started](../getting-started.md) for installation instructions.

| File | Description |
|------|-------------|
| [lokistack-basic.yaml](lokistack-basic.yaml) | Basic forwarding of all log types to a LokiStack instance using service account authentication |
| [elasticsearch.yaml](elasticsearch.yaml) | Forwarding application logs to an external Elasticsearch 8.x cluster with username/password auth and TLS |
| [splunk.yaml](splunk.yaml) | Forwarding application and infrastructure logs to a Splunk HEC endpoint |
| [cloudwatch.yaml](cloudwatch.yaml) | Forwarding application and infrastructure logs to AWS CloudWatch using static access key credentials |
| [kafka.yaml](kafka.yaml) | Forwarding application logs to Kafka with SASL/SCRAM-SHA-512 authentication and TLS |
| [syslog.yaml](syslog.yaml) | Forwarding infrastructure logs to a remote syslog server over TLS using RFC 5424 |
| [multi-output-with-filters.yaml](multi-output-with-filters.yaml) | Advanced configuration with custom inputs, drop/multiline filters, and multiple outputs (LokiStack + Splunk) |
