# Troubleshooting Guide

This guide covers diagnostic commands, common issues, and solutions for the Cluster Logging Operator.

## Diagnostic Commands

### Check Overall Status

```bash
# Operator status
oc get deployment cluster-logging-operator -n openshift-logging

# ClusterLogForwarder status
oc get clf -n openshift-logging

# Detailed status with conditions
oc get clf collector -n openshift-logging -o jsonpath='{.status.conditions}' | jq .

# Collector pods
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector

# Collector pod logs
oc logs -n openshift-logging -l app.kubernetes.io/component=collector --tail=100

# Operator logs
oc logs -n openshift-logging deployment/cluster-logging-operator --tail=100
```

### Check Specific Conditions

```bash
# Check if ClusterLogForwarder is ready
oc get clf collector -n openshift-logging -o jsonpath='{.status.conditions[?(@.type=="Ready")]}'

# Check input validation
oc get clf collector -n openshift-logging -o jsonpath='{.status.inputConditions}'

# Check output validation
oc get clf collector -n openshift-logging -o jsonpath='{.status.outputConditions}'

# Check pipeline validation
oc get clf collector -n openshift-logging -o jsonpath='{.status.pipelineConditions}'
```

## Common Issues

### 1. ServiceAccount Does Not Exist

**Symptom:** Status condition shows reason `ServiceAccountDoesNotExist`

**Cause:** The ServiceAccount referenced in `spec.serviceAccount.name` does not exist in the namespace.

**Solution:**

```bash
oc create serviceaccount <name> -n openshift-logging
```

### 2. Missing ClusterRoles (ClusterRoleMissing)

**Symptom:** Status shows `ClusterRoleMissing` or `Authorized: False`

**Cause:** The collector ServiceAccount does not have the required ClusterRoles for the log types being collected.

**Solution:**

```bash
# For application logs
oc adm policy add-cluster-role-to-user collect-application-logs system:serviceaccount:openshift-logging:<sa-name>

# For infrastructure logs
oc adm policy add-cluster-role-to-user collect-infrastructure-logs system:serviceaccount:openshift-logging:<sa-name>

# For audit logs
oc adm policy add-cluster-role-to-user collect-audit-logs system:serviceaccount:openshift-logging:<sa-name>
```

### 3. Validation Failure

**Symptom:** Status shows `ValidationFailure`

**Cause:** The ClusterLogForwarder spec has configuration errors.

**Solution:** Check specific condition messages:

```bash
oc get clf collector -n openshift-logging -o yaml | grep -A5 "ValidationFailure"
```

Common validation issues:

- Pipeline references a non-existent input, output, or filter
- Output URL is malformed
- Required output fields are missing (e.g., authentication for Splunk)
- Invalid name format (must match `^[a-z][a-z0-9-]*[a-z0-9]$`)
- Filter regex does not compile

### 4. Collector Pods Not Starting

**Symptom:** Collector pods in CrashLoopBackOff or Pending state

**Diagnostic steps:**

```bash
# Check pod events
oc describe pod -n openshift-logging -l app.kubernetes.io/component=collector

# Check if there's a node selector mismatch
oc get nodes --show-labels

# Check resource availability
oc describe node <node-name> | grep -A10 "Allocated resources"
```

**Common causes:**

- Insufficient resources on nodes
- Node selector does not match any nodes
- Tolerations do not match node taints
- Security context constraint (SCC) issues

### 5. Logs Not Being Forwarded

**Symptom:** Logs are not appearing at the destination

**Diagnostic steps:**

```bash
# Check collector is running
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector

# Check collector logs for errors
oc logs -n openshift-logging -l app.kubernetes.io/component=collector --tail=200 | grep -i error

# Check Vector internal metrics
oc exec -n openshift-logging <collector-pod> -- curl -s http://localhost:24220/metrics

# Verify output connectivity
oc exec -n openshift-logging <collector-pod> -- curl -v <output-url>
```

**Common causes:**

- Output URL is not reachable from collector pods
- Authentication credentials are incorrect or expired
- TLS certificate issues (expired, wrong CA)
- Rate limiting is too aggressive
- Network policies blocking egress

### 6. High Memory Usage in Collector

**Symptom:** Collector pods OOMKilled

**Solution:** Increase memory limits:

```yaml
spec:
  collector:
    resources:
      limits:
        memory: 1Gi
      requests:
        memory: 512Mi
```

