# Documentation Validation Shortcomings

**Validated against**: https://api.fmffz-83h23-m2c.fd8q.p3.openshiftapps.com:443 (version 4.21.14)
**Date**: 2026-06-29
**Feature gates**: null (no custom feature gates configured)
**Docs directory**: /home/jsuri/random-testing/user-facing-docs/cluster-logging-operator/user-docs
**Kubernetes version**: v1.34.6
**Operator installed**: No — the Cluster Logging Operator is NOT installed on this cluster. The `openshift-logging` namespace exists but contains no operator deployment, no CRDs, no ClusterRoles, and no collector pods.

---

## CRITICAL — Blocks user from following documentation

### 1. Operator channel `stable-6.6` does not exist — installation will fail

**Files affected**:
- `getting-started.md`: line 73
- `deployment.md`: line 43

**Problem**: The docs instruct users to install the operator from the `stable-6.6` channel, but this channel does not exist on the cluster. The only available channels are `stable-6.4` (CSV: `cluster-logging.v6.4.5`) and `stable-6.5` (CSV: `cluster-logging.v6.5.1`). A user following the getting-started guide step-by-step will fail at the installation step because the specified channel cannot be found in OperatorHub.

**Reproduction**:
```
$ oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'
stable-6.4 stable-6.5

$ oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.defaultChannel}'
stable-6.5
```

**Fix needed**: Change the channel reference from `stable-6.6` to `stable-6.5` (or to "the latest available `stable-*` channel"), and update the version references accordingly.

---

### 2. Documented version "6.6.0" does not exist — misleading version throughout docs

**Files affected**:
- `README.md`: line 7 (`Current version: **6.6.0**`)
- `deployment.md`: line 95 (`any version >= 6.2.0 to 6.6.0`)
- `deployment.md`: line 133 (`oc delete csv cluster-logging.v6.6.0`)

**Problem**: The docs state the current version is 6.6.0, but the latest available version on this cluster is 6.5.1. The uninstall command `oc delete csv cluster-logging.v6.6.0` will fail with "not found" because that CSV version does not exist. The upgrade path claim "6.2.0 to 6.6.0" is also inaccurate.

**Reproduction**:
```
$ oc get packagemanifest cluster-logging -n openshift-marketplace -o json | jq '[.status.channels[] | {name: .name, currentCSV: .currentCSV}]'
[
  { "name": "stable-6.4", "currentCSV": "cluster-logging.v6.4.5" },
  { "name": "stable-6.5", "currentCSV": "cluster-logging.v6.5.1" }
]

$ oc delete csv cluster-logging.v6.6.0 -n openshift-logging
Error from server (NotFound): ...
```

**Fix needed**: Update all version references from `6.6.0` to `6.5.1` (or make version references dynamic with a note to check the installed version).

---

### 3. All 7 example YAML files fail server-side dry-run

**Files affected**:
- `examples/lokistack-basic.yaml`
- `examples/elasticsearch.yaml`
- `examples/splunk.yaml`
- `examples/cloudwatch.yaml`
- `examples/kafka.yaml`
- `examples/syslog.yaml`
- `examples/multi-output-with-filters.yaml`

**Problem**: All example YAML files fail `oc apply --dry-run=server` because the `ClusterLogForwarder` CRD (`observability.openshift.io/v1`) is not registered on the cluster. This is a direct consequence of Issue #1 (operator not installed). If the operator were successfully installed, these would likely pass. The examples themselves are structurally valid YAML and reference the correct API version.

**Reproduction**:
```
$ oc apply --dry-run=server -f examples/lokistack-basic.yaml
error: resource mapping not found for name: "collector" namespace: "openshift-logging" from "examples/lokistack-basic.yaml": no matches for kind "ClusterLogForwarder" in version "observability.openshift.io/v1"
ensure CRDs are installed first
```

**Fix needed**: This is a downstream effect of Issue #1. Once the channel/version references are corrected and the operator can be installed, these should pass. Add a prerequisite note to `examples/README.md` stating that the operator must be installed first.

---

## SIGNIFICANT — Incorrect information

### 4. Inconsistent label selectors for collector pods across documents

**Files affected**:
- `getting-started.md`: lines 319, 333 (uses `app.kubernetes.io/component=collector`)
- `api-reference.md`: lines 333, 336 (uses `component=collector`)
- `troubleshooting.md`: lines 20, 23, 106, 130, 133 (uses `component=collector`)

