# Deployment Guide

## Overview

The Cluster Logging Operator (CLO) is deployed via the Operator Lifecycle Manager (OLM) on OpenShift. It manages Vector-based log collectors as DaemonSets and Deployments.

## Prerequisites

| Requirement | Details |
|-------------|---------|
| OpenShift Version | 4.20 - 4.23 |
| Minimum Kubernetes | 1.18.3 |
| Architectures | amd64, arm64, ppc64le, s390x |
| Namespace | openshift-logging |
| Privileges | Cluster administrator |
| Subscriptions | OpenShift Kubernetes Engine, OCP, or Platform Plus |

## Installation

### Step 1: Prepare the Namespace

```bash
oc create namespace openshift-logging
oc label ns/openshift-logging openshift.io/cluster-monitoring=true --overwrite
oc label ns/openshift-logging pod-security.kubernetes.io/enforce=privileged --overwrite
oc label ns/openshift-logging pod-security.kubernetes.io/audit=privileged --overwrite
oc label ns/openshift-logging pod-security.kubernetes.io/warn=privileged --overwrite
oc label ns/openshift-logging security.openshift.io/scc.podSecurityLabelSync=false --overwrite
oc annotate ns/openshift-logging openshift.io/node-selector="" --overwrite
```

Why each label matters:
- `cluster-monitoring=true` -- Enables Prometheus to scrape metrics from this namespace
- Pod security labels -- Required because collector pods need privileged access to read host logs
- `scc.podSecurityLabelSync=false` -- Prevents automatic SCC label overwriting

### Step 2: Install via OperatorHub

1. In the OpenShift web console, go to Operators > OperatorHub
2. Search for "Red Hat OpenShift Logging"
3. Select the operator and click Install
4. Configure:
   - Update channel: `stable-6.5`
   - Installation mode: A specific namespace on the cluster
   - Installed Namespace: `openshift-logging`
   - Update approval: Automatic (recommended) or Manual
5. Click Install

### Step 3: Verify Installation

```bash
oc get csv -n openshift-logging
oc get deployment cluster-logging-operator -n openshift-logging
oc wait --for=condition=available --timeout=5m deployment/cluster-logging-operator -n openshift-logging
```

## What Gets Deployed

The operator creates and manages:

| Resource | Type | Purpose |
|----------|------|---------|
| cluster-logging-operator | Deployment | The operator itself (1 replica) |
| Vector collector | DaemonSet | Collects node/container logs (one pod per node) |
| Vector receiver | Deployment | HTTP/Syslog receivers (2 replicas, only if receiver inputs configured) |
| ConfigMaps | ConfigMap | Vector configuration (TOML), trusted CA bundles |
| Secrets | Secret | Authentication credentials, TLS certificates |
| ClusterRoles | ClusterRole | RBAC for log collection (collect-application-logs, collect-infrastructure-logs, collect-audit-logs) |
| ClusterRoleBindings | ClusterRoleBinding | Binds roles to collector ServiceAccount |
| NetworkPolicies | NetworkPolicy | Optional network isolation for collector pods |
| ServiceMonitors | ServiceMonitor | Prometheus metrics scraping configuration |
| PrometheusRules | PrometheusRule | Alert definitions |

## Operator Configuration

**Environment Variables** (set in operator deployment):

| Variable | Description |
|----------|-------------|
| RELATED_IMAGE_VECTOR | Vector collector image |
| RELATED_IMAGE_LOG_FILE_METRIC_EXPORTER | Log file metric exporter image |
| WATCH_NAMESPACE | Namespace to watch (set by OLM) |

**Annotations** on ClusterLogForwarder:

| Annotation | Description | Values |
|------------|-------------|--------|
| observability.openshift.io/log-level | Vector log verbosity | trace, debug, info, warn, error, off |
| observability.openshift.io/max-unavailable | Max unavailable during rollout | Number or percentage |

## Upgrading

**Automatic Upgrades (via OLM):**
- If update approval is set to Automatic, OLM upgrades the operator when new versions appear in the channel
- Supported upgrade path: any version >= 6.2.0 to 6.5.1
- The operator handles rolling updates of collector pods

**Manual Upgrades:**
1. In the OpenShift web console, go to Operators > Installed Operators
2. Select Cluster Logging
3. Click Upgrade (if available)

**Upgrade Considerations:**
- Review release notes for breaking changes
- Collector pods are rolling-updated (controlled by maxUnavailable)
- Log forwarding continues during upgrade with minimal disruption
- Monitor collector pod status during upgrade

## Uninstalling

### Step 1: Remove ClusterLogForwarder Resources

```bash
oc delete clusterlogforwarder --all -n openshift-logging
```

### Step 2: Remove LogFileMetricExporter (if installed)

```bash
oc delete logfilemetricexporter --all -n openshift-logging
```

### Step 3: Uninstall the Operator

1. In the OpenShift web console, go to Operators > Installed Operators
2. Select Cluster Logging
3. Click Actions > Uninstall Operator

Or via CLI:

```bash
oc delete subscription cluster-logging -n openshift-logging
oc delete csv -n openshift-logging -l operators.coreos.com/cluster-logging.openshift-logging
```

### Step 4: Clean Up Cluster-Scoped Resources

```bash
# Remove ClusterRoles and ClusterRoleBindings
oc delete clusterrole collect-application-logs collect-infrastructure-logs collect-audit-logs
oc delete clusterrolebinding collect-application-logs collect-infrastructure-logs collect-audit-logs

# Remove CRDs (optional -- only if no other logging operator version will be installed)
oc delete crd clusterlogforwarders.observability.openshift.io
oc delete crd logfilemetricexporters.logging.openshift.io
```

### Step 5: Remove the Namespace (optional)

```bash
oc delete namespace openshift-logging
```

## Management State

The ClusterLogForwarder supports a `managementState` field:
- **Managed** (default): Operator actively reconciles the resource, deploys and updates collectors
- **Unmanaged**: Operator stops managing the resource. Use for manual configuration changes or troubleshooting. The operator will not overwrite your changes, but also will not fix issues automatically.

```yaml
spec:
  managementState: Unmanaged
```

Warning: Unmanaged state is not supported by Red Hat. Use only for debugging and return to Managed state as soon as possible.

## Collector Resource Sizing

Recommendations based on cluster size and log volume:

| Cluster Size | Log Volume | CPU Request | Memory Request |
|-------------|------------|-------------|----------------|
| Small (< 10 nodes) | Low | 200m | 256Mi |
| Medium (10-50 nodes) | Medium | 500m | 512Mi |
| Large (50+ nodes) | High | 1000m | 1Gi |

Configure in CollectorSpec:

```yaml
spec:
  collector:
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: "1"
        memory: 1Gi
```

## High Availability

- The operator itself runs as a single replica
- Collector DaemonSet runs one pod per node (inherently distributed)
- Receiver Deployments run 2 replicas for HA
- Use tolerations and affinity rules for scheduling control

## Disconnected/Air-Gapped Clusters

The operator supports disconnected environments:
- All container images must be mirrored to a local registry
- Set `RELATED_IMAGE_*` environment variables to point to mirrored images
- No external network access required for log collection
- Output destinations must be reachable from the cluster network
