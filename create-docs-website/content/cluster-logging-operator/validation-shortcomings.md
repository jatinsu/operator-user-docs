# Documentation Validation Shortcomings

**Validated against**: https://api.aur2w-2f3uo-e85.4f01.p3.openshiftapps.com:443 (version 4.21.14)
**Date**: 2026-07-01
**Feature gates**: Default (null)
**Docs directory**: /home/jsuri/random-testing/user-facing-docs/operator-user-docs/test/cluster-logging-operator/user-docs
**Source directory**: /home/jsuri/random-testing/user-facing-docs/operator-user-docs/test/cluster-logging-operator

---

## CRITICAL -- Blocks user from following documentation

### 1. Subscription channel `stable-6.6` does not exist for Cluster Logging Operator

**Files affected**: getting-started.md (lines 49, 78), deployment.md (lines 47, 79)

**Problem**: Both documents instruct users to subscribe to the `stable-6.6` channel for the Cluster Logging Operator. This channel does not exist in the operator catalog on this cluster. The available channels are `stable-6.4` and `stable-6.5`. A user creating a Subscription with `channel: stable-6.6` will see the Subscription remain in a pending state indefinitely and the operator will never install.

**Reproduction**:
```
$ export KUBECONFIG=/home/jsuri/random-testing/user-facing-docs/operator-user-docs/test/kubeconfig
$ oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'
stable-6.4 stable-6.5
```

**Fix needed**: Update the documented channel to the latest available channel (`stable-6.5`), or add a note instructing users to verify available channels with `oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'` and use the latest stable channel.

---

### 2. Subscription channel `stable-6.6` does not exist for Loki Operator

**Files affected**: deployment.md (lines 177-178, 188)

**Problem**: The deployment guide instructs users to install the Loki Operator from the `stable-6.6` channel. The only available channel for the Loki Operator on this cluster is `alpha`. A user following the docs will create a Subscription that never resolves.

**Reproduction**:
```
$ export KUBECONFIG=/home/jsuri/random-testing/user-facing-docs/operator-user-docs/test/kubeconfig
$ oc get packagemanifest loki-operator -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'
alpha
```

**Fix needed**: Update the Loki Operator channel reference to the correct available channel, or add a prerequisite step to check available channels.

---

### 3. All 6 example YAMLs fail server-side dry-run (CRD not registered)

**Files affected**: examples/cloudwatch-sts.yaml, examples/kafka-sasl.yaml, examples/lokistack-basic.yaml, examples/multi-output-filtered.yaml, examples/splunk-hec.yaml, examples/syslog-rfc5424.yaml

**Problem**: All example YAML files fail `oc apply --dry-run=server` because the ClusterLogForwarder CRD (`observability.openshift.io/v1`) is not registered on the cluster. While this is expected when the operator is not installed, there is no README or note in the examples directory explaining that the Cluster Logging Operator must be installed first. A user browsing the examples directory would encounter confusing errors without context.

**Reproduction**:
```
$ export KUBECONFIG=/home/jsuri/random-testing/user-facing-docs/operator-user-docs/test/kubeconfig
$ oc apply --dry-run=server -f user-docs/examples/lokistack-basic.yaml
error: resource mapping not found for name: "instance" namespace: "openshift-logging" from "user-docs/examples/lokistack-basic.yaml": no matches for kind "ClusterLogForwarder" in version "observability.openshift.io/v1"
ensure CRDs are installed first
```

**Fix needed**: Add a README.md to the examples/ directory noting that the Cluster Logging Operator must be installed before applying these examples, and link back to the getting-started guide.

---

## SIGNIFICANT -- Incorrect information

### 4. `openshift.io/node-selector` placed under labels instead of annotations in getting-started.md

**Files affected**: getting-started.md (line 29)

**Problem**: The namespace YAML in getting-started.md places `openshift.io/node-selector: ""` under `metadata.labels`. In OpenShift, `openshift.io/node-selector` is a namespace **annotation**, not a label. Placing it as a label has no effect — the cluster default node selector will still apply to pods in the namespace, which could prevent collector pods from scheduling on all nodes. The deployment.md file correctly places it under `metadata.annotations`.

**Reproduction**:
```yaml
# getting-started.md (INCORRECT - line 29):
metadata:
  labels:
    openshift.io/node-selector: ""

# deployment.md (CORRECT - line 30):
metadata:
  annotations:
    openshift.io/node-selector: ""
```

