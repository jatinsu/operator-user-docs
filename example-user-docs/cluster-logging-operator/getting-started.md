# Getting Started with the Cluster Logging Operator

This guide walks through installing the Cluster Logging Operator on OpenShift Container Platform and configuring log collection and forwarding.

## Prerequisites

- OpenShift Container Platform 4.14 or later
- Cluster administrator access (`cluster-admin` role)
- If using LokiStack as the log store: the Loki Operator must be installed and object storage (S3, Azure Blob Storage, Google Cloud Storage, or OpenStack Swift) must be configured
- The `oc` CLI installed and authenticated to your cluster

## Step 1: Create the openshift-logging Namespace

Create the namespace where the Cluster Logging Operator and its components will run.

Save the following to a file named `namespace.yaml`:

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

Apply it:

```bash
oc apply -f namespace.yaml
```

## Step 2: Install the Operator

You can install the Cluster Logging Operator through the OpenShift web console or the CLI.

### Option A: Web Console

1. Navigate to **Operators** > **OperatorHub** in the OpenShift web console.
2. Search for **Cluster Logging**.
3. Select the **Cluster Logging** operator provided by Red Hat.
4. Click **Install**.
5. Set the installation namespace to `openshift-logging`.
6. Select the latest available **stable** update channel (e.g., `stable-6.5`). Verify available channels by checking OperatorHub or running `oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'`.
7. Click **Install** and wait for the operator to reach the `Succeeded` phase.

### Option B: CLI

Create the OperatorGroup and Subscription resources.

Save the following to `operatorgroup.yaml`:

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

Save the following to `subscription.yaml`:

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

Apply both:

```bash
oc apply -f operatorgroup.yaml
oc apply -f subscription.yaml
```

Wait for the operator CSV to reach the `Succeeded` phase:

```bash
oc get csv -n openshift-logging
```

## Step 3: Create a Service Account

Create a service account that the log collector will use:

```bash
oc create serviceaccount collector -n openshift-logging
```

## Step 4: Grant Log Collection Permissions

Bind the required cluster roles to the collector service account. Each role controls access to a different category of logs:

```bash
oc adm policy add-cluster-role-to-user collect-application-logs system:serviceaccount:openshift-logging:collector
oc adm policy add-cluster-role-to-user collect-infrastructure-logs system:serviceaccount:openshift-logging:collector
oc adm policy add-cluster-role-to-user collect-audit-logs system:serviceaccount:openshift-logging:collector
```

## Step 5: Create a ClusterLogForwarder

The `ClusterLogForwarder` resource defines where logs are collected from and where they are sent. The following example forwards application and infrastructure logs to an external Elasticsearch instance.

Save the following to `clusterlogforwarder.yaml`:

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
  - name: my-elasticsearch
    type: elasticsearch
    elasticsearch:
      url: https://elasticsearch.example.com:9200
      version: 8
      index: '{.log_type||"application"}'
    tls:
      insecureSkipVerify: true
  pipelines:
  - name: all-logs
    inputRefs:
    - application
    - infrastructure
    outputRefs:
    - my-elasticsearch
```

Apply it:

```bash
oc apply -f clusterlogforwarder.yaml
```

Replace `https://elasticsearch.example.com:9200` with the URL of your Elasticsearch instance. For production deployments, configure proper TLS certificates instead of using `insecureSkipVerify`.

## Step 6: Verify the Deployment

Check that the collector pods are running:

```bash
oc get pods -n openshift-logging
```

You should see collector pods in a `Running` state on each node.

Inspect the ClusterLogForwarder status:

```bash
oc get clusterlogforwarder instance -n openshift-logging -o yaml
```

Look for the `status.conditions` section and confirm that the `Ready` condition is set to `True`. If it is not, the `message` field will describe what needs to be resolved.

## Quickstart with LokiStack

To use LokiStack as the log store instead of an external output, follow these high-level steps:

1. **Install the Loki Operator.** Install it from OperatorHub into the `openshift-operators-redhat` namespace.

2. **Create an object storage secret.** Create a secret in the `openshift-logging` namespace containing credentials for your object storage backend (S3, Azure Blob Storage, GCS, or Swift).

3. **Create a LokiStack CR.** Deploy a LokiStack instance in the `openshift-logging` namespace, referencing the storage secret. Choose a size appropriate for your cluster (`1x.demo` for testing, `1x.small` or larger for production).

4. **Grant write permissions to the collector service account.** Bind the `logging-collector-logs-writer` cluster role:

   ```bash
   oc adm policy add-cluster-role-to-user logging-collector-logs-writer system:serviceaccount:openshift-logging:collector
   ```

5. **Create a ClusterLogForwarder with a lokiStack output.** Set the output type to `lokiStack` and reference your LokiStack instance:

   ```yaml
   outputs:
   - name: loki
     type: lokiStack
     lokiStack:
       target:
         name: logging-loki
         namespace: openshift-logging
   ```

For detailed LokiStack deployment instructions, see [deployment.md](deployment.md). For the full list of ClusterLogForwarder options, see [configuration-reference.md](configuration-reference.md).
