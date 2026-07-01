# Getting Started with the Cluster Logging Operator

This guide walks you through installing the Cluster Logging Operator (CLO) on OpenShift and configuring it to collect and forward cluster logs. By the end, you will have a working log collection pipeline that gathers application and infrastructure logs and forwards them to a LokiStack log store.

The CLO deploys and manages a log collector (based on Vector) as a DaemonSet on every node in your cluster. You configure what to collect and where to send it by creating a `ClusterLogForwarder` custom resource.

---

## Prerequisites

Before you begin, make sure you have the following:

- **OpenShift Container Platform v4.20 or later** (minimum Kubernetes 1.18.3)
- **Cluster administrator access** (you will need to create namespaces, ClusterRoleBindings, and install operators)
- **Supported CPU architectures:** amd64, arm64, ppc64le, s390x
- **Supported subscriptions:** OpenShift Kubernetes Engine, OpenShift Container Platform, or OpenShift Platform Plus
- The `oc` CLI installed and authenticated to your cluster

Verify your cluster version:

```bash
oc version
```

---

## Step 1: Prepare the Namespace

The CLO expects to run in the `openshift-logging` namespace. Create it and apply the required labels and annotations:

```bash
oc create namespace openshift-logging
```

Enable cluster monitoring for the namespace:

```bash
oc label ns/openshift-logging openshift.io/cluster-monitoring=true --overwrite
```

Configure pod security admission to allow privileged workloads (the collector requires host-level access to read log files):

```bash
oc label ns/openshift-logging pod-security.kubernetes.io/enforce=privileged --overwrite
oc label ns/openshift-logging pod-security.kubernetes.io/audit=privileged --overwrite
oc label ns/openshift-logging pod-security.kubernetes.io/warn=privileged --overwrite
```

Disable automatic security context constraint (SCC) label synchronization so the labels you just set are not overwritten:

```bash
oc label ns/openshift-logging security.openshift.io/scc.podSecurityLabelSync=false --overwrite
```

Allow collector pods to be scheduled on any node (including control plane nodes):

```bash
oc annotate ns/openshift-logging openshift.io/node-selector="" --overwrite
```

---

## Step 2: Install the Operator

Install the Cluster Logging Operator through OperatorHub:

1. In the OpenShift web console, navigate to **Operators > OperatorHub**.
2. Search for **"Red Hat OpenShift Logging"**.
3. Select the **Red Hat** version of the operator (not the community version).
4. Click **Install**.
5. On the install form:
   - Set **Update channel** to `stable-6.5`.
   - Set **Installation mode** to **A specific namespace on the cluster**.
   - Set **Installed Namespace** to `openshift-logging`.
   - Leave **Approval strategy** as `Automatic` (or choose `Manual` if you want to approve updates yourself).
6. Click **Install** and wait for the operator to reach the `Succeeded` phase.

OLM (Operator Lifecycle Manager) handles the operator deployment, RBAC, and CRD installation automatically.

Verify the operator is running:

```bash
oc get deployment cluster-logging-operator -n openshift-logging
```

You should see `READY 1/1` and `AVAILABLE 1`.

---

## Step 3: Create a ServiceAccount for the Collector

The collector runs under a dedicated ServiceAccount that you create and manage. This ServiceAccount must be granted ClusterRoles that permit it to collect each category of logs you need.

Create the ServiceAccount:

```bash
oc create serviceaccount logcollector -n openshift-logging
```

Bind the required ClusterRoles. The CLO ships three ClusterRoles for log collection permissions:

| ClusterRole | What it permits |
|---|---|
| `collect-application-logs` | Reading logs from application workload pods |
| `collect-infrastructure-logs` | Reading logs from `openshift-*` and `kube-*` namespaces and some node-level logs |
| `collect-audit-logs` | Reading node-level security audit logs |

Bind all three roles to collect every log type:

```bash
oc adm policy add-cluster-role-to-user collect-application-logs system:serviceaccount:openshift-logging:logcollector
oc adm policy add-cluster-role-to-user collect-infrastructure-logs system:serviceaccount:openshift-logging:logcollector
oc adm policy add-cluster-role-to-user collect-audit-logs system:serviceaccount:openshift-logging:logcollector
```

If you only need a subset of log types, bind only the corresponding roles. The operator validates that the ServiceAccount has the required permissions for the inputs referenced in your `ClusterLogForwarder` and will report a condition error if permissions are missing.

---

## Step 4: Set Up a Log Store (Optional but Recommended)

