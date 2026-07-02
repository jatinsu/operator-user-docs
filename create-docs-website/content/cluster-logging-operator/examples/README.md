# Example ClusterLogForwarder Configurations

These examples demonstrate common log forwarding configurations for the Cluster Logging Operator.

**Prerequisite**: The Cluster Logging Operator must be installed and the ClusterLogForwarder CRD must be registered before applying any of these examples. See the [Getting Started](../getting-started.md) guide for installation instructions.

## Examples

| File | Description |
|------|-------------|
| [lokistack-basic.yaml](lokistack-basic.yaml) | Forward application and infrastructure logs to a LokiStack instance |
| [cloudwatch-sts.yaml](cloudwatch-sts.yaml) | Forward all log types to AWS CloudWatch using IAM role (STS) authentication |
| [kafka-sasl.yaml](kafka-sasl.yaml) | Forward application and infrastructure logs to Kafka with SASL authentication and TLS |
| [splunk-hec.yaml](splunk-hec.yaml) | Forward application and infrastructure logs to Splunk via HEC |
| [syslog-rfc5424.yaml](syslog-rfc5424.yaml) | Forward infrastructure logs to a remote syslog server using RFC5424 format |
| [multi-output-filtered.yaml](multi-output-filtered.yaml) | Multi-output setup with custom inputs, drop/prune filters, Elasticsearch and S3 outputs |

All examples require a service account named `collector` with appropriate ClusterRole bindings. See the [Deployment Guide](../deployment.md#service-account-and-rbac-setup) for RBAC setup.
