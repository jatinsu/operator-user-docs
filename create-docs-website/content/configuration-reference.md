# ClusterLogForwarder Configuration Reference

Complete field reference for the `ClusterLogForwarder` custom resource (API group `observability.openshift.io/v1`). Every field documented here corresponds to a Go struct in the operator source code under `api/observability/v1/`.

---

## Table of Contents

1. [ClusterLogForwarderSpec (Top-level)](#1-clusterlogforwarderspec-top-level)
2. [CollectorSpec](#2-collectorspec)
3. [Input Types](#3-input-types)
4. [Output Types](#4-output-types)
5. [Filter Types](#5-filter-types)
6. [Authentication Types](#6-authentication-types)
7. [TLS Configuration](#7-tls-configuration)
8. [Tuning Options](#8-tuning-options)
9. [Dynamic Template Syntax](#9-dynamic-template-syntax)

---

## 1. ClusterLogForwarderSpec (Top-level)

The `spec` of a `ClusterLogForwarder` resource. The resource name itself must match the pattern `^[a-z][a-z0-9-]{1,61}[a-z0-9]$`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `managementState` | `string` | No | `Managed` | Controls whether the operator manages this resource. Values: `Managed`, `Unmanaged`. |
| `serviceAccount` | [ServiceAccount](#serviceaccount) | Yes | - | ServiceAccount used by collector pods to authenticate with outputs. |
| `collector` | [CollectorSpec](#2-collectorspec) | No | - | Collector pod deployment configuration (resources, scheduling, network policy). |
| `inputs` | \[\][InputSpec](#3-input-types) | No | - | Custom input definitions. Three built-in inputs are always available: `application`, `infrastructure`, `audit`. |
| `outputs` | \[\][OutputSpec](#4-output-types) | Yes | - | Log output destinations. |
| `filters` | \[\][FilterSpec](#5-filter-types) | No | - | Reusable filter definitions referenced by pipelines. |
| `pipelines` | \[\][PipelineSpec](#pipelinespec) | Yes | - | Pipeline definitions that route inputs through filters to outputs. |

### ServiceAccount

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `name` | `string` | Yes | Pattern: `^[a-z][a-z0-9-]{2,62}[a-z0-9]$` | Name of the ServiceAccount in the same namespace as the ClusterLogForwarder. |

### PipelineSpec

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `name` | `string` | Yes | Pattern: `^[a-z][a-z0-9-]*[a-z0-9]$` | Unique pipeline name. |
| `inputRefs` | `[]string` | Yes | MinItems: 1 | References to inputs. Built-in values: `application`, `infrastructure`, `audit`. Can also reference custom input names. |
| `outputRefs` | `[]string` | Yes | MinItems: 1 | References to output names defined in `spec.outputs`. |
| `filterRefs` | `[]string` | No | - | References to filter names defined in `spec.filters`. Filters are applied in the order listed. |

---

## 2. CollectorSpec

Configuration for the collector (Vector) pods deployed by the operator.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resources` | `corev1.ResourceRequirements` | No | CPU and memory requests/limits for collector pods. |
| `nodeSelector` | `map[string]string` | No | Node labels used to schedule collector pods onto specific nodes. |
| `tolerations` | `[]corev1.Toleration` | No | Tolerations applied to collector pods for scheduling on tainted nodes. |
| `affinity` | `corev1.Affinity` | No | Affinity and anti-affinity rules for collector pod scheduling. |
| `networkPolicy` | [NetworkPolicy](#networkpolicy) | No | Network policy configuration for collector pods. |
| `maxUnavailable` | `IntOrString` | No | Maximum number or percentage of collector pods that can be unavailable during a rolling update. Pattern: `^(?:[0-9]{1,2}|100)%?$`. Examples: `1`, `"50%"`. |

### NetworkPolicy

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `ruleSet` | `string` | Yes | Enum: `AllowAllIngressEgress`, `RestrictIngressEgress` | Controls the network policy rule set applied to collector pods. |

---

## 3. Input Types

Inputs define the sources of log data. Three built-in inputs (`application`, `infrastructure`, `audit`) are always available and do not need to be declared. Custom inputs are defined in `spec.inputs` to apply filtering, tuning, or to configure receiver endpoints.

### InputSpec

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `name` | `string` | Yes | Pattern: `^[a-z][a-z0-9-]*[a-z0-9]$` | Unique input name. |
| `type` | `string` | Yes | Enum: `application`, `infrastructure`, `audit`, `receiver` | The type of log input. The corresponding type-specific field must also be set. |
| `application` | [Application](#application-input) | No | Required when `type: application` | Application log input configuration. |
| `infrastructure` | [Infrastructure](#infrastructure-input) | No | Required when `type: infrastructure` | Infrastructure log input configuration. |
| `audit` | [Audit](#audit-input) | No | Required when `type: audit` | Audit log input configuration. |
| `receiver` | [ReceiverSpec](#receiver-input) | No | Required when `type: receiver` | External log receiver configuration. |

### Application Input

Configures collection of application container logs with optional namespace/container filtering, label selection, and rate limiting.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `selector` | `metav1.LabelSelector` | No | Kubernetes label selector to match pods whose logs should be collected. |
| `includes` | \[\][NamespaceContainerSpec](#namespacecontainerspec) | No | Namespace and container patterns to include. |
| `excludes` | \[\][NamespaceContainerSpec](#namespacecontainerspec) | No | Namespace and container patterns to exclude. Excludes take precedence over includes. |
| `tuning` | [ContainerInputTuningSpec](#containerinputtuningspec) | No | Tuning parameters for application log collection. |

### Infrastructure Input

Configures collection of infrastructure logs from node journals and infrastructure container logs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sources` | `[]string` | No | Infrastructure log sources. Enum values: `node` (journald system logs), `container` (infrastructure namespace pods). |
| `tuning` | [InfrastructureInputTuningSpec](#infrastructureinputtuningspec) | No | Tuning parameters for infrastructure log collection. |

### Audit Input

Configures collection of audit logs from various cluster audit subsystems.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sources` | `[]string` | No | Audit log sources. Enum values: `kubeAPI`, `openshiftAPI`, `auditd`, `ovn`. |
| `tuning` | [AuditInputTuningSpec](#auditinputtuningspec) | No | Tuning parameters for audit log collection. |

### Receiver Input

Configures an HTTP or syslog receiver endpoint that accepts logs from external sources.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `type` | `string` | Yes | Enum: `http`, `syslog` | The receiver protocol type. |
| `port` | `int32` | Yes | Minimum: 1024, Maximum: 65535 | Port on which the receiver listens. |
| `tls` | [InputTLSSpec](#inputtlsspec) | No | - | TLS configuration for the receiver. If omitted, certificates are auto-generated. |
| `http` | [HTTPReceiver](#httpreceiver) | No | Required when `type: http` | HTTP receiver-specific configuration. |

### HTTPReceiver

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `format` | `string` | Yes | Enum: `kubeAPIAudit` | Expected format of incoming HTTP log payloads. |

### NamespaceContainerSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `namespace` | `string` | No | Namespace name or glob pattern (e.g., `openshift-*`). |
| `container` | `string` | No | Container name or glob pattern. |

### ContainerInputTuningSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rateLimitPerContainer` | [LimitSpec](#limitspec) | No | Rate limit applied per container. |
| `maxMessageSize` | `Quantity` | No | Maximum message size in bytes. Messages exceeding this size are dropped. |

### InfrastructureInputTuningSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `container` | [ContainerInputTuningSpec](#containerinputtuningspec) | No | Tuning for infrastructure container log collection. |

### AuditInputTuningSpec

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `ignoreOlder` | `Duration` | No | Minimum: `1s`. Default: `3600s` | Ignore audit log entries older than this duration. |

### LimitSpec

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `maxRecordsPerSecond` | `int64` | Yes | Minimum: 1 (exclusive of 0) | Maximum number of log records per second. |

---

## 4. Output Types

Outputs define where logs are forwarded. Each output has a `type` field that determines which type-specific configuration block must be provided.

### OutputSpec (Common Fields)

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `name` | `string` | Yes | Pattern: `^[a-z][a-z0-9-]*[a-z0-9]$` | Unique output name. |
| `type` | `string` | Yes | Enum: see [Output Type Enum](#output-type-enum) | The output destination type. |
| `tls` | [OutputTLSSpec](#7-tls-configuration) | No | - | TLS settings for the output connection. |
| `rateLimit` | [LimitSpec](#limitspec) | No | - | Per-output rate limit. |

Plus exactly one of the type-specific configuration fields listed below.

### Output Type Enum

| Value | Description |
|-------|-------------|
| `lokiStack` | Red Hat managed LokiStack |
| `loki` | Standalone Loki |
| `elasticsearch` | Elasticsearch |
| `splunk` | Splunk HEC |
| `cloudwatch` | Amazon CloudWatch |
| `googleCloudLogging` | Google Cloud Logging |
| `azureLogsIngestion` | Azure Monitor Logs Ingestion API |
| `azureMonitor` | Azure Monitor Data Collector API (DEPRECATED) |
| `kafka` | Apache Kafka |
| `http` | Generic HTTP/HTTPS endpoint |
| `syslog` | Syslog (RFC 3164 / RFC 5424) |
| `s3` | Amazon S3 or S3-compatible storage |
| `otlp` | OpenTelemetry Protocol (OTLP) |

---

### 4.1 LokiStack

Red Hat managed LokiStack output. Requires a LokiStack instance deployed via the Loki Operator.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `authentication` | [LokiStackAuthentication](#lokistackauthentication) | Yes | - | Authentication configuration. |
| `target` | [LokiStackTarget](#lokistacktarget) | Yes | - | Target LokiStack instance reference. |
| `labelKeys` | [LokiStackLabelKeys](#lokistacklabelkeys) | No | Cannot be set when `dataModel: Otel` | Label keys for Loki stream labels. |
| `dataModel` | `string` | No | Enum: `Viaq`, `Otel`. Default: `Viaq` | Data model used for log records. |
| `tuning` | [LokiTuningSpec](#lokituningspec) | No | `snappy` compression not allowed when `dataModel: Otel` | Tuning parameters. |

#### LokiStackAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | [BearerToken](#bearertoken) | Yes | Bearer token authentication. Typically `from: serviceAccount`. |

#### LokiStackTarget

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `namespace` | `string` | Yes | MinLength: 3 | Namespace of the LokiStack instance. |
| `name` | `string` | Yes | Pattern: `^[a-z][a-z0-9-]{2,62}[a-z0-9]$` | Name of the LokiStack instance. |

#### LokiStackLabelKeys

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `global` | `[]string` | No | Label keys applied to all tenants. |
| `application` | [LokiStackTenantLabelKeys](#lokistacktenantlabelkeys) | No | Label keys for the application tenant. |
| `infrastructure` | [LokiStackTenantLabelKeys](#lokistacktenantlabelkeys) | No | Label keys for the infrastructure tenant. |
| `audit` | [LokiStackTenantLabelKeys](#lokistacktenantlabelkeys) | No | Label keys for the audit tenant. |

#### LokiStackTenantLabelKeys

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ignoreGlobal` | `bool` | No | If true, global label keys are not applied to this tenant. |
| `labelKeys` | `[]string` | No | Tenant-specific label keys. |

#### LokiTuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec), plus:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `compression` | `string` | No | Enum: `none`, `gzip`, `snappy` | Compression algorithm. |

---

### 4.2 Loki (Standalone)

Standalone Loki instance output.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | Yes | Must be a valid URL | Loki push API endpoint URL. |
| `authentication` | [HTTPAuthentication](#httpauthentication) | No | - | Authentication credentials. |
| `labelKeys` | `[]string` | No | Defaults: `log_type`, `kubernetes.container_name`, `kubernetes.namespace_name`, `kubernetes.pod_name` | Log fields used as Loki stream labels. |
| `tenantKey` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax) | Template for the `X-Scope-OrgID` header (multi-tenant Loki). |
| `proxyURL` | `string` | No | Must be a valid URL if set | HTTP proxy URL. |
| `tuning` | [LokiTuningSpec](#lokituningspec) | No | - | Tuning parameters. |

---

### 4.3 Elasticsearch

Elasticsearch output (versions 6, 7, or 8).

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | Yes | Must be a valid URL | Elasticsearch endpoint URL. |
| `authentication` | [HTTPAuthentication](#httpauthentication) | No | - | Authentication credentials. |
| `index` | `string` | Yes | [Dynamic template syntax](#9-dynamic-template-syntax) | Index name template for log storage. |
| `version` | `int` | Yes | Minimum: 6, Maximum: 8 | Elasticsearch major version. |
| `headers` | `map[string]string` | No | - | Additional HTTP headers sent with each request. |
| `tuning` | [ElasticsearchTuningSpec](#elasticsearchtuningspec) | No | - | Tuning parameters. |

#### ElasticsearchTuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec), plus:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `compression` | `string` | No | Enum: `none`, `gzip`, `zlib` | Compression algorithm. |

---

### 4.4 Splunk

Splunk HTTP Event Collector (HEC) output.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | Yes | Must be a valid URL | Splunk HEC endpoint URL. |
| `authentication` | [SplunkAuthentication](#splunkauthentication) | Yes | - | HEC token authentication. |
| `index` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax) | Splunk index name. |
| `source` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax) | Splunk source field. |
| `sourceType` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax). Only valid when `payloadKey` is set. | Splunk sourcetype field. |
| `payloadKey` | `FieldPath` | No | [FieldPath pattern](#fieldpath) | Field path to use as the event payload instead of the full log record. |
| `indexedFields` | `[]FieldPath` | No | - | Fields to add as indexed fields in Splunk. |
| `tuning` | [SplunkTuningSpec](#splunktuningspec) | No | - | Tuning parameters. |

#### SplunkAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | [SecretReference](#secretreference) | Yes | Reference to the Splunk HEC token stored in a Secret. |

#### SplunkTuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec), plus:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `compression` | `string` | No | Enum: `none`, `gzip` | Compression algorithm. |

---

### 4.5 CloudWatch

Amazon CloudWatch Logs output.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | No | Must be a valid URL if set | Custom CloudWatch endpoint URL (for non-standard regions or VPC endpoints). |
| `authentication` | [AwsAuthentication](#awsauthentication) | Yes | - | AWS authentication configuration. |
| `region` | `string` | Yes | - | AWS region (e.g., `us-east-1`). |
| `groupName` | `string` | Yes | [Dynamic template syntax](#9-dynamic-template-syntax) | CloudWatch log group name template. |
| `tuning` | [CloudwatchTuningSpec](#cloudwatchtuningspec) | No | - | Tuning parameters. |

#### CloudwatchTuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec), plus:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `compression` | `string` | No | Enum: `gzip`, `none`, `snappy`, `zlib`, `zstd` | Compression algorithm. |

---

### 4.6 Google Cloud Logging

Google Cloud Logging output.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | [GoogleCloudLoggingId](#googlecloudloggingid) | Yes | Google Cloud resource identifier. |
| `logId` | `string` | Yes | Log ID template using [dynamic template syntax](#9-dynamic-template-syntax). |
| `authentication` | [GoogleCloudLoggingAuthentication](#googlecloudloggingauthentication) | No | Authentication credentials. |
| `tuning` | [GoogleCloudLoggingTuningSpec](#googlecloudloggingtuningspec) | No | Tuning parameters. |

#### GoogleCloudLoggingId

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `type` | `string` | Yes | Enum: `billingAccount`, `folder`, `project`, `organization` | The Google Cloud resource type. |
| `value` | `string` | Yes | - | The resource identifier value. |

#### GoogleCloudLoggingAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credentials` | [SecretReference](#secretreference) | Yes | Reference to a Secret containing Google Cloud service account JSON credentials. |
| `token` | [BearerToken](#bearertoken) | No | Bearer token for Workload Identity Federation (WIF). |

#### GoogleCloudLoggingTuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec). No additional fields.

---

### 4.7 Azure Logs Ingestion

Azure Monitor Logs Ingestion API output (Data Collection Rules).

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | Yes | Must be a valid URL | Data Collection Endpoint (DCE) URL. |
| `authentication` | [AzureLogsIngestionAuthentication](#azurelogsIngestionauthentication) | Yes | - | Azure authentication configuration. |
| `dcrImmutableId` | `string` | Yes | - | Immutable ID of the Data Collection Rule (DCR). |
| `streamName` | `string` | Yes | - | Name of the stream in the DCR. |
| `tokenScope` | `string` | No | Default: `https://monitor.azure.com/.default` | OAuth token scope. |
| `timestampField` | `string` | No | Default: `TimeGenerated` | Timestamp field name in the destination table. Values: `TimeGenerated`, `Timestamp`, `EventStartTime`. |
| `tuning` | [AzureLogsIngestionTuningSpec](#azurelogsingestiontuningspec) | No | - | Tuning parameters. |

#### AzureLogsIngestionAuthentication

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `type` | `string` | Yes | Enum: `clientSecret`, `workloadIdentity` | Authentication method type. |
| `clientSecret` | [AzureLogsIngestionClientSecret](#azurelogsingestionclientsecret) | No | Required when `type: clientSecret` | Client secret authentication details. |
| `workloadIdentity` | [AzureLogsIngestionWorkloadIdentity](#azurelogsingestionworkloadidentity) | No | Required when `type: workloadIdentity` | Workload identity authentication details. |

#### AzureLogsIngestionClientSecret

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenantId` | `string` | Yes | Azure AD tenant ID. |
| `clientId` | `string` | Yes | Azure AD application (client) ID. |
| `secret` | [SecretReference](#secretreference) | Yes | Reference to the client secret stored in a Kubernetes Secret. |

#### AzureLogsIngestionWorkloadIdentity

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenantId` | `string` | Yes | Azure AD tenant ID. |
| `clientId` | `string` | Yes | Azure AD application (client) ID. |
| `token` | [BearerToken](#bearertoken) | Yes | Bearer token for workload identity federation. |

#### AzureLogsIngestionTuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec). No additional fields.

---

### 4.8 Azure Monitor (DEPRECATED)

> **DEPRECATED:** Use [Azure Logs Ingestion](#47-azure-logs-ingestion) instead. This output type will be removed in a future release.

Azure Monitor Data Collector API output.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `authentication` | [AzureMonitorAuthentication](#azuremonitorauthentication) | Yes | - | Shared key authentication. |
| `customerId` | `string` | Yes | - | Log Analytics workspace ID. |
| `logType` | `string` | Yes | MinLength: 1, Pattern: `^[a-zA-Z0-9][a-zA-Z0-9_]{0,99}$` | Custom log table name. |
| `azureResourceId` | `string` | No | - | Azure resource ID to associate with log data. |
| `host` | `string` | No | - | Alternative host for the Data Collector API. |
| `tuning` | [BaseOutputTuningSpec](#baseoutputtuningspec) | No | - | Tuning parameters. |

#### AzureMonitorAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sharedKey` | [SecretReference](#secretreference) | Yes | Reference to the Azure Monitor shared key stored in a Secret. |

---

### 4.9 Kafka

Apache Kafka output.

Validation: At least one of `url` or `brokers` must be provided.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | No | Pattern: `^(tcp\|tls)://...` | Kafka broker URL. Mutually optional with `brokers`. |
| `brokers` | `[]string` | No | Each entry pattern: `^(tcp\|tls)://...` | List of initial Kafka broker endpoints. |
| `topic` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax). Default: `topic` | Kafka topic name template. |
| `authentication` | [KafkaAuthentication](#kafkaauthentication) | No | - | SASL authentication configuration. |
| `tuning` | [KafkaTuningSpec](#kafkatuningspec) | No | - | Tuning parameters. |

#### KafkaAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sasl` | [SASLAuthentication](#saslauthentication) | No | SASL authentication settings. |

#### SASLAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | [SecretReference](#secretreference) | No | Reference to the SASL username stored in a Secret. |
| `password` | [SecretReference](#secretreference) | No | Reference to the SASL password stored in a Secret. |
| `mechanism` | `string` | No | SASL mechanism (e.g., `PLAIN`, `SCRAM-SHA-256`, `SCRAM-SHA-512`). |

#### KafkaTuningSpec

Note: KafkaTuningSpec does not inherit from BaseOutputTuningSpec. It has its own subset of tuning fields.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `deliveryMode` | `string` | No | Enum: `AtLeastOnce`, `AtMostOnce` | Delivery guarantee mode. |
| `maxWrite` | `Quantity` | No | - | Maximum payload size per send. |
| `compression` | `string` | No | Enum: `none`, `snappy`, `zstd`, `lz4` | Compression algorithm. |

---

### 4.10 HTTP

Generic HTTP/HTTPS output for sending logs to any HTTP endpoint.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | Yes | Must be a valid URL | Destination endpoint URL. |
| `authentication` | [HTTPAuthentication](#httpauthentication) | No | - | Authentication credentials. |
| `headers` | `map[string]string` | No | - | Additional HTTP headers sent with each request. |
| `timeout` | `int` | No | Default: 10 (seconds) | Request timeout in seconds. |
| `method` | `string` | No | Enum: `GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `OPTIONS`, `TRACE`, `PATCH`. Default: `POST` | HTTP method. |
| `proxyURL` | `string` | No | Must be a valid URL if set | HTTP proxy URL. |
| `format` | `string` | No | Enum: `json`, `ndjson` | Payload format. |
| `tuning` | [HTTPTuningSpec](#httptuningspec) | No | - | Tuning parameters. |

#### HTTPTuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec), plus:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `compression` | `string` | No | Enum: `none`, `gzip`, `snappy`, `zlib` | Compression algorithm. |

---

### 4.11 Syslog

Syslog output supporting RFC 3164 and RFC 5424 formats.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | Yes | Pattern: `^(tcp\|tls\|udp)://...` (must include port) | Syslog server URL with protocol scheme and port. |
| `rfc` | `string` | Yes | Enum: `RFC3164`, `RFC5424` | Syslog RFC format. |
| `severity` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax) | Syslog severity template. |
| `facility` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax) | Syslog facility template. |
| `appName` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax). Truncated to 48 chars. | RFC 5424 APP-NAME field. |
| `procId` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax). Truncated to 128 chars. | RFC 5424 PROCID field. |
| `msgId` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax). Truncated to 32 chars. | RFC 5424 MSGID field. |
| `payloadKey` | `FieldPath` | No | [FieldPath pattern](#fieldpath) | Field path used as the syslog message body instead of the full log record. |
| `enrichment` | `string` | No | Enum: `None`, `KubernetesMinimal`. Default: `None` | Whether to enrich syslog messages with Kubernetes metadata. |
| `tuning` | [SyslogTuningSpec](#syslogtuningspec) | No | - | Tuning parameters. |

#### SyslogTuningSpec

Note: SyslogTuningSpec does not inherit from BaseOutputTuningSpec. It only supports delivery mode.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `deliveryMode` | `string` | No | Enum: `AtLeastOnce`, `AtMostOnce` | Delivery guarantee mode. |

---

### 4.12 S3

Amazon S3 or S3-compatible (MinIO, Ceph, etc.) storage output.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `authentication` | [AwsAuthentication](#awsauthentication) | Yes | - | AWS authentication configuration. |
| `region` | `string` | Yes | - | AWS region or S3-compatible region identifier. |
| `bucket` | `string` | Yes | Pattern: `^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$` | S3 bucket name. |
| `keyPrefix` | `string` | No | [Dynamic template syntax](#9-dynamic-template-syntax) | Object key prefix template. |
| `url` | `string` | No | - | Custom S3-compatible endpoint URL (for MinIO, Ceph, etc.). |
| `tuning` | [S3TuningSpec](#s3tuningspec) | No | - | Tuning parameters. |

#### S3TuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec), plus:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `compression` | `string` | No | Enum: `gzip`, `none`, `snappy`, `zlib`, `zstd` | Compression algorithm. |

---

### 4.13 OTLP

OpenTelemetry Protocol (OTLP) output for sending logs to OTLP-compatible collectors or backends.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `url` | `string` | Yes | Pattern: `^(https?):\/\/\S+$`, must be a valid URL | OTLP endpoint URL. Should typically end with `/v1/logs`. |
| `authentication` | [HTTPAuthentication](#httpauthentication) | No | - | Authentication credentials. |
| `tuning` | [OTLPTuningSpec](#otlptuningspec) | No | - | Tuning parameters. |

#### OTLPTuningSpec

Inherits all fields from [BaseOutputTuningSpec](#baseoutputtuningspec), plus:

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `compression` | `string` | No | Enum: `gzip`, `snappy`, `zlib`, `zstd`, `none` | Compression algorithm. |

---

## 5. Filter Types

Filters process log records in a pipeline. They are defined in `spec.filters` and referenced by name in `spec.pipelines[].filterRefs`. Filters are applied in the order they appear in `filterRefs`.

### FilterSpec

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `name` | `string` | Yes | Pattern: `^[a-z][a-z0-9-]*[a-z0-9]$` | Unique filter name. |
| `type` | `string` | Yes | Enum: `detectMultilineException`, `drop`, `kubeAPIAudit`, `openshiftLabels`, `parse`, `prune` | The filter type. The corresponding type-specific field must be set for types that require configuration. |
| `drop` | \[\][DropTest](#droptest) | No | Required when `type: drop` | Drop filter test conditions. |
| `prune` | [PruneFilterSpec](#prunefilterspec) | No | Required when `type: prune` | Prune filter configuration. |
| `kubeAPIAudit` | [KubeAPIAudit](#kubeapiaudit) | No | Required when `type: kubeAPIAudit` | Kubernetes API audit policy configuration. |
| `openshiftLabels` | `map[string]string` | No | Required when `type: openshiftLabels` | Key-value pairs added to `openshift.labels` on log records. |

### 5.1 detectMultilineException

Automatically merges multi-line exception stack traces into a single log entry. No additional configuration fields required.

### 5.2 parse

Enables structured log parsing. The collector attempts to parse log messages as JSON or other structured formats. No additional configuration fields required.

### 5.3 drop

Drops log records that match specified conditions.

#### DropTest

Each `DropTest` contains an array of `DropCondition` entries that are logically ANDed together. If all conditions in a test match, the log record is dropped. Multiple `DropTest` entries are logically ORed -- a record is dropped if any single test matches entirely.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `test` | \[\][DropCondition](#dropcondition) | Yes | MinItems: 1 | Array of conditions (ANDed). |

#### DropCondition

Exactly one of `matches` or `notMatches` must be provided per condition.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `field` | `FieldPath` | No | [FieldPath pattern](#fieldpath) | Log record field to evaluate. |
| `matches` | `string` | No | Regular expression | Drop the record if the field value matches this regex. |
| `notMatches` | `string` | No | Regular expression | Drop the record if the field value does NOT match this regex. |

### 5.4 prune

Removes or retains specific fields from log records. Exactly one of `in` or `notIn` should be used.

#### PruneFilterSpec

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `in` | `[]FieldPath` | No | Cannot contain `.log_type`, `.log_source`, `.message` | List of fields to remove from log records. |
| `notIn` | `[]FieldPath` | No | Must contain `.log_type`, `.log_source`, `.message` | List of fields to keep. All other fields are removed. |

### 5.5 kubeAPIAudit

Filters Kubernetes API server audit logs using audit policy rules. Supports wildcard extensions beyond the standard Kubernetes audit policy format.

#### KubeAPIAudit

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `rules` | `[]audit.PolicyRule` | No | Empty list means default rules apply | Audit policy rules in standard Kubernetes audit policy format. |
| `omitStages` | `[]audit.Stage` | No | - | Audit stages to exclude from logging. |
| `omitResponseCodes` | `[]int` | No | Default: `[404, 409, 422, 429]`. Set to empty list to disable. | HTTP response codes to omit from audit logs. |

### 5.6 openshiftLabels

Adds key-value labels to the `openshift.labels` field on log records. The filter value is a `map[string]string` defined directly on the `openshiftLabels` field of `FilterSpec`.

---

## 6. Authentication Types

### BearerToken

Used for token-based authentication with outputs. Supports tokens from a Kubernetes Secret or from the collector's ServiceAccount.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `from` | `string` | Yes | Enum: `secret`, `serviceAccount` | Source of the bearer token. |
| `secret` | [BearerTokenSecretKey](#bearertokensecretkey) | No | Required when `from: secret` | Secret reference for the token. |

#### BearerTokenSecretKey

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Name of the Kubernetes Secret. |
| `key` | `string` | Yes | Key within the Secret data. |

### HTTPAuthentication

Common authentication block used by Loki, Elasticsearch, HTTP, and OTLP outputs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | [BearerToken](#bearertoken) | No | Bearer token authentication. |
| `username` | [SecretReference](#secretreference) | No | Reference to a Secret containing the username. |
| `password` | [SecretReference](#secretreference) | No | Reference to a Secret containing the password. |

### AwsAuthentication

AWS authentication used by CloudWatch and S3 outputs.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `type` | `string` | Yes | Enum: `awsAccessKey`, `iamRole` | AWS authentication method. |
| `awsAccessKey` | [AwsAccessKey](#awsaccesskey) | No | Required when `type: awsAccessKey` | Static AWS access key credentials. |
| `iamRole` | [AwsRole](#awsrole) | No | Required when `type: iamRole` | IAM role-based authentication (STS/IRSA). |
| `assumeRole` | [AwsAssumeRole](#awsassumerole) | No | - | Optional cross-account role assumption. |

#### AwsAccessKey

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keyId` | [SecretReference](#secretreference) | Yes | Reference to a Secret containing the AWS access key ID. |
| `keySecret` | [SecretReference](#secretreference) | Yes | Reference to a Secret containing the AWS secret access key. |

#### AwsRole

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `roleARN` | [SecretReference](#secretreference) | Yes | Reference to a Secret containing the IAM role ARN. |
| `token` | [BearerToken](#bearertoken) | Yes | Bearer token for STS authentication. |

#### AwsAssumeRole

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `roleARN` | [SecretReference](#secretreference) | Yes | - | Reference to a Secret containing the role ARN to assume. |
| `externalID` | `string` | No | MinLength: 2, MaxLength: 1224, Pattern: `^[\w+=,.@:/-]*$` | External ID for cross-account access. |
| `sessionName` | `string` | No | Pattern: `^[a-zA-Z0-9_+=,.@-]{2,64}$` | Session name for the assumed role session. |

### SplunkAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | [SecretReference](#secretreference) | Yes | Reference to a Secret containing the Splunk HEC token. |

### KafkaAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sasl` | [SASLAuthentication](#saslauthentication) | No | SASL authentication settings. |

### AzureLogsIngestionAuthentication

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `type` | `string` | Yes | Enum: `clientSecret`, `workloadIdentity` | Authentication method type. |
| `clientSecret` | [AzureLogsIngestionClientSecret](#azurelogsingestionclientsecret) | No | Required when `type: clientSecret` | Client secret credentials. |
| `workloadIdentity` | [AzureLogsIngestionWorkloadIdentity](#azurelogsingestionworkloadidentity) | No | Required when `type: workloadIdentity` | Workload identity federation credentials. |

### GoogleCloudLoggingAuthentication

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `credentials` | [SecretReference](#secretreference) | Yes | Reference to a Secret containing Google Cloud service account JSON key. |
| `token` | [BearerToken](#bearertoken) | No | Bearer token for Workload Identity Federation (WIF). |

---

## 7. TLS Configuration

### OutputTLSSpec

TLS configuration for output connections. Inherits fields from the base TLSSpec and adds output-specific options.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `ca` | [ValueReference](#valuereference) | No | - | Reference to a CA certificate bundle for server verification. |
| `certificate` | [ValueReference](#valuereference) | No | - | Reference to a client certificate for mutual TLS. |
| `key` | [SecretReference](#secretreference) | No | - | Reference to the client private key for mutual TLS. |
| `keyPassphrase` | [SecretReference](#secretreference) | No | - | Reference to the passphrase for an encrypted client key. |
| `insecureSkipVerify` | `bool` | No | `false` | If true, skip server certificate verification. Not recommended for production. |
| `securityProfile` | `TLSSecurityProfile` | No | - | OpenShift TLS security profile. Values: `Old`, `Intermediate`, `Modern`, `Custom`. |

### InputTLSSpec

TLS configuration for receiver inputs. Uses the base TLSSpec fields. If not defined on a receiver input, certificates are auto-generated.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ca` | [ValueReference](#valuereference) | No | Reference to a CA certificate bundle. |
| `certificate` | [ValueReference](#valuereference) | No | Reference to a server certificate. |
| `key` | [SecretReference](#secretreference) | No | Reference to the server private key. |
| `keyPassphrase` | [SecretReference](#secretreference) | No | Reference to the passphrase for an encrypted server key. |

### ValueReference

A reference to a value stored in either a ConfigMap or a Secret. Exactly one of `configMapName` or `secretName` must be set.

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| `key` | `string` | Yes | - | The key within the ConfigMap or Secret. |
| `configMapName` | `string` | No | Mutually exclusive with `secretName` | Name of the ConfigMap containing the value. |
| `secretName` | `string` | No | Mutually exclusive with `configMapName` | Name of the Secret containing the value. |

### SecretReference

A reference to a key within a Kubernetes Secret.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | `string` | Yes | The key within the Secret data. |
| `secretName` | `string` | Yes | Name of the Kubernetes Secret. |

---

## 8. Tuning Options

### BaseOutputTuningSpec

Common tuning fields inherited by most output-specific tuning specs (exceptions noted per output type).

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `deliveryMode` | `string` | No | In-memory buffer (no durable guarantee) | Delivery guarantee mode. `AtLeastOnce`: durable disk buffer, retries on failure. `AtMostOnce`: best-effort, may lose records on failure. |
| `maxWrite` | `Quantity` | No | - | Maximum payload size per write operation (e.g., `10Mi`). |
| `minRetryDuration` | `Duration` | No | - | Minimum wait duration between retry attempts (e.g., `1s`). |
| `maxRetryDuration` | `Duration` | No | - | Maximum wait duration between retry attempts (e.g., `300s`). |

### Per-Output Compression Options

| Output Type | Tuning Base | Compression Values |
|-------------|------------|-------------------|
| `lokiStack` | BaseOutputTuningSpec | `none`, `gzip`, `snappy` |
| `loki` | BaseOutputTuningSpec | `none`, `gzip`, `snappy` |
| `elasticsearch` | BaseOutputTuningSpec | `none`, `gzip`, `zlib` |
| `splunk` | BaseOutputTuningSpec | `none`, `gzip` |
| `cloudwatch` | BaseOutputTuningSpec | `gzip`, `none`, `snappy`, `zlib`, `zstd` |
| `googleCloudLogging` | BaseOutputTuningSpec | (no compression field) |
| `azureLogsIngestion` | BaseOutputTuningSpec | (no compression field) |
| `azureMonitor` | BaseOutputTuningSpec | (no compression field) |
| `kafka` | Custom (deliveryMode + maxWrite only) | `none`, `snappy`, `zstd`, `lz4` |
| `http` | BaseOutputTuningSpec | `none`, `gzip`, `snappy`, `zlib` |
| `syslog` | Custom (deliveryMode only) | (no compression field) |
| `s3` | BaseOutputTuningSpec | `gzip`, `none`, `snappy`, `zlib`, `zstd` |
| `otlp` | BaseOutputTuningSpec | `gzip`, `snappy`, `zlib`, `zstd`, `none` |

---

## 9. Dynamic Template Syntax

Several output fields support dynamic template syntax, which allows log record fields to be interpolated into string values at runtime.

### Format

```
{.fieldPath||fallback}
```

- `.fieldPath` references a field in the log record using dot notation.
- `||` separates alternatives. The first non-empty value is used.
- Quoted strings (e.g., `"default"`) provide literal fallback values.
- Multiple fallbacks can be chained.

### Examples

| Template | Behavior |
|----------|----------|
| `foo-{.bar\|\|"none"}` | Uses the value of `.bar`, falls back to the literal string `none`. |
| `{.foo\|\|.bar\|\|"missing"}` | Uses `.foo` if present, then `.bar`, then the literal `missing`. |
| `app-{.kubernetes.namespace_name}` | Interpolates the namespace name. |
| `{.log_type}` | Uses the log type value directly. |

### Fields That Support Dynamic Templates

| Output Type | Fields |
|-------------|--------|
| `elasticsearch` | `index` |
| `loki` | `tenantKey` |
| `cloudwatch` | `groupName` |
| `googleCloudLogging` | `logId` |
| `kafka` | `topic` |
| `splunk` | `index`, `source`, `sourceType` |
| `syslog` | `severity`, `facility`, `appName`, `procId`, `msgId` |
| `s3` | `keyPrefix` |

---

## FieldPath

A dot-notation path referencing a field in a log record.

Pattern: `^(\.[a-zA-Z0-9_]+|\.\"[^\"]+\")(\.[a-zA-Z0-9_]+|\.\"[^\"]+\")*$`

Examples:
- `.message`
- `.kubernetes.namespace_name`
- `.kubernetes.labels."app.kubernetes.io/name"`
