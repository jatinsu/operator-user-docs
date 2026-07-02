# Troubleshooting

## Checking Operator Status

```bash
# Check operator pod
oc get pods -n openshift-logging -l name=cluster-logging-operator

# Check operator logs
oc logs -n openshift-logging deployment/cluster-logging-operator

# Check ClusterLogForwarder status
oc get clusterlogforwarder -n openshift-logging -o yaml
```

### Understanding Status Conditions

The ClusterLogForwarder reports several condition types that indicate the health and validity of your logging configuration:

- **Ready**: True when collectors are deployed and running.
- **observability.openshift.io/Valid**: Validation of the overall configuration has passed.
- **observability.openshift.io/Authorized**: RBAC permissions have been verified for the service account.
- **ValidInput{name}**: Per-input validation status, reported for each named input.
- **ValidOutput{name}**: Per-output validation status, reported for each named output.
- **ValidPipeline{name}**: Per-pipeline validation status, reported for each named pipeline.
- **ValidFilter{name}**: Per-filter validation status, reported for each named filter.

## Checking Collector Status

```bash
# List collector pods
oc get pods -n openshift-logging -l app.kubernetes.io/component=collector

# Check collector logs
oc logs -n openshift-logging <collector-pod-name>

# Check collector configuration
oc get configmap -n openshift-logging -l app.kubernetes.io/component=collector -o yaml
```

## Common Issues

### Collector Pods Not Starting

**Symptoms**: Collector pods in CrashLoopBackOff or Pending state.

**Possible causes**:
- Missing or incorrect service account
- Insufficient RBAC permissions
- Resource constraints (CPU/memory limits too low)
- Node selector or toleration mismatch

**Resolution steps**:
1. Check pod events: `oc describe pod <pod-name> -n openshift-logging`
2. Verify the service account exists.
3. Verify ClusterRoleBindings are in place.
4. Check resource limits in the collector spec.

### Logs Not Being Forwarded

**Symptoms**: No logs appearing at the output destination.

**Possible causes**:
- Output URL incorrect or unreachable
- TLS certificate issues
- Authentication credentials missing or expired
- Network policy blocking egress

**Resolution steps**:
1. Check ClusterLogForwarder status conditions.
2. Check collector pod logs for connection errors.
3. Verify output credentials in referenced Secrets.
4. Test network connectivity from the collector pod.

### Permission Denied Errors

**Symptoms**: Status condition shows Authorized=False.

**Possible causes**:
- Service account missing required ClusterRoleBindings
- Attempting to collect log types without the appropriate role

**Resolution**:
```bash
# Grant application log collection
oc adm policy add-cluster-role-to-user collect-application-logs system:serviceaccount:<namespace>:<sa-name>

# Grant infrastructure log collection
oc adm policy add-cluster-role-to-user collect-infrastructure-logs system:serviceaccount:<namespace>:<sa-name>

# Grant audit log collection
oc adm policy add-cluster-role-to-user collect-audit-logs system:serviceaccount:<namespace>:<sa-name>
```

### High Log Volume / Log Loss

**Symptoms**: Logs being dropped, high memory usage on collector pods.

**Possible causes**:
- Collector resource limits too low for log volume
- No rate limiting configured
- Slow output destination causing backpressure

**Resolution**:
1. Increase collector resources.
2. Configure rate limiting (per-container or per-output maxRecordsPerSecond).
3. Use AtLeastOnce delivery mode for critical logs.
4. Consider splitting pipelines across multiple outputs.

### TLS Connection Failures

**Symptoms**: Collector logs show TLS handshake errors.

**Possible causes**:
- Missing or incorrect CA certificate
- Expired certificates
- TLS version mismatch (check security profile)
- insecureSkipVerify not set when using self-signed certs

**Resolution**:
1. Verify the CA bundle in the referenced Secret or ConfigMap.
2. Check certificate expiration dates.
3. Try setting the TLS security profile to "Old" for compatibility testing.
4. For testing only, set insecureSkipVerify: true.

## Enabling Debug Logging

Set the Vector collector log level via annotation:
```bash
oc annotate clusterlogforwarder instance -n openshift-logging observability.openshift.io/log-level=debug
```

Valid levels: trace, debug, info, warn, error, off

## Using Must-Gather

Collect comprehensive diagnostic data:
```bash
oc adm must-gather --image=quay.io/openshift-logging/cluster-logging-operator:latest -- /usr/bin/gather
```

This collects:
- Operator and collector pod logs
- ClusterLogForwarder and all related CRs
- ConfigMaps with Vector configuration
- RBAC resources
- Prometheus alerting rules
- Node and PV information
- Namespace configurations

The output is organized under `cluster-logging/` in the must-gather archive.

## Unmanaged Mode for Advanced Debugging

For advanced troubleshooting, switch to Unmanaged mode to manually edit the Vector configuration:

```bash
oc patch clusterlogforwarder instance -n openshift-logging --type=merge -p '{"spec":{"managementState":"Unmanaged"}}'
```

Then edit the collector ConfigMap directly. Restart collector pods to apply:
```bash
oc delete pods -n openshift-logging -l app.kubernetes.io/component=collector
```

Switch back to Managed when done:
```bash
oc patch clusterlogforwarder instance -n openshift-logging --type=merge -p '{"spec":{"managementState":"Managed"}}'
```

## Useful Diagnostic Commands

```bash
# Check all logging resources
oc get all -n openshift-logging

# View collector DaemonSet
oc get daemonset -n openshift-logging -l app.kubernetes.io/component=collector

# Check events in the namespace
oc get events -n openshift-logging --sort-by='.lastTimestamp'

# View the generated Vector configuration (replace <clf-name> with your ClusterLogForwarder name, e.g. "instance")
oc get configmap -n openshift-logging <clf-name>-config -o jsonpath='{.data["vector\.toml"]}'

# Check metrics endpoint
oc exec -n openshift-logging <collector-pod> -- curl -s http://localhost:24231/metrics
```