Also consider:

- Reducing the number of inputs or outputs
- Adding rate limits to high-volume inputs
- Using drop filters to reduce log volume

### 7. Log Loss Under High Volume

**Symptom:** Missing logs, gaps in log data

**Key concepts:**

- CRI-O rotates container log files at approximately 12KB per file, keeping up to 5 files
- If the collector cannot read logs fast enough, rotated files are lost
- This is inherent to the container log pipeline and not a bug

**Solutions:**

- Set delivery mode to `AtLeastOnce` (default) for durable delivery
- Increase collector resources (CPU and memory)
- Use rate limiting on inputs to control flow
- Reduce log volume with drop filters
- Monitor the metric `vector_buffer_events` for buffer growth
- See the [High Volume Log Loss guide](https://github.com/openshift/cluster-logging-operator/blob/master/docs/administration/high-volume-log-loss.adoc) for detailed capacity planning

### 8. File Fingerprinting Warnings

**Symptom:** Collector logs show "File fingerprinting warning"

**Cause:** When using a container runtime (like conmon) that creates extremely short-lived files, Vector may detect a file, attempt to fingerprint it (read initial bytes), but the file is already removed.

**Solution:** This warning is generally harmless and can be ignored. It occurs during normal container lifecycle operations.

### 9. Collector Not Redeploying After Config Change

**Symptom:** Changes to ClusterLogForwarder do not take effect

**Diagnostic:**

```bash
# Check if operator is running
oc get deployment cluster-logging-operator -n openshift-logging

# Check operator logs for reconciliation
oc logs deployment/cluster-logging-operator -n openshift-logging --tail=50 | grep -i reconcil

# Check management state
oc get clf collector -n openshift-logging -o jsonpath='{.spec.managementState}'
```

**Common causes:**

- ManagementState is set to "Unmanaged"
- Operator pod is not running
- Configuration validation failed (check status conditions)

### 10. TLS Certificate Errors

**Symptom:** Collector logs show TLS handshake errors or certificate verification failures

**Solutions:**

```bash
# Check if the Secret/ConfigMap with certs exists
oc get secret <secret-name> -n openshift-logging
oc get configmap <configmap-name> -n openshift-logging

# Verify cert validity
oc get secret <secret-name> -n openshift-logging -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout

# Temporarily test with insecureSkipVerify (NOT for production)
```

## Metrics and Alerts

The operator exposes these key metrics (via Prometheus):

| Metric | Description |
|--------|-------------|
| `log_collected_bytes_total` | Total bytes collected |
| `log_logged_bytes_total` | Total bytes logged |
| `vector_component_errors_total` | Total errors by component |
| `vector_buffer_events` | Current buffer size |
| `vector_component_sent_events_total` | Events sent per component |
| `vector_component_received_events_total` | Events received per component |

### Built-in Alerts

| Alert | Severity | Fires After | Description |
|-------|----------|-------------|-------------|
| `CollectorNodeDown` | critical | 10m | Collector pod cannot be scraped on a node |
| `ClusterLogForwarderNotReady` | error | 1m | ClusterLogForwarder is not in Ready state |
| `DiskBufferUsage` | warning | 5m | Disk buffer usage exceeds 15% of node `/var` filesystem |
| `ClusterLogForwarderOutputErrorRate` | critical | 5m | Output error rate exceeds 10% for a sink |
| `ClusterLogForwarderRuntimeConfigurationMissingUnmatched` | error | - | Runtime configuration has missing or unmatched elements |
| `ClusterLogForwarderAzureMonitorLogsDeprecation` | warning | - | ClusterLogForwarder uses deprecated Azure Monitor HTTP Data Collector API |
| `CollectorSourceDiscardedLogs` | warning | - | Collector source is discarding logs (typically exceeding maxMessageSize) |
| `CollectorHigh403ForbiddenResponseRate` | critical | - | High rate of HTTP 403 responses from an output |

Runbooks for alerts are available at [openshift/runbooks](https://github.com/openshift/runbooks/tree/master/alerts/cluster-logging-operator).

## Getting Help

- Check the [API Reference](api-reference.md) for valid field values and constraints
- Check the [Configuration Reference](configuration-reference.md) for all available options
- Review [OpenShift Logging Documentation](https://docs.openshift.com/container-platform/latest/logging/cluster-logging.html)
