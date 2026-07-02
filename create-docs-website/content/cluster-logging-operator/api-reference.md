# API Reference

This document provides the complete API reference for the Custom Resource Definitions (CRDs) managed by the Cluster Logging Operator.

---

## ClusterLogForwarder (observability.openshift.io/v1)

- **Short names:** `obsclf`, `clf`
- **Scope:** Namespaced
- **Categories:** observability
- **Name validation:** Must match `^[a-z][a-z0-9-]{1,61}[a-z0-9]$` (valid DNS1035 label)

The ClusterLogForwarder configures log collection and forwarding. You define inputs (log sources), outputs (destinations), optional filters (transformations), and pipelines that route logs from inputs through filters to outputs.

---

### Spec Fields

#### Top-Level Spec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `managementState` | string | No | `Managed` | Controls whether the operator actively reconciles this resource. Valid values: `Managed`, `Unmanaged`. |
| `serviceAccount` | [ServiceAccount](#serviceaccount) | Yes | - | Service account used by collector pods. |
| `inputs` | [][InputSpec](#inputspec) | No | - | Custom input definitions. Built-in inputs (`application`, `infrastructure`, `audit`) are available without explicit definition. |
| `outputs` | [][OutputSpec](#outputspec) | Yes | - | Output destinations for log messages. |
| `filters` | [][FilterSpec](#filterspec) | No | - | Log transformation filters applied within pipelines. |
| `pipelines` | [][PipelineSpec](#pipelinespec) | Yes | - | Routes logs from inputs through filters to outputs. |
| `collector` | [CollectorSpec](#collectorspec) | No | - | Collector deployment configuration (resources, placement, network policy). |

#### ServiceAccount

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name of the ServiceAccount to deploy the forwarder. Must match pattern `^[a-z][a-z0-9-]{2,62}[a-z0-9]$`. The ServiceAccount must be created by the administrator. |

---

#### CollectorSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `resources` | corev1.ResourceRequirements | No | - | Resource requirements (requests/limits) for collector containers. |
| `nodeSelector` | map[string]string | No | - | Node labels for scheduling collector pods to specific nodes. |
| `tolerations` | []corev1.Toleration | No | - | Tolerations that collector pods will accept. |
| `affinity` | corev1.Affinity | No | - | Scheduling rules based on node or pod affinity/anti-affinity constraints. |
| `networkPolicy` | [NetworkPolicy](#networkpolicy-collector) | No | - | Network policy for the collector. |
| `maxUnavailable` | IntOrString | No | - | Maximum unavailable pods during a rolling update. Defaults to 100% when not set. Value can be a number or a percentage string. Must match pattern `^(?:[0-9]{1,2}|100)%?$`. |

##### NetworkPolicy (Collector)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `ruleSet` | string | Yes | - | Type of network policy rule set. Valid values: `AllowAllIngressEgress`, `RestrictIngressEgress`. |

---

#### InputSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name used to refer to this input from a pipeline. Must match pattern `^[a-z][a-z0-9-]*[a-z0-9]$`. |
| `type` | string | Yes | - | Type of input. Valid values: `application`, `infrastructure`, `audit`, `receiver`. |
| `application` | [Application](#application-input) | Conditional | - | Application log input configuration. Required when `type` is `application`. |
| `infrastructure` | [Infrastructure](#infrastructure-input) | Conditional | - | Infrastructure log input configuration. Required when `type` is `infrastructure`. |
| `audit` | [Audit](#audit-input) | Conditional | - | Audit log input configuration. Required when `type` is `audit`. |
| `receiver` | [ReceiverSpec](#receiver-input) | Conditional | - | Receiver input configuration for non-cluster log sources. Required when `type` is `receiver`. |

---

##### Application Input

Selects application workload logs. All conditions in the selector are combined with logical AND.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `selector` | metav1.LabelSelector | No | - | Pod label selector. Only logs from pods with matching labels are collected. If absent or empty, logs are collected regardless of labels. |
| `includes` | [][NamespaceContainerSpec](#namespacecontainerspec) | No | - | Namespaces and containers to include when collecting logs. Infrastructure namespaces are still excluded for `*` values unless a qualifying glob pattern is specified. |
| `excludes` | [][NamespaceContainerSpec](#namespacecontainerspec) | No | - | Namespaces and containers to exclude when collecting logs. Takes precedence over `includes`. |
| `tuning` | [ContainerInputTuningSpec](#containerinputtuningspec) | No | - | Container input tuning parameters. |

###### NamespaceContainerSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `namespace` | string | No | `*` | Namespace glob pattern. Supports glob patterns and presumes `*` if omitted. |
| `container` | string | No | `*` | Container name glob pattern. Supports glob patterns and presumes `*` if omitted. |

###### ContainerInputTuningSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `rateLimitPerContainer` | [LimitSpec](#limitspec) | No | - | Per-container rate limit applied per collector deployment. Log records exceeding the rate limit are dropped. |
| `maxMessageSize` | Quantity | No | - | Maximum message length in bytes for a single log event when all partial log lines are merged. Messages exceeding this limit are dropped. |

---

##### Infrastructure Input

Collects infrastructure logs from container workloads in namespaces `default`, `kube*`, `openshift*`, and journald logs from cluster nodes.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `sources` | []string | No | all sources | Infrastructure log sources to collect. Valid values: `container`, `node`. Omitting collects all sources. |
| `tuning` | [InfrastructureInputTuningSpec](#infrastructureinputtuningspec) | No | - | Infrastructure input tuning, currently available only for container sources. |

###### InfrastructureInputTuningSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `container` | [ContainerInputTuningSpec](#containerinputtuningspec) | No | - | Input tuning for container sources. |

---

##### Audit Input

Collects system audit logs.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `sources` | []string | No | all sources | Audit log sources to collect. Valid values: `kubeAPI`, `openshiftAPI`, `auditd`, `ovn`. Omitting collects all sources. |
| `tuning` | [AuditInputTuningSpec](#auditinputtuningspec) | No | - | Audit input tuning. |

###### AuditInputTuningSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `ignoreOlder` | Duration | No | `3600s` (1 hour) | Maximum duration since the last modification of an audit log file before the collector ignores it. When the collector restarts, files not modified within this window may not be collected. Increase for audit sources with infrequent writes. Must be at least 1 second. |

---

##### Receiver Input

Configures a network receiver for receiving logs from non-cluster sources.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | string | Yes | - | Type of receiver. Valid values: `http`, `syslog`. HTTP currently only supports Kubernetes audit logs (`log_type = "audit"`). Syslog currently only supports node infrastructure logs (`log_type = "infrastructure"`). |
| `port` | int32 | Yes | - | Port the receiver listens on. Must be between 1024 and 65535 (inclusive). |
| `tls` | [InputTLSSpec](#inputtlsspec) | No | - | TLS settings for the receiver. When not defined, the operator requests certificates from the cluster's cert signing service. |
| `http` | [HTTPReceiver](#httpreceiver) | No | - | HTTP receiver-specific configuration. |

###### InputTLSSpec

Identical to [TLSSpec](#tlsspec) -- contains `ca`, `certificate`, `key`, and `keyPassphrase` fields.

###### HTTPReceiver

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `format` | string | Yes | - | Format of incoming log data. Valid values: `kubeAPIAudit`. |

---

#### OutputSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name used to refer to this output from a pipeline. Must match pattern `^[a-z][a-z0-9-]*[a-z0-9]$`. |
| `type` | string | Yes | - | Type of output destination. Valid values: `azureLogsIngestion`, `azureMonitor`, `cloudwatch`, `elasticsearch`, `googleCloudLogging`, `http`, `kafka`, `loki`, `lokiStack`, `otlp`, `s3`, `splunk`, `syslog`. |
| `tls` | [OutputTLSSpec](#outputtlsspec) | No | - | TLS settings for output connections. |
| `rateLimit` | [LimitSpec](#limitspec) | No | - | Rate limit in records-per-second on the total aggregate rate of logs forwarded to this output from any given collector container. Logs may be dropped to enforce the limit. |

---

##### OutputTLSSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `insecureSkipVerify` | bool | No | `false` | Skip validating server certificates. Not recommended for production. |
| `securityProfile` | TLSSecurityProfile | No | - | TLS security profile for the connection. Valid profile types: `Old`, `Intermediate`, `Modern`, `Custom`. |
| `ca` | [ValueReference](#valuereference) | No | - | Custom list of trusted certificate authorities. |
| `certificate` | [ValueReference](#valuereference) | No | - | Server certificate to use. |
| `key` | [SecretReference](#secretreference) | No | - | Private key of the server certificate. |
| `keyPassphrase` | [SecretReference](#secretreference) | No | - | Passphrase to unlock the private key. |

---

##### CloudWatch Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `authentication` | [AwsAuthentication](#awsauthentication) | Yes | - | AWS authentication credentials. |
| `region` | string | Yes | - | AWS region. |
| `groupName` | string | Yes | - | CloudWatch log group name. Supports template syntax for dynamic per-event values (see [Template Syntax](#template-syntax)). |
| `url` | string | No | - | URL to send log records to. Optional -- uses default AWS endpoint if not set. |
| `tuning` | [CloudwatchTuningSpec](#cloudwatchtuningspec) | No | - | Tuning options. Extends [BaseOutputTuningSpec](#baseoutputtuningspec) with `compression` (valid values: `gzip`, `none`, `snappy`, `zlib`, `zstd`). |

###### AwsAuthentication

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | string | Yes | - | Authentication type. Valid values: `awsAccessKey`, `iamRole`. |
| `awsAccessKey` | [AwsAccessKey](#awsaccesskey) | Conditional | - | AWS access key credentials. Required when `type` is `awsAccessKey`. |
| `iamRole` | [AwsRole](#awsrole) | Conditional | - | IAM role credentials for STS-enabled clusters. Required when `type` is `iamRole`. |
| `assumeRole` | [AwsAssumeRole](#awsassumerole) | No | - | Additional role to assume for cross-account log forwarding. |

###### AwsAccessKey

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `keyId` | [SecretReference](#secretreference) | Yes | - | Secret containing the AWS access key ID. |
| `keySecret` | [SecretReference](#secretreference) | Yes | - | Secret containing the AWS access key secret. |

###### AwsRole

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `roleARN` | [SecretReference](#secretreference) | Yes | - | Secret containing the role ARN. Requires an OIDC provider in an STS-enabled cluster. |
| `token` | [BearerToken](#bearertoken) | Yes | - | Bearer token for authentication. |

###### AwsAssumeRole

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `roleARN` | [SecretReference](#secretreference) | Yes | - | Secret containing the ARN of the role to assume. |
| `externalID` | string | No | - | External ID for additional security when assuming the role. Must be 2-1224 characters, alphanumeric with `+=,.@:/-`. |
| `sessionName` | string | No | - | Optional identifier for the assumed role session. Must match `^[a-zA-Z0-9_+=,.@-]{2,64}$`. |

---

##### Elasticsearch Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | URL to send log records to. Must be a valid URL. |
| `version` | int | Yes | - | Elasticsearch API version. Must be one of: `6`, `7`, `8`. Use `8` for Elasticsearch v8 or greater. |
| `index` | string | Yes | - | Index for logs. Supports template syntax for dynamic per-event values (see [Template Syntax](#template-syntax)). When forwarding to Red Hat Managed Elasticsearch, must match `^(app\|infra\|audit)-write$`. |
| `authentication` | [HTTPAuthentication](#httpauthentication) | No | - | Authentication credentials. |
| `headers` | map[string]string | No | - | Optional headers sent with requests. |
| `tuning` | [ElasticsearchTuningSpec](#elasticsearchtuningspec) | No | - | Tuning options. Extends [BaseOutputTuningSpec](#baseoutputtuningspec) with `compression` (valid values: `none`, `gzip`, `zlib`). |

---

##### Splunk Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | URL to send log records to (Splunk HEC endpoint). Must be a valid URL. |
| `authentication` | [SplunkAuthentication](#splunkauthentication) | Yes | - | Authentication credentials. |
| `index` | string | No | - | Splunk index for logs. Supports template syntax (see [Template Syntax](#template-syntax)). |
| `indexedFields` | [][FieldPath](#fieldpath) | No | - | Fields to be indexed by Splunk. Increases storage usage. Nested fields are flattened with dot notation. |
| `source` | string | No | auto-detected | Source identifier for the log event. Supports template syntax. If not specified, auto-detected from `.log_source` and `.log_type`. |
| `sourceType` | string | No | `_json` | Pretrained or custom source type. Can only be set when `payloadKey` is defined. Supports template syntax. |
| `payloadKey` | [FieldPath](#fieldpath) | No | - | Record field to use as payload. If not set, the complete log record is forwarded. |
| `tuning` | [SplunkTuningSpec](#splunktuningspec) | No | - | Tuning options. Extends [BaseOutputTuningSpec](#baseoutputtuningspec) with `compression` (valid values: `none`, `gzip`). |

###### SplunkAuthentication

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `token` | [SecretReference](#secretreference) | Yes | - | Secret containing the Splunk HEC token. |

---

##### Kafka Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | No | - | URL to send log records to. Must use `tcp` or `tls` scheme with a port number (e.g., `tls://kafka.example.com:9093/topic`). Either `url` or `brokers` must be provided. |
| `brokers` | []string | No | - | List of Kafka broker endpoints. Each must match `^(tcp\|tls)://...` pattern with a port. Used for initial connection only; the Kafka client fetches updated lists. Falls back to `url` if not provided. |
| `topic` | string | No | `topic` | Target Kafka topic. Supports template syntax (see [Template Syntax](#template-syntax)). |
| `authentication` | [KafkaAuthentication](#kafkaauthentication) | No | - | Authentication credentials. |
| `tuning` | [KafkaTuningSpec](#kafkatuningspec) | No | - | Tuning options with `deliveryMode`, `maxWrite`, and `compression` (valid values: `none`, `snappy`, `zstd`, `lz4`). |

###### KafkaAuthentication

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `sasl` | [SASLAuthentication](#saslauthentication) | No | - | SASL authentication options. |

###### SASLAuthentication

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `username` | [SecretReference](#secretreference) | No | - | Secret containing the SASL username. |
| `password` | [SecretReference](#secretreference) | No | - | Secret containing the SASL password. |
| `mechanism` | string | No | - | SASL mechanism to use. |

---

##### Loki Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | URL to send log records to. Must be a valid URL. |
| `authentication` | [HTTPAuthentication](#httpauthentication) | No | - | Authentication credentials. |
| `labelKeys` | []string | No | `log_type`, `kubernetes.container_name`, `kubernetes.namespace_name`, `kubernetes.pod_name` | Log record keys mapped to Loki stream labels. The label `kubernetes_host` is always present. |
| `tenantKey` | string | No | - | Tenant for the logs. Supports template syntax (see [Template Syntax](#template-syntax)). |
| `proxyURL` | string | No | - | URL of an HTTP or HTTPS proxy. Must be a valid URL if specified. |
| `tuning` | [LokiTuningSpec](#lokituningspec) | No | - | Tuning options. Extends [BaseOutputTuningSpec](#baseoutputtuningspec) with `compression` (valid values: `none`, `gzip`, `snappy`). |

---

##### LokiStack Output

Forwards logs to a Red Hat managed Loki deployment using the Red Hat tenancy model.

The following fields are required as default stream labels for LokiStack and cannot be pruned:
- `.kubernetes.container_name`
- `.kubernetes.namespace_name`
- `.kubernetes.pod_name`

If these fields are not present in the log record, they will be set to the empty string.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `authentication` | [LokiStackAuthentication](#lokistackauthentication) | Yes | - | Authentication credentials. |
| `target` | [LokiStackTarget](#lokistacktarget) | Yes | - | Reference to the in-cluster LokiStack resource. |
| `labelKeys` | [LokiStackLabelKeys](#lokistacklabelkeys) | No | - | Configuration for mapping log record keys to Loki stream labels. Cannot be set when `dataModel` is `Otel`. |
| `dataModel` | string | No | `Viaq` | Data model for storing log data. Valid values: `Viaq`, `Otel`. |
| `tuning` | [LokiTuningSpec](#lokituningspec) | No | - | Tuning options. Extends [BaseOutputTuningSpec](#baseoutputtuningspec) with `compression` (valid values: `none`, `gzip`, `snappy`). Note: `snappy` compression cannot be used when `dataModel` is `Otel`. |

###### LokiStackAuthentication

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `token` | [BearerToken](#bearertoken) | Yes | - | Bearer token for authenticating requests. |

###### LokiStackTarget

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `namespace` | string | Yes | - | Namespace of the in-cluster LokiStack resource. Minimum length: 3. |
| `name` | string | Yes | - | Name of the in-cluster LokiStack resource. Must match pattern `^[a-z][a-z0-9-]{2,62}[a-z0-9]$`. |

###### LokiStackLabelKeys

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `global` | []string | No | `log_type`, `kubernetes.container_name`, `kubernetes.namespace_name`, `kubernetes.pod_name` | Record keys used as stream labels for all tenants. The label `kubernetes_host` is always present and not configurable. |
| `application` | [LokiStackTenantLabelKeys](#lokistacktenantlabelkeys) | No | - | Label keys configuration for the `application` tenant. |
| `infrastructure` | [LokiStackTenantLabelKeys](#lokistacktenantlabelkeys) | No | - | Label keys configuration for the `infrastructure` tenant. |
| `audit` | [LokiStackTenantLabelKeys](#lokistacktenantlabelkeys) | No | - | Label keys configuration for the `audit` tenant. |

###### LokiStackTenantLabelKeys

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `ignoreGlobal` | bool | No | `false` | When true, the tenant does not use labels configured in the global section. |
| `labelKeys` | []string | No | - | Log record keys mapped to Loki stream labels. Combined with global labels by default unless `ignoreGlobal` is true. |

---

##### Syslog Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | Absolute URL with scheme and port. Valid schemes: `tcp`, `tls`, `udp`. Must match pattern `^(tcp\|tls\|udp)://...`. Example: `udp://syslog.example.com:514`. |
| `rfc` | string | Yes | - | RFC format for generated messages. Valid values: `RFC3164`, `RFC5424`. |
| `severity` | string | No | - | Syslog severity. Supports template syntax. Values: `Emergency`, `Alert`, `Critical`, `Error`, `Warning`, `Notice`, `Informational`, `Debug`, or a decimal integer. |
| `facility` | string | No | - | Syslog facility. Supports template syntax. Keywords include: `kernel`, `user`, `mail`, `daemon`, `auth`, `syslog`, `lpr`, `news`, `uucp`, `cron`, `authpriv`, `ftp`, `ntp`, `security`, `console`, `solaris-cron`, `local0`-`local7`, or a decimal integer. |
| `payloadKey` | string | No | - | Record field to use as payload. Must be a single field path in curly brackets (e.g., `{.message}`). If empty, uses the whole message. |
| `appName` | string | No | - | APP-NAME part of the syslog-msg header (RFC 5424). Maximum final value length: 48. Supports template syntax. |
| `procId` | string | No | - | PROCID part of the syslog-msg header (RFC 5424). Maximum final value length: 128. Supports template syntax. |
| `msgId` | string | No | - | MSGID part of the syslog-msg header (RFC 5424). Maximum final value length: 32. Supports template syntax. |
| `enrichment` | string | No | - | Additional modification to the log message. Valid values: `None` (no enrichment), `KubernetesMinimal` (adds `namespace_name`, `pod_name`, `container_name` to the message body). |
| `tuning` | [SyslogTuningSpec](#syslogtuningspec) | No | - | Tuning options with `deliveryMode` only. |

---

##### HTTP Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | URL to send log records to. Must be a valid URL. |
| `authentication` | [HTTPAuthentication](#httpauthentication) | No | - | Authentication credentials. |
| `headers` | map[string]string | No | - | Optional headers sent with requests. |
| `timeout` | int | No | 10 | HTTP request timeout in seconds. |
| `method` | string | No | `POST` | HTTP method. Valid values: `GET`, `HEAD`, `POST`, `PUT`, `DELETE`, `OPTIONS`, `TRACE`, `PATCH`. |
| `proxyURL` | string | No | - | URL of an HTTP or HTTPS proxy. Must be a valid URL if specified. |
| `format` | string | No | - | Data format for sending. Valid values: `json`, `ndjson`. |
| `tuning` | [HTTPTuningSpec](#httptuningspec) | No | - | Tuning options. Extends [BaseOutputTuningSpec](#baseoutputtuningspec) with `compression` (valid values: `none`, `gzip`, `snappy`, `zlib`). |

---

##### OTLP Output

Sends logs via OpenTelemetry Protocol using Red Hat OpenShift logging semantic conventions.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | URL to send log records to. Must match pattern `^(https?):\/\/\S+$`. The OTLP spec recommends it terminate with `/v1/logs`. |
| `authentication` | [HTTPAuthentication](#httpauthentication) | No | - | Authentication credentials. |
| `tuning` | [OTLPTuningSpec](#otlptuningspec) | No | - | Tuning options. Extends [BaseOutputTuningSpec](#baseoutputtuningspec) with `compression` (valid values: `gzip`, `snappy`, `zlib`, `zstd`, `none`). |

---

##### S3 Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `authentication` | [AwsAuthentication](#awsauthentication) | Yes | - | AWS authentication credentials. |
| `region` | string | Yes | - | AWS region. |
| `bucket` | string | Yes | - | S3 bucket name. Must match pattern `^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$`. |
| `keyPrefix` | string | No | - | S3 key prefix for log objects. Supports template syntax (see [Template Syntax](#template-syntax)). Must end in `/` to act as a directory path -- a trailing `/` is not automatically added. |
| `url` | string | No | - | Custom S3-compatible endpoint URL. If not specified, the default AWS S3 endpoint is used. Useful for S3-compatible services like MinIO, Ceph Object Gateway, or Dell EMC ECS. |
| `tuning` | [S3TuningSpec](#s3tuningspec) | No | - | Tuning options. Extends [BaseOutputTuningSpec](#baseoutputtuningspec) with `compression` (valid values: `gzip`, `none`, `snappy`, `zlib`, `zstd`). |

---

##### GoogleCloudLogging Output

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | [GoogleCloudLoggingId](#googlecloudloggingid) | Yes | - | Identifies the destination for logs. |
| `logId` | string | Yes | - | Log ID identifying the log stream. Supports template syntax (see [Template Syntax](#template-syntax)). |
| `authentication` | [GoogleCloudLoggingAuthentication](#googlecloudloggingauthentication) | No | - | Authentication credentials. |
| `tuning` | [GoogleCloudLoggingTuningSpec](#googlecloudloggingtuningspec) | No | - | Tuning options. Same as [BaseOutputTuningSpec](#baseoutputtuningspec). |

###### GoogleCloudLoggingId

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | string | Yes | - | ID type. Valid values: `billingAccount`, `folder`, `project`, `organization`. |
| `value` | string | Yes | - | The value of the ID. |

###### GoogleCloudLoggingAuthentication

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `credentials` | [SecretReference](#secretreference) | Yes | - | Secret containing the GCP credentials JSON file. For service account auth, use a service_account key file. For Workload Identity Federation (WIF), use an external_account configuration file. |
| `token` | [BearerToken](#bearertoken) | No | - | Bearer token used as the subject token for GCP Workload Identity Federation token exchange. Only needed when the credentials file is an `external_account` type. |

---

##### AzureLogsIngestion Output

Sends log events to the Azure Monitor Logs Ingestion API using a Data Collection Rule (DCR).

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | - | URL of the Logs Ingestion API endpoint. Must be a valid URL. |
| `authentication` | [AzureLogsIngestionAuthentication](#azurelogsIngestionauthentication) | Yes | - | Authentication credentials. |
| `dcrImmutableId` | string | Yes | - | Immutable ID of the Data Collection Rule (DCR). |
| `streamName` | string | Yes | - | Name of the custom log stream in the DCR. |
| `tokenScope` | string | No | `https://monitor.azure.com/.default` | Token scope for dedicated Azure regions. |
| `timestampField` | string | No | `TimeGenerated` | Destination field (column) for the timestamp. Common values: `TimeGenerated` (default), `Timestamp` (legacy), `EventStartTime` (ASIM). |
| `tuning` | [AzureLogsIngestionTuningSpec](#azurelogsingestiontuningspec) | No | - | Tuning options. Same as [BaseOutputTuningSpec](#baseoutputtuningspec). |

###### AzureLogsIngestionAuthentication

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | string | Yes | - | Authentication type. Valid values: `clientSecret`, `workloadIdentity`. |
| `clientSecret` | [AzureLogsIngestionClientSecret](#azurelogsingestionclientsecret) | Conditional | - | Azure AD service principal credentials. Required when `type` is `clientSecret`. |
| `workloadIdentity` | [AzureLogsIngestionWorkloadIdentity](#azurelogsingestionworkloadidentity) | Conditional | - | Azure AD Workload Identity credentials. Required when `type` is `workloadIdentity`. |

###### AzureLogsIngestionClientSecret

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tenantId` | string | Yes | - | Azure Active Directory tenant ID. |
| `clientId` | string | Yes | - | Azure Active Directory application (client) ID. |
| `secret` | [SecretReference](#secretreference) | Yes | - | Secret containing the Azure AD client secret. |

###### AzureLogsIngestionWorkloadIdentity

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tenantId` | string | Yes | - | Azure Active Directory tenant ID. |
| `clientId` | string | Yes | - | Azure Active Directory application (client) ID. |
| `token` | [BearerToken](#bearertoken) | Yes | - | Bearer token for authentication. |

---

##### AzureMonitor Output (DEPRECATED)

**DEPRECATED:** Use [AzureLogsIngestion](#azurelogsingestion-output) instead. This output type will be removed in a future release.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `authentication` | [AzureMonitorAuthentication](#azuremonitorauthentication) | Yes | - | Authentication credentials. |
| `customerId` | string | Yes | - | Unique identifier for the Log Analytics workspace. |
| `logType` | string | Yes | - | Record type of the data. Letters, numbers, and underscores only. Max 100 characters. Must match `^[a-zA-Z0-9][a-zA-Z0-9_]{0,99}$`. |
| `azureResourceId` | string | No | - | Resource ID of the Azure resource the data should be associated with. |
| `host` | string | No | - | Alternative host for dedicated Azure regions (e.g., China region). |
| `tuning` | [BaseOutputTuningSpec](#baseoutputtuningspec) | No | - | Tuning options. |

###### AzureMonitorAuthentication

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `sharedKey` | [SecretReference](#secretreference) | Yes | - | Secret containing the shared key for authentication. |

---

#### FilterSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name used to refer to the filter from a pipeline. Must match pattern `^[a-z][a-z0-9-]*[a-z0-9]$`. |
| `type` | string | Yes | - | Type of filter. Valid values: `openshiftLabels`, `detectMultilineException`, `drop`, `kubeAPIAudit`, `parse`, `prune`. |
| `kubeAPIAudit` | [KubeAPIAudit](#kubeapiaudit-filter) | Conditional | - | Kubernetes API audit filter configuration. Required when `type` is `kubeAPIAudit`. |
| `drop` | [][DropTest](#droptest) | Conditional | - | Drop filter tests. Required when `type` is `drop`. |
| `prune` | [PruneFilterSpec](#prunefilterspec) | Conditional | - | Prune filter configuration. Required when `type` is `prune`. |
| `openshiftLabels` | map[string]string | Conditional | - | Labels applied to log records in the `openshift.labels` map. Required when `type` is `openshiftLabels`. |

---

##### detectMultilineException Filter

Enables multi-line error detection of container logs. No additional configuration required.

##### parse Filter

Enables parsing of log entries into structured logs. No additional configuration required.

---

##### drop Filter

A drop filter applies a sequence of tests to a log record and drops the record if any test passes. Each test contains a sequence of conditions -- all conditions must be true for the test to pass.

###### DropTest

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `test` | [][DropCondition](#dropcondition) | Yes (minItems: 1) | - | Array of conditions that are ANDed together. |

###### DropCondition

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `field` | [FieldPath](#fieldpath) | No | - | Dot-delimited path to a field in the log record. Must start with `.`. |
| `matches` | string | No | - | Regular expression. If the field matches, the log record is dropped. Cannot be used with `notMatches`. |
| `notMatches` | string | No | - | Regular expression. If the field does NOT match, the log record is dropped. Cannot be used with `matches`. |

---

##### prune Filter

Prunes log record fields to reduce the size of logs flowing into a log store.

###### PruneFilterSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `in` | [][FieldPath](#fieldpath) | No | - | Fields to remove from the log record. Cannot contain `.log_type`, `.log_source`, or `.message`. If used with GoogleCloudLogging pipeline, `.hostname` cannot be added. |
| `notIn` | [][FieldPath](#fieldpath) | No | - | Fields to keep -- all other fields are removed. Must contain `.log_type`, `.log_source`, and `.message`. If used with GoogleCloudLogging pipeline, `.hostname` must be included. |

---

##### kubeAPIAudit Filter

Filters Kubernetes API server audit logs based on audit policy rules. Rules are checked in order; the first matching rule is used. See the [Kubernetes Audit Policy](https://kubernetes.io/docs/reference/config-api/apiserver-audit.v1/#audit-k8s-io-v1-Policy) for standard rule behavior.

Audit levels determine how much data is included:
- **None:** Event is dropped.
- **Metadata:** Only audit metadata is included.
- **Request:** Audit metadata and request body are included.
- **RequestResponse:** All data is included (metadata, request body, response body).

Extensions over the standard Kube Audit Policy:
- Wildcards (`*`) are supported in names of users, groups, namespaces, and resources.
- Default rules apply for events not matching any rule (user events forwarded; read-only system events dropped; same-namespace service account writes dropped; all others forwarded).
- Events can be dropped based on HTTP response status code.

###### KubeAPIAudit

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `rules` | []PolicyRule | No | default rules apply | Audit policy rules. Rules are strictly ordered; the first match is used. |
| `omitStages` | []Stage | No | - | Stages for which no events are created. Can also be specified per rule (union of both). |
| `omitResponseCodes` | []int | No | `[404, 409, 422, 429]` | HTTP status codes for which no events are created. Set to empty list `[]` to omit no status codes. |

---

##### openshiftLabels Filter

Labels applied to log records passing through a pipeline. These labels appear in the `openshift.labels` map in the log record. The value is a `map[string]string` -- no additional nested configuration.

---

#### PipelineSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Name of the pipeline. Must match pattern `^[a-z][a-z0-9-]*[a-z0-9]$`. |
| `inputRefs` | []string | Yes (minItems: 1) | - | Names of inputs to this pipeline. Built-in inputs: `application`, `infrastructure`, `audit`. |
| `outputRefs` | []string | Yes (minItems: 1) | - | Names of outputs from this pipeline. |
| `filterRefs` | []string | No | - | Names of filters applied in order. If a filter drops a record, subsequent filters are not applied. |

---

### Common Types

#### SecretReference

References a single key in a Secret in the same namespace.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `key` | string | Yes | - | Name of the key inside the referenced Secret. |
| `secretName` | string | Yes | - | Name of the Secret containing the referenced value. |

#### ValueReference

References a single field in either a ConfigMap or Secret in the same namespace. Exactly one of `configMapName` or `secretName` must be set.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `key` | string | Yes | - | Name of the key in the referenced ConfigMap or Secret. |
| `configMapName` | string | No | - | Name of the ConfigMap containing the referenced value. |
| `secretName` | string | No | - | Name of the Secret containing the referenced value. |

#### BearerToken

Configures the source of a bearer token for authentication.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `from` | string | Yes | - | Source of the token. Valid values: `secret`, `serviceAccount`. |
| `secret` | [BearerTokenSecretKey](#bearertokensecretkey) | Conditional | - | Secret containing the token. Required when `from` is `secret`. |

##### BearerTokenSecretKey

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `key` | string | Yes | - | Name of the key in the referenced Secret. |
| `name` | string | Yes | - | Name of the Secret. |

#### HTTPAuthentication

Common authentication credentials for HTTP-based outputs.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `token` | [BearerToken](#bearertoken) | No | - | Bearer token for authentication. |
| `username` | [SecretReference](#secretreference) | No | - | Secret containing the username. |
| `password` | [SecretReference](#secretreference) | No | - | Secret containing the password. |

#### TLSSpec

Options for TLS connections (used by inputs).

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `ca` | [ValueReference](#valuereference) | No | - | Custom list of trusted certificate authorities. |
| `certificate` | [ValueReference](#valuereference) | No | - | Server certificate to use. |
| `key` | [SecretReference](#secretreference) | No | - | Private key of the server certificate. |
| `keyPassphrase` | [SecretReference](#secretreference) | No | - | Passphrase to unlock the private key. |

#### BaseOutputTuningSpec

Common tuning parameters for outputs.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `deliveryMode` | string | No | in-memory (AtMostOnce behavior) | Delivery mode for log forwarding. Valid values: `AtLeastOnce` (durable, possible duplicates), `AtMostOnce` (in-memory, possible loss). |
| `maxWrite` | Quantity | No | - | Maximum payload size in bytes of a single send to the output. |
| `minRetryDuration` | Duration | No | - | Minimum time to wait between retry attempts after a delivery failure. |
| `maxRetryDuration` | Duration | No | - | Maximum time to wait between retry attempts after a delivery failure. |

#### LimitSpec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `maxRecordsPerSecond` | int64 | Yes | - | Maximum number of log records allowed per input/output in a pipeline. Records exceeding this limit are dropped. Must be greater than 0. |

#### FieldPath

A dot-delimited path to a field in the log record. Must start with `.`. The path can contain alphanumeric characters and underscores (`a-zA-Z0-9_`). Segments containing characters outside this range must be quoted.

Pattern: `^(\.[a-zA-Z0-9_]+|\."[^"]+")(\.[a-zA-Z0-9_]+|\."[^"]+")*$`

Examples: `.kubernetes.namespace_name`, `.log_type`, `.kubernetes.labels.foobar`, `.kubernetes.labels."foo-bar/baz"`

#### Template Syntax

Several string fields support template syntax for dynamic per-event values. Templates combine static text with dynamic field references.

- Dynamic values are encased in single curly brackets `{}` and must end with a static fallback value separated by `||`.
- Static values can contain alphanumeric characters, dashes, underscores, dots, and forward slashes.

Examples:
1. `foo-{.bar||"none"}`
2. `{.foo||.bar||"missing"}`
3. `foo.{.bar.baz||.qux.quux.corge||.grault||"nil"}-waldo.fred{.plugh||"none"}`

---

### Status Fields

#### ClusterLogForwarderStatus

| Field | Type | Description |
|-------|------|-------------|
| `conditions` | []metav1.Condition | Top-level conditions of the log forwarder. |
| `inputConditions` | []metav1.Condition | Conditions mapped to input names. |
| `outputConditions` | []metav1.Condition | Conditions mapped to output names. |
| `filterConditions` | []metav1.Condition | Conditions mapped to filter names. |
| `pipelineConditions` | []metav1.Condition | Conditions mapped to pipeline names. |

#### Condition Types

| Condition Type | Description |
|----------------|-------------|
| `Ready` | Indicates the service is ready. `True` means operands are running and providing service. `False` means operands cannot provide service and the operator cannot recover without external changes. |
| `observability.openshift.io/Authorized` | Authorization state of the service. |
| `observability.openshift.io/Valid` | Validation state of the overall resource. |
| `observability.openshift.io/ValidInput` | Validation state prefix for a named input. |
| `observability.openshift.io/ValidOutput` | Validation state prefix for a named output. |
| `observability.openshift.io/ValidPipeline` | Validation state prefix for a named pipeline. |
| `observability.openshift.io/ValidFilter` | Validation state prefix for a named filter. |
| `observability.openshift.io/LogLevel` | Validates the value of the log-level annotation. |
| `observability.openshift.io/MaxUnavailableAnnotation` | Validates the value of the max-unavailable-rollout annotation. |

#### Common Reasons

| Reason | Description |
|--------|-------------|
| `ClusterRolesExist` | The collector service account is bound to all required cluster roles. |
| `ClusterRoleMissing` | The collector service account is missing one or more required cluster roles. |
| `DeploymentError` | An error occurred deploying the collector or a related component. |
| `InitializationFailed` | Failure initializing the reconciliation context. |
| `ManagementStateUnmanaged` | The workload is in an Unmanaged state. |
| `MissingSpec` | A type is specified without a defined spec. |
| `ReconciliationComplete` | The operator has initialized, validated, and deployed resources. |
| `ServiceAccountDoesNotExist` | The ServiceAccount was not found. |
| `ServiceAccountCheckFailure` | Failure retrieving the ServiceAccount. |
| `ValidationSuccess` | Validation succeeded. |
| `ValidationFailure` | Validation failed. |
| `UnknownState` | The operator cannot determine the state of the deployment. |
| `FailureToRemoveStaleWorkload` | A failure occurred removing a stale workload after the deployment type changed. |
| `LogLevelSupported` | The log-level annotation value is valid and supported. |
| `MaxUnavailableAnnotationSupported` | The max-unavailable-rollout annotation value is valid and supported. |

---

## LogFileMetricExporter (logging.openshift.io/v1alpha1)

- **Short name:** `lfme`
- **Scope:** Namespaced
- **Categories:** logging
- **Name:** Must be `instance`

The LogFileMetricExporter deploys a DaemonSet that exports metrics about log files on cluster nodes.

> **Note:** This CRD is at `v1alpha1` maturity. Its schema may change in future releases.

---

### Spec Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `resources` | corev1.ResourceRequirements | No | - | Resource requirements (requests/limits) for the exporter containers. |
| `nodeSelector` | map[string]string | No | - | Node labels for scheduling the exporter pods to specific nodes. |
| `tolerations` | []corev1.Toleration | No | - | Tolerations that exporter pods will accept. |
| `networkPolicy` | [NetworkPolicy](#networkpolicy-lfme) | No | - | Network policy for the exporter. |

#### NetworkPolicy (LFME)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `ruleSet` | string | Yes | - | Type of network policy rule set. Valid values: `AllowIngressMetrics`, `AllowAllIngressEgress`. |

---

### Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `conditions` | []metav1.Condition | Conditions of the Log File Metric Exporter. |

#### Condition Reasons

| Reason | Description |
|--------|-------------|
| `Valid` | The LogFileMetricExporter is deployed successfully. |
| `Invalid` | There was an issue with the LogFileMetricExporter instance. |
