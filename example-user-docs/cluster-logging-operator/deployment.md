# Cluster Logging Operator Deployment Guide

This guide covers installing, configuring, upgrading, and uninstalling the Cluster Logging Operator (CLO) on OpenShift.

---

## Installation

### Prerequisites

- OpenShift Container Platform 4.14 or later with cluster-admin access.
- For LokiStack-based log storage: the Loki Operator must be installed and an object storage backend (S3, GCS, Azure Blob, or Swift) must be available.

### Namespace Setup

Create the `openshift-logging` namespace with the required labels before installing the operator.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-logging
  labels:
    openshift.io/cluster-monitoring: "true"
    pod-security.kubernetes.io/enforce: privileged
    pod-security.kubernetes.io/audit: privileged
    pod-security.kubernetes.io/warn: privileged
    security.openshift.io/scc.podSecurityLabelSync: "false"
  annotations:
    openshift.io/node-selector: ""
```

Apply the namespace:

```bash
oc apply -f namespace.yaml
```

The `openshift.io/cluster-monitoring` label enables the in-cluster Prometheus instance to scrape metrics from the logging components. The pod security labels allow the collector pods to run with the privileged security context they require. Setting `openshift.io/node-selector` to an empty string ensures logging pods can be scheduled on any node regardless of the cluster default node selector.

### Install via OperatorHub (Web Console)

1. In the OpenShift web console, navigate to **Operators** > **OperatorHub**.
2. Search for **Cluster Logging**.
3. Select the **Cluster Logging** operator tile.
4. On the Install screen, configure the following:
   - **Update channel**: Select the latest available **stable** channel (e.g., `stable-6.5`). Verify available channels with `oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'`.
   - **Installation mode**: A specific namespace on the cluster
   - **Installed Namespace**: `openshift-logging`
   - **Update approval**: Automatic (recommended) or Manual
5. Click **Install** and wait for the operator to reach the `Succeeded` phase.

### Install via CLI

Create an OperatorGroup and Subscription to install the operator from the command line.

**OperatorGroup:**

```yaml
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: openshift-logging
  namespace: openshift-logging
spec:
  targetNamespaces:
  - openshift-logging
```

**Subscription:**

```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: cluster-logging
  namespace: openshift-logging
spec:
  channel: stable-6.5
  name: cluster-logging
  source: redhat-operators
  sourceNamespace: openshift-marketplace
  installPlanApproval: Automatic
```

Apply both resources:

```bash
oc apply -f operatorgroup.yaml
oc apply -f subscription.yaml
```

### Verify Installation

Confirm the ClusterServiceVersion reaches the `Succeeded` phase:

```bash
oc get csv -n openshift-logging
```

Verify the operator pod is running:

```bash
oc get pods -n openshift-logging
```

You should see a pod named `cluster-logging-operator-*` in a `Running` state.

---

## Service Account and RBAC Setup

The Cluster Logging Operator uses a service account to collect and forward logs. The operator defines several ClusterRoles that control which log types the collector can access and where it can write.

### Collection ClusterRoles

These ClusterRoles grant the collector permission to read logs from the node filesystem:

| ClusterRole | Description |
|---|---|
| `collect-application-logs` | Allows collecting container logs from application workloads |
| `collect-infrastructure-logs` | Allows collecting logs from OpenShift platform components and journal logs |
| `collect-audit-logs` | Allows collecting Kubernetes API server, OpenShift API server, and node audit logs |

### LokiStack Write ClusterRoles

When forwarding to a LokiStack instance, additional ClusterRoles authorize writing to each tenant:

| ClusterRole | Description |
|---|---|
| `cluster-logging-write-application-logs` | Grants write access to the application tenant in LokiStack |
| `cluster-logging-write-infrastructure-logs` | Grants write access to the infrastructure tenant in LokiStack |
| `cluster-logging-write-audit-logs` | Grants write access to the audit tenant in LokiStack |

### Create a Service Account and Bind Roles

Create the service account:

```bash
oc create serviceaccount collector -n openshift-logging
```

Bind the collection roles:

```bash
oc adm policy add-cluster-role-to-user collect-application-logs \
  system:serviceaccount:openshift-logging:collector

oc adm policy add-cluster-role-to-user collect-infrastructure-logs \
  system:serviceaccount:openshift-logging:collector

oc adm policy add-cluster-role-to-user collect-audit-logs \
  system:serviceaccount:openshift-logging:collector
```

If forwarding to LokiStack, also bind the write roles:

```bash
oc adm policy add-cluster-role-to-user cluster-logging-write-application-logs \
  system:serviceaccount:openshift-logging:collector

oc adm policy add-cluster-role-to-user cluster-logging-write-infrastructure-logs \
  system:serviceaccount:openshift-logging:collector

oc adm policy add-cluster-role-to-user cluster-logging-write-audit-logs \
  system:serviceaccount:openshift-logging:collector
```

---

## LokiStack Integration

LokiStack is the recommended log storage backend for the Cluster Logging Operator. This section walks through the full setup.

### Step 1: Install the Loki Operator

Install the Loki Operator from OperatorHub into the `openshift-operators-redhat` namespace. Verify the available channel with `oc get packagemanifest loki-operator -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'`, then create a Subscription:

```yaml
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: loki-operator
  namespace: openshift-operators-redhat
spec:
  channel: alpha
  name: loki-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
  installPlanApproval: Automatic
```

```bash
oc apply -f loki-subscription.yaml
```

### Step 2: Create a Storage Secret

Create a secret containing your object storage credentials. The following example uses S3:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: logging-loki-s3
  namespace: openshift-logging
stringData:
  access_key_id: "<your-access-key>"
  access_key_secret: "<your-secret-key>"
  bucketnames: "<bucket-name>"
  endpoint: "https://s3.amazonaws.com"
  region: "<region>"
```

```bash
oc apply -f loki-secret.yaml
```

Replace the placeholder values with your actual S3 credentials and bucket details.

### Step 3: Create the LokiStack Custom Resource

```yaml
apiVersion: loki.grafana.com/v1
kind: LokiStack
metadata:
  name: logging-loki
  namespace: openshift-logging
spec:
  size: 1x.small
  storage:
    schemas:
    - version: v13
      effectiveDate: "2024-10-25"
    secret:
      name: logging-loki-s3
      type: s3
  storageClassName: gp3-csi
  tenants:
    mode: openshift-logging
```

```bash
oc apply -f lokistack.yaml
```

Wait for the LokiStack pods to become ready:

```bash
oc get pods -n openshift-logging -l app.kubernetes.io/instance=logging-loki
```

### Step 4: Grant Write Permissions

Bind the LokiStack write roles to your collector service account as described in the [Service Account and RBAC Setup](#service-account-and-rbac-setup) section above.

### Step 5: Create a ClusterLogForwarder with LokiStack Output

Create a ClusterLogForwarder that sends logs to the LokiStack instance:

```yaml
apiVersion: observability.openshift.io/v1
kind: ClusterLogForwarder
metadata:
  name: instance
  namespace: openshift-logging
spec:
  serviceAccount:
    name: collector
  outputs:
  - name: default-lokistack
    type: lokiStack
    lokiStack:
      target:
        name: logging-loki
        namespace: openshift-logging
      authentication:
        token:
          from: serviceAccount
    tls:
      ca:
        key: service-ca.crt
        configMapName: openshift-service-ca.crt
  pipelines:
  - name: default-pipeline
    inputRefs:
    - application
    - infrastructure
    outputRefs:
    - default-lokistack
  filters:
  - name: detect-multiline
    type: detectMultilineException
```

```bash
oc apply -f clusterlogforwarder.yaml
```

Verify that collector pods are deployed:

```bash
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector
```

---

## Collector Configuration

The `CollectorSpec` section of the ClusterLogForwarder allows you to tune the collector deployment. The following fields are available:

### resources

Set CPU and memory requests and limits for the collector containers:

```yaml
spec:
  collector:
    resources:
      limits:
        cpu: "500m"
        memory: "1Gi"
      requests:
        cpu: "100m"
        memory: "256Mi"
```

### nodeSelector

Restrict which nodes the collector pods run on:

```yaml
spec:
  collector:
    nodeSelector:
      node-role.kubernetes.io/infra: ""
```

### tolerations

Allow collector pods to schedule on nodes with specific taints:

```yaml
spec:
  collector:
    tolerations:
    - key: "node-role.kubernetes.io/infra"
      operator: "Exists"
      effect: "NoSchedule"
```

### affinity

Apply Kubernetes affinity and anti-affinity rules to collector pods. Accepts standard `nodeAffinity`, `podAffinity`, and `podAntiAffinity` configurations.

### networkPolicy

Controls the network policy applied to collector pods. Two modes are available:

- `AllowAllIngressEgress` -- No network restrictions on the collector pods (default).
- `RestrictIngressEgress` -- Restricts traffic to only the required endpoints for log forwarding.

```yaml
spec:
  collector:
    networkPolicy: RestrictIngressEgress