**Problem**: The getting-started guide uses the label selector `app.kubernetes.io/component=collector` while the API reference and troubleshooting guide use `component=collector`. These are different Kubernetes labels. Using the wrong one returns zero pods. A user who follows the getting-started guide will learn one label, then get no results when following troubleshooting commands.

**Reproduction**: Cannot verify which label is correct on this cluster since no collector pods exist (operator not installed). However, the inconsistency itself is a documentation defect regardless of which label is correct.

**Fix needed**: Determine which label the operator actually sets on collector pods and use it consistently across all docs. Based on modern Kubernetes labeling conventions, `app.kubernetes.io/component=collector` is the more likely correct label (it follows the recommended label convention). Update `api-reference.md` and `troubleshooting.md` to match `getting-started.md`.

---

### 5. Kafka example brokers missing required URL scheme prefix

**Files affected**:
- `configuration-reference.md`: line 452 (documents `brokers` validation as `Each entry pattern: ^(tcp|tls)://...`)
- `examples/kafka.yaml`: lines 23-24 (uses bare hostnames without scheme)

**Problem**: The configuration reference states that each Kafka broker entry must match `^(tcp|tls)://...`, but the kafka.yaml example uses bare hostnames: `"kafka-broker-1.example.com:9093"` and `"kafka-broker-2.example.com:9093"`. If the documented validation is correct, the example YAML would fail validation. If the example is correct, the documented pattern is wrong.

**Reproduction**:
```yaml
# examples/kafka.yaml lines 23-24 use:
brokers:
  - "kafka-broker-1.example.com:9093"
  - "kafka-broker-2.example.com:9093"

# But configuration-reference.md says each entry must match: ^(tcp|tls)://...
```

**Fix needed**: Either add `tls://` prefix to the broker entries in kafka.yaml (making them `"tls://kafka-broker-1.example.com:9093"`), or update the validation pattern in configuration-reference.md if bare hostnames are actually accepted.

---

### 6. Troubleshooting jsonpath with `[*]` piped to `jq` produces invalid JSON

**Files affected**:
- `troubleshooting.md`: line 17

**Problem**: The command `oc get clf collector -n openshift-logging -o jsonpath='{.status.conditions[*]}' | jq .` uses `[*]` which unpacks the array into space-separated individual JSON objects. When piped to `jq .`, this fails because `jq` in default mode expects a single JSON value. Multiple space-separated objects are not valid JSON input for `jq .`.

**Reproduction**: Cannot reproduce exactly since the CLF doesn't exist, but the jsonpath `[*]` behavior is well-documented: it iterates and space-separates elements rather than outputting an array.

**Fix needed**: Change the jsonpath from `'{.status.conditions[*]}'` to `'{.status.conditions}'` (remove `[*]`) to output a valid JSON array, or change the jq command to `jq -s .` to slurp space-separated objects into an array.

---

### 7. OperatorHub search name inconsistency between guides

**Files affected**:
- `getting-started.md`: line 68 (says search for "Cluster Logging")
- `deployment.md`: line 40 (says search for "Red Hat OpenShift Logging")

**Problem**: The two guides give different search terms for finding the operator in OperatorHub. The actual PackageManifest name is `cluster-logging`, displayed as "Red Hat OpenShift Logging" in the OperatorHub catalog. Using "Cluster Logging" as a search term may still find it, but the inconsistency between the two guides is confusing.

**Reproduction**:
```
$ oc get packagemanifests -n openshift-marketplace | grep -i logging
cluster-logging                                         Red Hat Operators     141m
logging-operator                                        Community Operators   141m
```

**Fix needed**: Use the same search term in both guides. "Red Hat OpenShift Logging" matches the catalog display name and is more precise (distinguishes from the community "logging-operator").

---

## MINOR — Cosmetic or edge-case issues

### 8. `oc auth can-i collect application` produces warnings without the operator

**Files affected**:
- `api-reference.md`: lines 349-350

**Problem**: The documented command `oc auth can-i collect application --as=system:serviceaccount:<namespace>:<service-account-name>` produces warnings when the operator is not installed: `Warning: the server doesn't have a resource type 'application'` and `Warning: verb 'collect' is not a known verb`. The command still returns a result (`no`), but the warnings could confuse users.

**Reproduction**:
```
$ oc auth can-i collect application --as=system:serviceaccount:openshift-logging:logcollector
Warning: the server doesn't have a resource type 'application'
Warning: verb 'collect' is not a known verb
no
```