**Fix needed**: Move `openshift.io/node-selector: ""` from `labels` to `annotations` in getting-started.md's namespace YAML.

---

### 5. Collector pod label selector `component=collector` is incorrect in deployment.md

**Files affected**: deployment.md (line 303)

**Problem**: The deployment guide uses `oc get pods -n openshift-logging -l component=collector` to check collector pods. The actual label set by the operator on collector pods is `app.kubernetes.io/component=collector` (using Kubernetes recommended common labels, per `internal/runtime/runtime.go:118`). The short label `component=collector` will return no results even when collector pods are running. The troubleshooting.md file correctly uses `app.kubernetes.io/component=collector`.

**Reproduction**:
Source code reference (`internal/constants/labels.go:10`):
```go
LabelK8sComponent = "app.kubernetes.io/component"
```

Source code reference (`internal/runtime/runtime.go:118`):
```go
constants.LabelK8sComponent: component,  // sets app.kubernetes.io/component=collector
```

**Fix needed**: Change `component=collector` to `app.kubernetes.io/component=collector` in deployment.md line 303.

---

### 6. Loki Operator installation namespace text contradicts YAML

**Files affected**: deployment.md (line 177)

**Problem**: The prose text says "Install the Loki Operator from OperatorHub into the `openshift-logging` namespace" but the Subscription YAML immediately below (line 184) correctly specifies `namespace: openshift-operators-redhat`. The Loki Operator should be installed in `openshift-operators-redhat`, not `openshift-logging`. A user following the text instead of the YAML would install the Loki Operator in the wrong namespace.

**Reproduction**:
```
deployment.md line 177:
"Install the Loki Operator from OperatorHub into the `openshift-logging` namespace using the `stable-6.6` channel"

deployment.md line 184:
  namespace: openshift-operators-redhat
```

**Fix needed**: Change the prose to say "Install the Loki Operator from OperatorHub into the `openshift-operators-redhat` namespace".

---

### 7. Troubleshooting ConfigMap name `collector-config` assumes specific CLF name

**Files affected**: troubleshooting.md (line 184)

