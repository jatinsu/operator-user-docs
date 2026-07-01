# CRD API Reference

This document describes the Kubernetes Custom Resource Definitions (CRDs) provided by the Cluster Logging Operator, including their resource structure, status fields, conditions, and usage patterns.

For detailed configuration of individual spec fields (outputs, filters, inputs), see [configuration-reference.md](configuration-reference.md).

---

## CRD Overview

The Cluster Logging Operator manages two CRDs:

| CRD | API Group/Version | Short Names | Scope | Purpose |
|-----|-------------------|-------------|-------|---------|
| ClusterLogForwarder | `observability.openshift.io/v1` | `obsclf`, `clf` | Namespaced | Primary CRD for log collection and forwarding |
| LogFileMetricExporter | `logging.openshift.io/v1alpha1` | `lfme` | Namespaced | Exports log file metrics from cluster nodes |

---

## ClusterLogForwarder API

```yaml
apiVersion: observability.openshift.io/v1
kind: ClusterLogForwarder
```

### Metadata

Standard Kubernetes metadata applies. The operator recognizes the following annotations:

| Annotation | Description | Default |
|------------|-------------|---------|
| `observability.openshift.io/log-level` | Set the Vector collector log level. Valid values: `trace`, `debug`, `info`, `warn`, `error`, `off` | `warn` |
| `observability.openshift.io/max-unavailable-rollout` | (Deprecated) Override maxUnavailable for the collector DaemonSet rolling update. Absolute number or percentage. Prefer `spec.collector.maxUnavailable` instead. | `100%` |
| `logging.openshift.io/dev-preview-enable-collector-as-deployment` | Dev preview: deploy the collector as a Deployment instead of a DaemonSet (for HCP webhook audit log collection) | Not set |

