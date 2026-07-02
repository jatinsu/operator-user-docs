# Configuration Reference

This document covers all user-facing configuration options beyond the CRD field definitions. For complete CRD field details, see the [API Reference](api-reference.md).

## Annotations

The following annotations can be set on ClusterLogForwarder resources to control collector behavior:

| Annotation | Values | Description |
|-----------|--------|-------------|
| `observability.openshift.io/log-level` | `trace`, `debug`, `info`, `warn`, `error`, `off` | Sets the Vector collector log level |
| `observability.openshift.io/use-apiserver-cache` | `"true"` | Enables API server caching for kube-api metadata lookups, reducing API server load |

## Environment Variables

The following environment variables affect operator behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `WATCH_NAMESPACE` | Comma-separated list of namespaces the operator watches | Required (set by OLM) |
| `LOG_LEVEL` | Operator log level (integer) | `0` |
| `RELATED_IMAGE_VECTOR` | Vector container image | Set by operator CSV |
| `RELATED_IMAGE_LOG_FILE_METRIC_EXPORTER` | Log file metric exporter container image | Set by operator CSV |

## Supported Output Destinations

The ClusterLogForwarder supports 13 output types. Each type has specific protocol, authentication, and compression capabilities:

| Output Type | Protocols | Authentication Methods | Compression Options | Notes |
|------------|-----------|----------------------|-------------------|-------|
| `azureLogsIngestion` | HTTPS | Client Secret, Workload Identity | - | Azure Monitor Logs Ingestion API |
| `azureMonitor` | HTTPS | Shared Key | - | DEPRECATED |
| `cloudwatch` | HTTPS | AWS Access Key, IAM Role (STS), Assume Role | gzip, none, snappy, zlib, zstd | Dynamic group naming |
| `elasticsearch` | HTTP/HTTPS | Bearer Token, Basic Auth | none, gzip, zlib | Versions 6, 7, 8 |
| `googleCloudLogging` | HTTPS | Service Account, Workload Identity Federation | - | Project, folder, org, or billing account |
| `http` | HTTP/HTTPS | Bearer Token, Basic Auth | none, gzip, snappy, zlib | JSON or NDJSON format |
| `kafka` | TCP/TLS | SASL | none, snappy, zstd, lz4 | URL or broker list |
| `loki` | HTTP/HTTPS | Bearer Token, Basic Auth | none, gzip, snappy | Custom label keys, tenant key |
| `lokiStack` | HTTPS | Service Account Token | none, gzip, snappy | Red Hat managed Loki. Viaq or Otel data model |
| `otlp` | HTTP/HTTPS | Bearer Token, Basic Auth | gzip, snappy, zlib, zstd, none | OpenTelemetry Protocol |
| `s3` | HTTPS | AWS Access Key, IAM Role (STS), Assume Role | gzip, none, snappy, zlib, zstd | S3-compatible endpoints |
| `splunk` | HTTPS | HEC Token | none, gzip | Indexed fields, payload key |
| `syslog` | TCP/TLS/UDP | - | - | RFC3164 or RFC5424 |

## Input Types

### Built-in Inputs

The operator provides three built-in input types that cover standard log sources:

- **application**: Container logs from application workloads. This includes all namespaces that are not infrastructure namespaces (i.e., not `kube-*` or `openshift-*`).
- **infrastructure**: Node-level logs from journald and container logs from system namespaces (`kube-*`, `openshift-*`).
- **audit**: Audit logs from Kubernetes API server, OpenShift API server, auditd, and OVN.

### Custom Inputs

Custom inputs allow you to narrow the scope of log collection beyond the built-in types. Define them under `spec.inputs` in the ClusterLogForwarder:

- **Application input with filtering**: Use `application.namespaces` with glob patterns (e.g., `my-project-*`), `application.containers.includes`/`excludes` for container name filtering, and `application.selector.matchLabels` for pod label selectors.
- **Infrastructure input with source selection**: Use `infrastructure.sources` to select specific sources: `node` (journald logs) and/or `container` (infrastructure namespace container logs).
- **Audit input with source selection**: Use `audit.sources` to select specific audit sources: `kubeAPI`, `openshiftAPI`, `auditd`, and/or `ovn`.
- **Receiver input**: Accept logs sent to the collector from external sources. Supports `http` (for JSON-formatted log ingestion) and `syslog` (for syslog protocol ingestion) receiver types.

## Filter Types

Filters process log records in the pipeline between inputs and outputs. Define them under `spec.filters` and reference them by name in pipeline definitions.

### Drop Filter

Drops entire log records based on field conditions. Multiple conditions within a single `test` are ANDed together. Multiple `test` entries are ORed.

```yaml
filters:
- name: drop-debug
  type: drop
  drop:
  - test:
    - field: .level
      matches: "debug"
```

### Prune Filter

Removes or keeps specific fields from log records. Use `in` to list fields to remove, or `notIn` to list fields to keep (all others are removed). The fields `.log_type`, `.log_source`, and `.message` are required and cannot be pruned.

```yaml
filters:
- name: prune-fields
  type: prune
  prune:
    notIn:
    - .message
    - .kubernetes.namespace_name
    - .kubernetes.pod_name
    - .log_type
    - .log_source
```