**Fix needed**: Add a note that this command only works correctly after the operator is installed and the ClusterRoles exist. The warnings appear because the custom `collect` verb and `application` resource are defined by the operator's ClusterRoles.

---

### 9. Troubleshooting link to AsciiDoc file outside docs directory

**Files affected**:
- `troubleshooting.md`: line 189

**Problem**: The link `../docs/administration/high-volume-log-loss.adoc` points to an AsciiDoc file in the operator source tree. While the file exists in the source repository, it would not be available if the `user-docs/` directory is distributed standalone (e.g., published to a documentation site).

**Reproduction**:
```
$ ls ../docs/administration/high-volume-log-loss.adoc
# File exists in the source repo but is outside the user-docs/ directory
```

**Fix needed**: Either copy the relevant content into the troubleshooting guide, convert the link to an absolute URL pointing to the file on GitHub, or note that this link is relative to the operator source repository.

---

### 10. Missing prerequisite note in examples/README.md

**Files affected**:
- `examples/README.md`

**Problem**: The examples README lists example configurations but does not mention that the Cluster Logging Operator must be installed first. A user who navigates directly to the examples directory may attempt to apply them without having the CRDs registered.

**Fix needed**: Add a prerequisite note at the top stating that the Cluster Logging Operator must be installed before applying any example.

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 3 | Channel/version mismatch blocks installation; YAML examples fail without CRDs |
| SIGNIFICANT | 4 | Inconsistent label selectors, Kafka example vs validation pattern, jsonpath/jq issue, search name inconsistency |
| MINOR | 3 | `oc auth can-i` warnings, AsciiDoc cross-reference, missing prerequisite note |
| **Total** | **10** | |

### Commands used for validation

```bash
# Cluster baseline
export KUBECONFIG=<path>/kubeconfig
oc whoami
oc version
oc get clusterversion version -o jsonpath='{.status.desired.version}'
oc get featuregate cluster -o json | jq '.spec.featureSet'

# Namespace validation
oc get namespace openshift-logging -o json | jq '{labels: .metadata.labels, annotations: .metadata.annotations}'

# Operator validation
oc get deployment cluster-logging-operator -n openshift-logging
oc get csv -n openshift-logging
oc get subscription -n openshift-logging
oc get pods -n openshift-logging
oc get sa -n openshift-logging

# CRD validation
oc get crd clusterlogforwarders.observability.openshift.io
oc get crd logfilemetricexporters.logging.openshift.io
oc api-resources --api-group=observability.openshift.io
oc api-resources --api-group=logging.openshift.io

# ClusterRole validation
oc get clusterrole collect-application-logs
oc get clusterrole collect-infrastructure-logs
oc get clusterrole collect-audit-logs
oc get clusterrole cluster-logging-write-application-logs
oc get clusterrole cluster-logging-write-infrastructure-logs
oc get clusterrole cluster-logging-write-audit-logs
oc get clusterrole logging-collector-logs-writer
oc get clusterrole metadata-reader
oc get clusterrole clusterlogforwarder-editor-role
oc get clusterrole clusterlogforwarder-viewer-role

# Collector pod selectors (both variants)
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector
oc get pods -n openshift-logging -l component=collector

# Resource existence checks
oc get clusterlogforwarder -n openshift-logging
oc get clf -n openshift-logging
oc get logfilemetricexporter -n openshift-logging
oc get servicemonitor -n openshift-logging
oc get prometheusrule -n openshift-logging

# OperatorHub availability
oc get packagemanifests -n openshift-marketplace | grep -i logging
oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.channels[*].name}'
oc get packagemanifest cluster-logging -n openshift-marketplace -o jsonpath='{.status.defaultChannel}'
oc get packagemanifest cluster-logging -n openshift-marketplace -o json | jq '[.status.channels[] | {name, currentCSV}]'

# RBAC check
oc auth can-i collect application --as=system:serviceaccount:openshift-logging:logcollector

# YAML dry-run validation (all 7 examples)
oc apply --dry-run=server -f examples/lokistack-basic.yaml
oc apply --dry-run=server -f examples/elasticsearch.yaml
oc apply --dry-run=server -f examples/splunk.yaml
oc apply --dry-run=server -f examples/cloudwatch.yaml
oc apply --dry-run=server -f examples/kafka.yaml
oc apply --dry-run=server -f examples/syslog.yaml
oc apply --dry-run=server -f examples/multi-output-with-filters.yaml

# Deployment verification commands
oc wait --for=condition=available --timeout=5s deployment/cluster-logging-operator -n openshift-logging
oc get scc -o name
```