While the CLO can forward logs to many destinations (Elasticsearch, Splunk, CloudWatch, Kafka, and others), LokiStack is the recommended on-cluster log store for OpenShift. This step sets up LokiStack. Skip to [Step 5](#step-5-create-a-clusterlogforwarder) if you are forwarding to an external system.

### 4a. Install the Loki Operator

1. In the OpenShift web console, navigate to **Operators > OperatorHub**.
2. Search for **"Loki Operator"** and install the **Red Hat** version.
3. Install it in the `openshift-operators-redhat` namespace (or `All namespaces`).

### 4b. Create Object Storage Credentials

LokiStack requires object storage (such as AWS S3, Google Cloud Storage, Azure Blob, or OpenShift Data Foundation). Create a Secret with your storage credentials. The following example uses AWS S3:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: logging-loki-s3
  namespace: openshift-logging
stringData:
  access_key_id: "<your-access-key-id>"
  access_key_secret: "<your-secret-access-key>"
  bucketnames: "<your-bucket-name>"
  endpoint: "https://s3.<region>.amazonaws.com"
  region: "<region>"
```

Apply the Secret:

```bash
oc apply -f loki-s3-secret.yaml
```

### 4c. Create a LokiStack Instance

Create a `LokiStack` custom resource. The following example creates a minimal deployment suitable for development and testing:

```yaml
apiVersion: loki.grafana.com/v1
kind: LokiStack
metadata:
  name: logging-loki
  namespace: openshift-logging
spec:
  size: 1x.extra-small
  storage:
    schemas:
      - effectiveDate: "2024-10-01"
        version: v13
    secret:
      name: logging-loki-s3
      type: s3
  storageClassName: gp3-csi
  tenants:
    mode: openshift-logging
```

Apply the LokiStack:

```bash
oc apply -f lokistack.yaml
```

Wait for all LokiStack components to become ready:

```bash
oc get lokistack logging-loki -n openshift-logging
```

---

## Step 5: Create a ClusterLogForwarder

The `ClusterLogForwarder` is the central configuration resource. It defines:

- **`serviceAccount`** -- the ServiceAccount the collector pods run under (required).
- **`outputs`** -- named destinations where logs are sent.
- **`pipelines`** -- routes that connect inputs (log sources) to outputs.
- **`filters`** (optional) -- transformations applied to log records in a pipeline.

Three built-in inputs are always available without any extra configuration:
- `application` -- logs from application workload pods.
- `infrastructure` -- logs from `openshift-*` and `kube-*` system pods and some node logs.
- `audit` -- node-level security audit logs.

### Minimal Example: Forward to LokiStack

The following `ClusterLogForwarder` collects application and infrastructure logs and forwards them to the LokiStack you created in Step 4:

```yaml
apiVersion: observability.openshift.io/v1
kind: ClusterLogForwarder
metadata:
  name: collector
  namespace: openshift-logging
spec:
  serviceAccount:
    name: logcollector
  outputs:
    - name: lokistack-out
      type: lokiStack
      lokiStack:
        authentication:
          token:
            from: serviceAccount
        target:
          name: logging-loki
          namespace: openshift-logging
  pipelines:
    - name: app-logs
      inputRefs:
        - application
        - infrastructure
      outputRefs:
        - lokistack-out
```

Apply the `ClusterLogForwarder`:

```bash
oc apply -f clusterlogforwarder.yaml
```

### Adding a Filter

You can add filters to transform or drop log records. Filters are defined in the top-level `filters` array and referenced by name in a pipeline's `filterRefs` list. Filters are applied in the order they are listed.

The following example adds a `drop` filter that discards debug-level log messages:

```yaml
apiVersion: observability.openshift.io/v1
kind: ClusterLogForwarder
metadata:
  name: collector
  namespace: openshift-logging
spec:
  serviceAccount:
    name: logcollector
  filters:
    - name: drop-debug
      type: drop
      drop:
        - test:
            - field: .level
              matches: "debug"
  outputs:
    - name: lokistack-out
      type: lokiStack
      lokiStack:
        authentication:
          token:
            from: serviceAccount
        target:
          name: logging-loki
          namespace: openshift-logging
  pipelines:
    - name: app-logs
      inputRefs:
        - application
        - infrastructure
      outputRefs:
        - lokistack-out
      filterRefs:
        - drop-debug
```

Available filter types:

| Filter Type | Purpose |
|---|---|
| `detectMultilineException` | Reassembles multi-line exception stack traces into a single log entry |
| `drop` | Drops log records matching regex conditions |
| `kubeAPIAudit` | Filters Kubernetes API audit events by level to reduce volume |
| `openshiftLabels` | Adds custom labels to the `openshift.labels` map on log records |
| `parse` | Parses unstructured log messages into structured fields |
| `prune` | Removes specific fields from log records to reduce size |

---

## Step 6: Verify the Installation

Run the following commands to confirm everything is working.

Check the operator deployment:

```bash
oc get deployment cluster-logging-operator -n openshift-logging
```

List all `ClusterLogForwarder` resources:

```bash
oc get clusterlogforwarder -n openshift-logging
```

Check that collector pods are running (one per node):

```bash
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector
```

Inspect the detailed status conditions on the `ClusterLogForwarder` to confirm all inputs, outputs, filters, and pipelines are valid:

```bash
oc get clusterlogforwarder collector -n openshift-logging -o yaml
```

Look at the `.status.conditions` section. A healthy forwarder shows conditions with `status: "True"` and `reason: ValidationSuccess` (or similar). If there are problems, the conditions will describe what is wrong -- for example, a missing RBAC binding or an unreachable output endpoint.

You can also check the collector pod logs for errors:

```bash
oc logs -n openshift-logging -l app.kubernetes.io/component=collector --tail=50
```

---

## What's Next

- [Configuration Reference](configuration-reference.md) for all available `ClusterLogForwarder` options including collector tuning, delivery modes, and TLS settings
- [API Reference](api-reference.md) for complete CRD field documentation covering every field in the `observability.openshift.io/v1` API
- [Examples](examples/) for common configurations such as forwarding to Splunk, CloudWatch, Kafka, Elasticsearch, and external Loki
- [Troubleshooting](troubleshooting.md) if you run into issues with collector pods, log delivery, or status conditions