### Kube API Audit Filter

Filters Kubernetes API audit events by verb, user, group, namespace, or resource. By default, events with response codes 404, 409, 422, and 429 are omitted (configurable via `omitResponseCodes`).

```yaml
filters:
- name: audit-filter
  type: kubeAPIAudit
  kubeAPIAudit:
    omitStages:
    - RequestReceived
    rules:
    - level: None
      resources:
      - group: ""
        resources: ["events"]
```

### Parse Filter

Parses unstructured log data into a structured format. No additional configuration is required beyond specifying the filter name and type.

```yaml
filters:
- name: parse-logs
  type: parse
```

### Detect Multiline Exception Filter

Detects and merges multiline exception stack traces into a single log entry. Supports Java, JavaScript, Ruby, Python, Go, PHP, and Dart exception formats. No additional configuration is required.

```yaml
filters:
- name: detect-exceptions
  type: detectMultilineException
```

### OpenShift Labels Filter

Adds custom labels to log records in the `openshift.labels` field. These labels can be used for downstream categorization or routing.

```yaml
filters:
- name: add-labels
  type: openshiftLabels
  openshiftLabels:
    team: "platform-eng"
    environment: "production"
```

## Tuning and Performance

### Delivery Modes

Control the trade-off between durability and throughput using `spec.outputs[].tuning.delivery`:

- **AtLeastOnce**: Uses durable (disk-backed) buffering. Logs may be duplicated on crash recovery but are not lost. This is the safer option for critical log data.
- **AtMostOnce**: Uses in-memory buffering only. Provides higher throughput, but logs in the buffer are lost if the collector crashes.

### Output Tuning Parameters

Most output types support the following tuning fields under `spec.outputs[].tuning`:

| Parameter | Type | Description |
|-----------|------|-------------|
| `deliveryMode` | string | `AtLeastOnce` or `AtMostOnce` (see above) |
| `maxWrite` | Quantity | Maximum payload size in bytes for a single send to the output |
| `minRetryDuration` | Duration | Minimum time to wait between retry attempts after a delivery failure |
| `maxRetryDuration` | Duration | Maximum time to wait between retry attempts after a delivery failure |
| `compression` | string | Compression algorithm (varies by output type) |

### Rate Limiting

Rate limiting can be applied at two levels:

- **Output-level**: Set `spec.outputs[].rateLimit.maxRecordsPerSecond` to limit the rate of records sent to a specific output.
- **Input-level**: Set `spec.inputs[].application.tuning.rateLimitPerContainer.maxRecordsPerSecond` to limit the rate of log collection per container.

### Collector Resources

Set resource requests and limits for the collector pods under `spec.collector.resources`:

```yaml
spec:
  collector:
    resources:
      limits:
        cpu: "2"
        memory: 2Gi
      requests:
        cpu: 500m
        memory: 512Mi
```

### MaxUnavailable Rollout

Controls the pace of the DaemonSet rollout under `spec.collector.maxUnavailable`. This determines how many collector pods can be unavailable simultaneously during an update. The value can be an absolute number or a percentage (e.g., `"25%"`).

## TLS Configuration

### Output TLS

Configure TLS for output connections under `spec.outputs[].tls`:

- **insecureSkipVerify**: Set to `true` to skip server certificate validation. Not recommended for production environments.
- **securityProfile**: Set the TLS security profile to `Old`, `Intermediate`, `Modern`, or `Custom`. When using `Custom`, you can specify individual cipher suites and minimum TLS version.
- **CA, certificate, key**: Reference TLS material from Secrets or ConfigMaps using `ca`, `certificate`, and `key` fields, each specifying a `secretName` or `configMapName` and the corresponding `key` within.

### Input TLS (Receivers)

For receiver-type inputs, TLS is configured under `spec.inputs[].receiver.tls`:

- If no TLS configuration is provided, the operator automatically injects a service-serving certificate.
- You can specify custom TLS material using `ca`, `certificate`, `key`, and optionally `passphrase` fields.

## Network Policies

Control network access for the collector pods using `spec.collector.networkPolicy`:

- **AllowAllIngressEgress** (default): No network restrictions are applied. The collector can communicate freely.
- **RestrictIngressEgress**: Restricts network traffic to only the connections required for the configured inputs and outputs. This hardens the collector's network posture.

## Management State

Set via `spec.managementState`:

- **Managed** (default): The operator actively reconciles the ClusterLogForwarder resource, deploying and updating collector pods as needed.
- **Unmanaged**: The operator stops managing the resource. Existing collector pods remain running but are no longer updated. This allows manual editing of the Vector configuration for advanced debugging scenarios.

## Metrics Collection Profiles

Control which metrics the collector exposes by setting the label `monitoring.openshift.io/collection-profile` on the ClusterLogForwarder resource:

- **full**: All available metrics are collected and exposed.
- **minimal**: A reduced set of metrics is collected, lowering overhead on the monitoring stack.
- **telemetry**: Only telemetry-specific metrics are collected.

---

For complete CRD field definitions and schema details, see the [API Reference](api-reference.md).
