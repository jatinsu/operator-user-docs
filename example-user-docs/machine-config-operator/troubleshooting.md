# Troubleshooting

> **Hosted Control Plane (HyperShift) clusters:** On clusters with `controlPlaneTopology: External`, most diagnostic commands below will fail because the MCO control plane (operator, controller, daemon, server) runs on the management cluster, not on the hosted cluster. The core CRDs (MachineConfig, MachineConfigPool) and the `machine-config` ClusterOperator are not available. If `oc get infrastructure cluster -o jsonpath='{.status.controlPlaneTopology}'` returns `External`, contact your cluster administrator or check the management cluster for MCO diagnostics.

## Diagnostic Commands

### Check Operator Status
```bash
oc describe clusteroperator/machine-config
```
Look at the `Available`, `Progressing`, and `Degraded` conditions.

### Check Pool Status
```bash
oc get machineconfigpool
```
Look at UPDATED, UPDATING, DEGRADED, MACHINECOUNT columns.

```bash
oc describe machineconfigpool/worker
```

### Check Node State
```bash
oc get nodes -o custom-columns='NAME:.metadata.name,CONFIG:.metadata.annotations.machineconfiguration\.openshift\.io/currentConfig,DESIRED:.metadata.annotations.machineconfiguration\.openshift\.io/desiredConfig,STATE:.metadata.annotations.machineconfiguration\.openshift\.io/state,REASON:.metadata.annotations.machineconfiguration\.openshift\.io/reason'
```

### Check MCD Logs
```bash
# Find the MCD pod on a specific node
oc get pods -n openshift-machine-config-operator -l k8s-app=machine-config-daemon -o wide

# View logs
oc logs -n openshift-machine-config-operator <mcd-pod-name> -c machine-config-daemon

# View journal logs on the node directly
oc debug node/<node-name> -- chroot /host journalctl -u machine-config-daemon-firstboot.service
oc debug node/<node-name> -- chroot /host journalctl -u kubelet.service
```

### Check MCC Logs
```bash
oc logs -n openshift-machine-config-operator deployment/machine-config-controller -c machine-config-controller
```

### Check MCO Logs
```bash
oc logs -n openshift-machine-config-operator deployment/machine-config-operator
```

---

## Common Issues

### Node Stuck in "Working" State

**Symptoms:** Node annotation `state` remains `Working` and pool shows `UPDATING`.

**Diagnosis:**
```bash
# Check which node is stuck
oc get nodes -o custom-columns='NAME:.metadata.name,STATE:.metadata.annotations.machineconfiguration\.openshift\.io/state' | grep Working

# Check MCD logs on that node
oc logs -n openshift-machine-config-operator <mcd-pod-on-stuck-node> -c machine-config-daemon
```

**Common causes:**
1. Node cannot drain — pods with PodDisruptionBudgets or local storage blocking drain
2. Node is waiting for reboot but reboot failed
3. OS update (rpm-ostree) failed

**Resolution:**
- Check for PDB issues: `oc get pdb -A`
- Check drain status: look for "drain" messages in MCD logs
- If stuck during OS update, check `oc debug node/<node> -- chroot /host rpm-ostree status`

### Node in "Degraded" State

**Symptoms:** Node annotation `state` is `Degraded`, pool shows `DEGRADED > 0`.

**Diagnosis:**
```bash
# Find degraded nodes
oc get nodes -o custom-columns='NAME:.metadata.name,STATE:.metadata.annotations.machineconfiguration\.openshift\.io/state,REASON:.metadata.annotations.machineconfiguration\.openshift\.io/reason' | grep Degraded

# Check MCD logs
oc logs -n openshift-machine-config-operator <mcd-pod> -c machine-config-daemon | grep -i "degraded\|error"
```

**Common causes:**
1. **Configuration drift** — Someone manually edited a file managed by MCO
2. **Failed update** — An error occurred during configuration application
3. **Unreconcilable MachineConfig** — The MachineConfig contains invalid or unsupported configuration

**Resolution for configuration drift:**
Option 1 — Fix the file manually to match the MachineConfig:
```bash
# Check what the expected content is
oc get machineconfig <rendered-config-name> -o yaml
```

Option 2 — Force MCD to reapply all configuration (causes reboot):
```bash
oc debug node/<node-name> -- chroot /host touch /run/machine-config-daemon-force
```

### Configuration Drift Detection

**Symptoms:** Node goes Degraded shortly after manual file changes on the node.

**Explanation:** Starting in OpenShift 4.10, MCD uses `fsnotify` to monitor files managed by MachineConfig. Any manual change to a managed file triggers immediate Degraded state.

**Diagnosis:**
```bash
# Check reason annotation
oc get node <node-name> -o jsonpath='{.metadata.annotations.machineconfiguration\.openshift\.io/reason}'
```

**Resolution:**
1. Revert the manual change to match the MachineConfig
2. Or create a new MachineConfig with the desired content
3. Or use the force file to reapply: `oc debug node/<node-name> -- chroot /host touch /run/machine-config-daemon-force`

### Pool Shows RenderDegraded

**Symptoms:** MachineConfigPool condition `RenderDegraded` is True.

**Diagnosis:**
```bash
oc describe machineconfigpool/worker | grep -A5 RenderDegraded
oc logs -n openshift-machine-config-operator deployment/machine-config-controller -c machine-config-controller | grep -i render
```