### Spec Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `managementState` | `Managed` or `Unmanaged` | No | Controls whether the operator actively reconciles this resource. Default: `Managed`. |
| `collector` | [CollectorSpec](#collectorspec) | No | Resource limits, scheduling, and rollout configuration for collector pods. |
| `inputs` | [][InputSpec](configuration-reference.md) | No | Named filters for log messages. Three built-in inputs (`application`, `infrastructure`, `audit`) are always available without definition here. |
| `outputs` | [][OutputSpec](configuration-reference.md) | Yes | Named destinations for log messages. |
| `filters` | [][FilterSpec](configuration-reference.md) | No | Named transformations applied to log records passing through pipelines. |
| `pipelines` | [][PipelineSpec](#pipelinespec) | Yes | Connect inputs to outputs, optionally applying filters. |
| `serviceAccount` | [ServiceAccount](#serviceaccount) | Yes | The ServiceAccount used by collector pods. |

See [configuration-reference.md](configuration-reference.md) for full documentation of input, output, and filter types.

#### CollectorSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resources` | `ResourceRequirements` | No | CPU and memory requests/limits for collector pods. |
| `nodeSelector` | `map[string]string` | No | Node label selector for scheduling collector pods. |
| `tolerations` | `[]Toleration` | No | Tolerations for collector pod scheduling. |
| `affinity` | `Affinity` | No | Affinity and anti-affinity rules for collector pod placement. |
| `networkPolicy` | [NetworkPolicy](#networkpolicy-clusterlogforwarder) | No | Network policy configuration for the collector. |
| `maxUnavailable` | `IntOrString` | No | Maximum unavailable pods during rolling update. Absolute number (e.g., `50`) or percentage (e.g., `"50%"`). Pattern: `^(?:[0-9]{1,2}\|100)%?$`. Default: `100%`. |

#### PipelineSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Unique pipeline name. Must match `^[a-z][a-z0-9-]*[a-z0-9]$`. |
| `inputRefs` | `[]string` | Yes | Names of inputs to this pipeline (built-in or custom). |
| `outputRefs` | `[]string` | Yes | Names of outputs to send matched logs to. |
| `filterRefs` | `[]string` | No | Names of filters to apply, in order. |
| `detectMultilineErrors` | `bool` | No | Enable multiline error detection. |

#### ServiceAccount

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Name of the ServiceAccount in the same namespace. Must match `^[a-z][a-z0-9-]{2,62}[a-z0-9]$`. |

#### NetworkPolicy (ClusterLogForwarder)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ruleSet` | `NetworkPolicyRuleSetType` | Yes | The type of network policy rule set. |

Valid `ruleSet` values:

| Value | Description |
|-------|-------------|
| `AllowAllIngressEgress` | Allows all ingress and egress traffic |
| `RestrictIngressEgress` | Restricts ingress and egress traffic |

### Status

The `ClusterLogForwarderStatus` provides the reconciliation state of the forwarder and validation results for each component.

#### Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `conditions` | `[]metav1.Condition` | Overall forwarder conditions (ready state, authorization, validation) |
| `inputConditions` | `[]metav1.Condition` | Per-input validation status |
| `outputConditions` | `[]metav1.Condition` | Per-output validation status |
| `filterConditions` | `[]metav1.Condition` | Per-filter validation status |
| `pipelineConditions` | `[]metav1.Condition` | Per-pipeline validation status |

#### Condition Types

| Condition Type | Description |
|----------------|-------------|
| `Ready` | Operands are running and providing service |
| `observability.openshift.io/Authorized` | ServiceAccount authorization state |
| `observability.openshift.io/Valid` | Overall spec validation state |
| `observability.openshift.io/ValidInput{Name}` | Per-input validation (appears in `inputConditions`) |
| `observability.openshift.io/ValidOutput{Name}` | Per-output validation (appears in `outputConditions`) |
| `observability.openshift.io/ValidPipeline{Name}` | Per-pipeline validation (appears in `pipelineConditions`) |
| `observability.openshift.io/ValidFilter{Name}` | Per-filter validation (appears in `filterConditions`) |
| `observability.openshift.io/LogLevel` | Log level annotation validation |
| `observability.openshift.io/MaxUnavailableAnnotation` | Max unavailable annotation validation |

Each condition has a `status` of `True`, `False`, or `Unknown`.

#### Condition Reasons

| Reason | Description |
|--------|-------------|
| `ReconciliationComplete` | Resources have been successfully deployed |
| `ValidationSuccess` | Spec validation passed |
| `ValidationFailure` | Spec validation failed |
| `ClusterRolesExist` | Required cluster roles are bound to the ServiceAccount |
| `ClusterRoleMissing` | Required cluster roles are not found for the ServiceAccount |
| `DeploymentError` | Error occurred deploying the collector or related component |
| `InitializationFailed` | Failure initializing the reconciliation context |
| `FailureToRemoveStaleWorkload` | Failure removing a stale workload after deployment type change |
| `ServiceAccountDoesNotExist` | Referenced ServiceAccount not found in the namespace |
| `ServiceAccountCheckFailure` | Failure retrieving the ServiceAccount |
| `ManagementStateUnmanaged` | Resource is in `Unmanaged` state; operator will not act on it |
| `MissingSpec` | A type is specified without a corresponding spec definition |
| `LogLevelSupported` | The log-level annotation value is valid |
| `MaxUnavailableAnnotationSupported` | The max-unavailable-rollout annotation value is valid |
| `KubeCacheAnnotationSupported` | The apiserver-cache annotation value is valid |
| `UnknownState` | Cannot determine the deployment state |

### Built-in Inputs

Three inputs are always available without explicit definition in the `inputs` array. Reference them by name in `pipeline.inputRefs`:

| Input Name | Log Type | Description |
|------------|----------|-------------|
| `application` | Container logs | Logs from containers in non-infrastructure namespaces |
| `infrastructure` | System logs | Journald logs from nodes and container logs from system namespaces (`default`, `kube-*`, `openshift-*`) |
| `audit` | Audit logs | Kubernetes API server audit logs, OpenShift API audit logs, node auditd logs, and OVN audit logs |

### Naming Conventions

All named resources must follow these regex patterns:

| Resource | Pattern | Example |
|----------|---------|---------|
| Input, Output, Filter, Pipeline name | `^[a-z][a-z0-9-]*[a-z0-9]$` | `my-output-1` |
| ServiceAccount name | `^[a-z][a-z0-9-]{2,62}[a-z0-9]$` | `collector-sa` |
| ClusterLogForwarder name | `^[a-z][a-z0-9-]{1,61}[a-z0-9]$` | `collector` |

Names must start with a lowercase letter, end with a lowercase letter or digit, and contain only lowercase letters, digits, and hyphens.

### Validation Rules

The operator validates the following before deploying the collector:

1. All inputs referenced in `pipeline.inputRefs` exist (either built-in or defined in `spec.inputs`).
2. All outputs referenced in `pipeline.outputRefs` exist in `spec.outputs`.
3. All filters referenced in `pipeline.filterRefs` exist in `spec.filters`.
4. The ServiceAccount named in `spec.serviceAccount.name` exists in the same namespace.
5. The ServiceAccount is bound to the required ClusterRoles for each log type being collected (see [RBAC Requirements](#rbac-requirements-for-collector)).
6. Output-specific requirements are met (URL format, required authentication fields, TLS configuration).
7. Filter-specific requirements are met (regex compilation, valid field paths, prune constraints).

When validation fails, the operator sets the relevant condition to `False` with a `ValidationFailure` reason and a message describing the problem.

### RBAC Requirements for Collector

The ServiceAccount referenced by the ClusterLogForwarder must be bound to ClusterRoles that authorize collection of each log type used in the pipelines:

| Log Type | Required ClusterRole |
|----------|---------------------|
| `application` | `collect-application-logs` |
| `infrastructure` | `collect-infrastructure-logs` |
| `audit` | `collect-audit-logs` |

Bind these roles using a ClusterRoleBinding:

```bash
oc adm policy add-cluster-role-to-user collect-application-logs \
  -z <service-account-name> -n <namespace>
```

For writing logs to a LokiStack output, the collector ServiceAccount also needs Loki-specific ClusterRoles:

| ClusterRole | Permits Writing |
|-------------|-----------------|
| `cluster-logging-write-application-logs` | Application logs to Loki |
| `cluster-logging-write-infrastructure-logs` | Infrastructure logs to Loki |
| `cluster-logging-write-audit-logs` | Audit logs to Loki |
| `logging-collector-logs-writer` | All log types to Loki (combined role) |

Additional ClusterRoles used by the collector:

| ClusterRole | Purpose |
|-------------|---------|
| `metadata-reader` | Allows get/list/watch on pods, namespaces, and nodes for metadata enrichment |

---

## LogFileMetricExporter API

```yaml
apiVersion: logging.openshift.io/v1alpha1
kind: LogFileMetricExporter
```

The LogFileMetricExporter must be named `instance` and deployed in the `openshift-logging` namespace.

### Spec Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resources` | `ResourceRequirements` | No | CPU and memory requests/limits for exporter pods |
| `nodeSelector` | `map[string]string` | No | Node label selector for scheduling exporter pods |
| `tolerations` | `[]Toleration` | No | Tolerations for exporter pod scheduling |
| `networkPolicy` | [NetworkPolicy](#networkpolicy-logfilemetricexporter) | No | Network policy configuration for the exporter |

#### NetworkPolicy (LogFileMetricExporter)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ruleSet` | `NetworkPolicyRuleSetType` | Yes | The type of network policy rule set |

Valid `ruleSet` values (note: different from ClusterLogForwarder):

| Value | Description |
|-------|-------------|
| `AllowIngressMetrics` | Allows only ingress metrics traffic |
| `AllowAllIngressEgress` | Allows all ingress and egress traffic |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `conditions` | `[]metav1.Condition` | Status conditions for the exporter |

LogFileMetricExporter condition reasons:

| Reason | Description |
|--------|-------------|
| `Valid` | The resource is valid |
| `Invalid` | The resource is invalid |

---

## Common Types

### FieldPath

Log record field paths use dot notation starting with `.` to reference fields within a log record.

**Pattern:** `^(\.[a-zA-Z0-9_]+|\."[^"]+")(\.[a-zA-Z0-9_]+|\."[^"]+")*$`

Examples:
- `.kubernetes.namespace_name`
- `.log_type`
- `.message`
- `.kubernetes.labels."foo-bar/baz"` (quoted segment for special characters)

**Protected fields** (cannot be removed by the prune filter):
- `.log_type`
- `.log_source`
- `.message`

### Dynamic Template Values

Several output fields support dynamic templates that construct values from log record fields at runtime.

**Format:** `{.field||"fallback"}` or chained `{.field1||.field2||"static"}`

Rules:
- Static portions may contain alphanumeric characters, dashes, underscores, dots, and forward slashes.
- Dynamic portions are enclosed in `{}` and use dot-notation field paths.
- Dynamic values must end with a static fallback string (quoted) separated by `||`.
- Multiple field references can be chained with `||` as alternatives before the fallback.

**Examples:**
```
my-index-{.kubernetes.namespace_name||"unknown"}
{.log_type||"default"}
foo.{.bar.baz||.qux.quux.corge||.grault||"nil"}-waldo.fred{.plugh||"none"}
```

**Fields that support dynamic templates:**

| Output Type | Field |
|-------------|-------|
| CloudWatch | `groupName` |
| Elasticsearch | `index` |
| Kafka | `topic` |
| Splunk | `index`, `source` |
| Amazon S3 | `keyPrefix` |
| Loki | `tenantKey` |
| Google Cloud Logging | `logId` |
| Syslog | `severity`, `facility`, `appName`, `procId`, `msgId` |

---

## Useful Commands

### Listing and Inspecting Resources

```bash
# List all ClusterLogForwarders across namespaces
oc get clusterlogforwarder -A

# Get the full YAML of a ClusterLogForwarder (including status)
oc get clf collector -n openshift-logging -o yaml

# Describe a ClusterLogForwarder (includes events)
oc describe clf collector -n openshift-logging

# List LogFileMetricExporters
oc get logfilemetricexporter -n openshift-logging
```

### Checking Collector Health

```bash
# Check collector pods
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector

# View collector logs
oc logs -n openshift-logging -l app.kubernetes.io/component=collector --tail=50

# Check operator logs
oc logs -n openshift-logging deployment/cluster-logging-operator --tail=50
```

### Checking RBAC

```bash
# Verify ClusterRoleBindings for the collector ServiceAccount
oc get clusterrolebinding -o wide | grep <service-account-name>

# Check if a ServiceAccount can collect application logs
# Note: This command requires the operator to be installed (the ClusterRoles define the custom verb and resource).
oc auth can-i collect application \
  --as=system:serviceaccount:<namespace>:<service-account-name>
```

### Reading Conditions

```bash
# Get all conditions from a ClusterLogForwarder
oc get clf collector -n openshift-logging \
  -o jsonpath='{range .status.conditions[*]}{.type}{"\t"}{.status}{"\t"}{.reason}{"\t"}{.message}{"\n"}{end}'

# Check if the forwarder is ready
oc get clf collector -n openshift-logging \
  -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

---

## ClusterLogForwarder Editor and Viewer Roles

The operator installs ClusterRoles for managing access to ClusterLogForwarder resources:

| ClusterRole | Permissions |
|-------------|------------|
| `clusterlogforwarder-editor-role` | Create, delete, get, list, patch, update, watch on ClusterLogForwarder resources and their status |
| `clusterlogforwarder-viewer-role` | Get, list, watch on ClusterLogForwarder resources and their status |

---

## Source References

The API types are defined in the following source files within the [cluster-logging-operator](https://github.com/openshift/cluster-logging-operator) repository:

| File | Contents |
|------|----------|
| `api/observability/v1/clusterlogforwarder_types.go` | ClusterLogForwarder spec, status, collector, pipeline, and network policy types |
| `api/observability/v1/conditions.go` | Condition type and reason constants |
| `api/observability/v1/input_types.go` | Input types and built-in input names |
| `api/observability/v1/output_types.go` | Output types and output-specific specs |
| `api/observability/v1/filter_types.go` | Filter types and filter-specific specs |
| `api/logging/v1alpha1/log_file_metrics_exporter_types.go` | LogFileMetricExporter spec and status |
| `internal/constants/annotations.go` | Annotation key constants |