**Problem**: The troubleshooting command `oc get configmap -n openshift-logging collector-config` hardcodes the ConfigMap name as `collector-config`. Per the source code (`internal/factory/resource_names.go:40`), the ConfigMap name is `<clf-name>-config`. If the user named their ClusterLogForwarder `instance` (as shown in getting-started.md and all example YAMLs), the ConfigMap would be `instance-config`, not `collector-config`. Only if the CLF is named `collector` (as in deployment.md's LokiStack section) would this command work.

**Reproduction**:
Source code reference (`internal/factory/resource_names.go:40`):
```go
ConfigMap: resBaseName + "-config",  // resBaseName = clf.Name
```

**Fix needed**: Replace the hardcoded ConfigMap name with a note explaining that the name depends on the CLF name, e.g., `oc get configmap -n openshift-logging <clf-name>-config`, or use a label-based lookup: `oc get configmap -n openshift-logging -l app.kubernetes.io/component=collector`.

---

### 8. CLF name inconsistency between deployment.md and other docs/examples

**Files affected**: deployment.md (line 265)

**Problem**: The LokiStack CLF example in deployment.md uses `name: collector`, while getting-started.md (line 125) and all six example YAML files use `name: instance`. This inconsistency means troubleshooting commands that reference a specific CLF name (e.g., `oc get clusterlogforwarder instance`) or the derived ConfigMap name will not work consistently for users who followed deployment.md. The troubleshooting.md commands reference `instance` as the CLF name.

**Reproduction**:
```
deployment.md line 265: name: collector
getting-started.md line 125: name: instance
troubleshooting.md line 13: oc get clusterlogforwarder instance
All examples/*.yaml: name: instance
```

**Fix needed**: Standardize on one CLF name across all docs. Either change deployment.md to use `name: instance` or update troubleshooting commands to note the name is user-chosen.

---

## MINOR -- Cosmetic or edge-case issues

### 9. OperatorGroup name differs between getting-started.md and deployment.md

**Files affected**: getting-started.md (line 63), deployment.md (line 65)

**Problem**: getting-started.md names the OperatorGroup `cluster-logging` while deployment.md names it `openshift-logging`. Both would work, but the inconsistency between the two guides could confuse users who reference both documents.

**Reproduction**:
```
getting-started.md line 63: name: cluster-logging
deployment.md line 65: name: openshift-logging
```

**Fix needed**: Standardize on one OperatorGroup name across both files.

---

### 10. No README.md in examples/ directory

**Files affected**: examples/ directory

**Problem**: The examples directory contains 6 YAML files but no README explaining what each example demonstrates, what prerequisites are required, or how to use them. Users browsing the examples directory lack context about which example to use for their use case.

**Fix needed**: Add a brief README.md to the examples/ directory listing each example with a one-line description and a note about prerequisites.

---

### 11. deployment.md Subscription includes `installPlanApproval` while getting-started.md omits it

**Files affected**: getting-started.md (lines 71-82), deployment.md (lines 75-85)

**Problem**: The deployment.md Subscription YAML includes `installPlanApproval: Automatic` (line 84) while getting-started.md omits this field entirely. While `Automatic` is the default and both are functionally equivalent, the inconsistency could confuse users comparing the two documents.

**Fix needed**: Either add `installPlanApproval: Automatic` to getting-started.md for consistency, or remove it from deployment.md since it's the default.

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 3 | Channel `stable-6.6` doesn't exist for CLO or Loki Operator; example YAMLs fail without prerequisite context |
| SIGNIFICANT | 5 | Incorrect namespace YAML, wrong pod label selector, namespace text/YAML mismatch, wrong ConfigMap name, inconsistent CLF naming |
| MINOR | 3 | OperatorGroup name inconsistency, missing examples README, Subscription field inconsistency |
| **Total** | **11** | |

### Commands used for validation

```bash
# Cluster baseline
export KUBECONFIG=/home/jsuri/random-testing/user-facing-docs/operator-user-docs/test/kubeconfig
oc whoami
oc version
oc get clusterversion version -o jsonpath='{.status.desired.version}'
oc get featuregate cluster -o json | jq '.spec.featureSet'

# Namespace validation
oc get namespace openshift-logging -o json | jq '{labels: .metadata.labels, annotations: .metadata.annotations}'

# Operator status
oc get pods -n openshift-logging -l name=cluster-logging-operator
oc get csv -n openshift-logging -o custom-columns=NAME:.metadata.name,VERSION:.spec.version,PHASE:.status.phase
oc get subscription cluster-logging -n openshift-logging -o yaml
oc logs -n openshift-logging deployment/cluster-logging-operator

# CRD validation
oc get crd clusterlogforwarders.observability.openshift.io -o jsonpath='{.spec.group}/{.spec.versions[*].name}'
oc get crd logfilemetricexporters.logging.openshift.io -o jsonpath='{.spec.group}/{.spec.versions[*].name}'
oc api-resources --api-group=observability.openshift.io
oc api-resources --api-group=logging.openshift.io

# RBAC validation
oc get clusterrole collect-application-logs collect-infrastructure-logs collect-audit-logs
oc get clusterrole cluster-logging-write-application-logs cluster-logging-write-infrastructure-logs cluster-logging-write-audit-logs
oc get clusterrole logging-collector-logs-writer

# Collector validation
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector
oc get pods -n openshift-logging -l component=collector
oc get daemonset -n openshift-logging -l app.kubernetes.io/component=collector
oc get configmap -n openshift-logging collector-config
oc get configmap -n openshift-logging -l app.kubernetes.io/component=collector

# Resource listing
oc get all -n openshift-logging
oc get clusterlogforwarder -n openshift-logging
oc get events -n openshift-logging --sort-by='.lastTimestamp'

# Channel validation
oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'
oc get packagemanifest loki-operator -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'

# Storage validation
oc get storageclass gp3-csi
oc get storageclass

# Namespace validation
oc get namespace openshift-operators-redhat

# Example YAML dry-run
oc apply --dry-run=server -f user-docs/examples/cloudwatch-sts.yaml
oc apply --dry-run=server -f user-docs/examples/kafka-sasl.yaml
oc apply --dry-run=server -f user-docs/examples/lokistack-basic.yaml
oc apply --dry-run=server -f user-docs/examples/multi-output-filtered.yaml
oc apply --dry-run=server -f user-docs/examples/splunk-hec.yaml
oc apply --dry-run=server -f user-docs/examples/syslog-rfc5424.yaml

# Source code cross-reference
grep -rn 'LabelK8sComponent' internal/constants/labels.go
grep -rn 'CollectorConfigSecretName' internal/constants/constants.go
cat internal/factory/resource_names.go
cat internal/runtime/runtime.go (lines 110-134)
cat internal/collector/config.go
```