**Common causes:**
1. A MachineConfig has invalid Ignition syntax
2. Conflicting MachineConfigs (same file path with different content and no clear precedence)
3. Invalid label selector configuration

**Resolution:**
- Check recently created/modified MachineConfigs: `oc get machineconfig --sort-by=.metadata.creationTimestamp`
- Delete or fix the problematic MachineConfig

### KubeletConfig or ContainerRuntimeConfig Not Applying

**Symptoms:** KubeletConfig/ContainerRuntimeConfig status shows `Failure` condition.

**Diagnosis:**
```bash
oc describe kubeletconfig <name>
oc describe containerruntimeconfig <name>
oc logs -n openshift-machine-config-operator deployment/machine-config-controller -c machine-config-controller | grep -i kubelet
```

**Common causes:**
1. Invalid kubelet configuration fields
2. `machineConfigPoolSelector` does not match any pool
3. Pool label mismatch

**Resolution:**
- Verify the pool selector matches: `oc get mcp --show-labels`
- Validate the kubeletConfig fields against upstream Kubernetes documentation

### Updates Not Rolling Out

**Symptoms:** Pool shows new rendered config but nodes are not updating.

**Diagnosis:**
```bash
oc get machineconfigpool/worker -o yaml | grep -A5 'paused'
oc describe machineconfigpool/worker | grep -i maxUnavailable
```

**Common causes:**
1. Pool is paused (`spec.paused: true`)
2. MaxUnavailable nodes already reached
3. A previous node update is still in progress

**Resolution:**
```bash
# Unpause the pool
oc patch machineconfigpool/worker --type merge -p '{"spec":{"paused":false}}'

# Check if nodes are still updating
oc get nodes -o custom-columns='NAME:.metadata.name,STATE:.metadata.annotations.machineconfiguration\.openshift\.io/state'
```

### On-Cluster Build Failures

**Symptoms:** MachineConfigPool shows `BuildFailed` condition.

**Diagnosis:**
```bash
# Check MachineOSBuild status
oc get machineosbuilds
oc describe machineosbuild <name>

# Check builder pod logs
oc get pods -n openshift-machine-config-operator -l machineconfiguration.openshift.io/buildPod
oc logs -n openshift-machine-config-operator <builder-pod>

# Check build ConfigMaps for the Containerfile
oc get configmaps -n openshift-machine-config-operator -l machineconfiguration.openshift.io/build
```

**Common causes:**
1. Invalid Containerfile syntax
2. Push secret does not have access to the target registry
3. Base image pull failure
4. RPM installation failures in the Containerfile

**Resolution:**
- Fix the Containerfile content in MachineOSConfig
- Verify registry credentials: `oc get secret <push-secret-name> -n openshift-machine-config-operator -o yaml`
- Clean up failed builds and retry: delete the failed MachineOSBuild object

---

## Recovery Procedures

### Force Reconfiguration of a Node
If a node is degraded and cannot self-recover:
```bash
oc debug node/<node-name> -- chroot /host touch /run/machine-config-daemon-force
```
This causes MCD to skip the validity check and reapply all configuration. The node will reboot.

### Rolling Back a MachineConfig Change
MachineConfigs are declarative — to roll back, delete the MachineConfig that caused the issue:
```bash
oc delete machineconfig 99-worker-custom-config
```
This triggers a new render and rollout that reverts the change.

### Recovering from a Bad Kernel Argument
If a kernel argument prevents the node from booting:
1. Access the node console (out-of-band management, cloud console)
2. At the GRUB menu, edit the boot entry to remove the bad argument
3. Boot the node
4. Delete the offending MachineConfig

---

## Log Locations

| Component | Log Method |
|-----------|-----------|
| Machine Config Operator | `oc logs -n openshift-machine-config-operator deployment/machine-config-operator` |
| Machine Config Controller | `oc logs -n openshift-machine-config-operator deployment/machine-config-controller -c machine-config-controller` |
| Machine Config Daemon | `oc logs -n openshift-machine-config-operator <mcd-pod> -c machine-config-daemon` |
| Machine Config Server | `oc logs -n openshift-machine-config-operator <mcs-pod>` |
| Node systemd journal | `oc debug node/<node> -- chroot /host journalctl -u machine-config-daemon-firstboot.service` |
| Kubelet on node | `oc debug node/<node> -- chroot /host journalctl -u kubelet.service` |
| CRI-O on node | `oc debug node/<node> -- chroot /host journalctl -u crio.service` |
| rpm-ostree status | `oc debug node/<node> -- chroot /host rpm-ostree status` |

---

## Single Node OpenShift (SNO) Considerations
- No node draining occurs on SNO clusters (only one node, cannot drain the only control plane)
- Post-reboot, the cluster may take time to become fully available since all services run on the single node
- All authentication and API services are unavailable during reboot
- Rebootless updates are especially valuable on SNO

## Related Documentation
- [Getting Started](getting-started.md) -- Basic operations and status checks
- [Configuration Reference](configuration-reference.md) -- Configuration options
- [Deployment](deployment.md) -- Component architecture

## Writing Standards
- No emojis
- Include copyable commands for every diagnostic step
- Structure by symptom, not by component
- Include both diagnosis and resolution for each issue