```

### maxUnavailable

Controls the rolling update strategy for the collector DaemonSet. Specifies the maximum number (or percentage) of collector pods that can be unavailable during a rollout:

```yaml
spec:
  collector:
    maxUnavailable: 1
```

---

## Upgrading

The Cluster Logging Operator is managed by the Operator Lifecycle Manager (OLM), which handles upgrades automatically based on your Subscription configuration.

- **Channel-based updates**: The Subscription specifies the update channel (e.g., `stable-6.5`). OLM delivers new versions as they are published to that channel.
- **Skip range**: The operator's skip range ensures safe upgrades from version 6.2.0 and later. Earlier versions within the range are automatically skipped to reach the latest release.
- **No manual steps**: Minor version upgrades within the same channel require no manual intervention. OLM updates the ClusterServiceVersion and restarts the operator pod automatically.
- **Major version changes**: For upgrades from CLO v5 to v6, consult the v6.0 upgrade guide in the operator's documentation. Major version changes may involve API changes, deprecated fields, and changes to the logging data model.

To check the current installed version:

```bash
oc get csv -n openshift-logging -o custom-columns=NAME:.metadata.name,VERSION:.spec.version,PHASE:.status.phase
```

To verify the Subscription health:

```bash
oc get subscription cluster-logging -n openshift-logging -o yaml
```

---

## Uninstalling

Follow these steps to fully remove the Cluster Logging Operator and its resources from the cluster.

### Step 1: Delete ClusterLogForwarder Resources

Remove all ClusterLogForwarder instances to stop log collection:

```bash
oc delete clusterlogforwarder --all -n openshift-logging
```

### Step 2: Delete the Subscription

Remove the operator Subscription to prevent OLM from reinstalling it:

```bash
oc delete subscription cluster-logging -n openshift-logging
```

### Step 3: Delete the ClusterServiceVersion

Identify and delete the CSV to remove the operator deployment:

```bash
CSV_NAME=$(oc get csv -n openshift-logging -o name | grep cluster-logging)
oc delete $CSV_NAME -n openshift-logging
```

### Step 4: Delete the Namespace (Optional)

If no other resources in `openshift-logging` are needed, delete the namespace:

```bash
oc delete namespace openshift-logging
```

### Step 5: Clean Up Cluster-Scoped Resources

Remove any cluster-scoped resources left behind by the operator:

```bash
oc delete clusterrole collect-application-logs collect-infrastructure-logs collect-audit-logs \
  cluster-logging-write-application-logs cluster-logging-write-infrastructure-logs \
  cluster-logging-write-audit-logs

oc delete clusterrolebinding collect-application-logs collect-infrastructure-logs collect-audit-logs \
  cluster-logging-write-application-logs cluster-logging-write-infrastructure-logs \
  cluster-logging-write-audit-logs
```

Remove the CRDs if you want a complete cleanup:

```bash
oc get crd -o name | grep -E 'logging\.openshift\.io|loki\.grafana\.com' | xargs oc delete
```

**Warning**: Deleting CRDs removes all custom resources of those types across the entire cluster.

---

## Operator Capabilities

The Cluster Logging Operator provides the following platform capabilities:

- **Seamless upgrades**: OLM manages the full lifecycle of the operator, including automated upgrades within a channel. No manual migration steps are required for minor version updates.
- **Disconnected environment support**: The operator and its components can be deployed in air-gapped or restricted network environments using mirrored registries.
- **FIPS compliance**: The operator supports running on FIPS-enabled OpenShift clusters. Cryptographic modules used by the collector comply with FIPS 140-2 requirements.
- **Proxy-aware**: The operator and collector pods honor cluster-wide proxy settings. HTTP_PROXY, HTTPS_PROXY, and NO_PROXY environment variables are automatically injected when a cluster proxy is configured.
- **TLS security profiles**: The operator supports configurable TLS security profiles for connections between the collector and log outputs. Available profiles:
  - `Old` -- Broadest compatibility, supports TLS 1.0+.
  - `Intermediate` -- Balanced security and compatibility, supports TLS 1.2+ (default).
  - `Modern` -- Strictest security, supports TLS 1.3 only.
  - `Custom` -- User-defined ciphers and minimum TLS version.

Configure the TLS profile in the ClusterLogForwarder output spec:

```yaml
spec:
  outputs:
  - name: example-output
    type: syslog
    tls:
      securityProfile:
        type: Intermediate
```
