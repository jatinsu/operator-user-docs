# Getting Started with the Machine Config Operator

## Prerequisites

- OpenShift Container Platform 4.x cluster with **self-managed control plane** (not HyperShift/Hosted Control Plane)
- Red Hat CoreOS (RHCOS) nodes -- the MCO manages RHCOS specifically and does not apply to non-RHCOS nodes
- `oc` CLI tool configured with cluster-admin access
- The MCO is installed automatically as part of OpenShift -- no manual installation is needed

> **Note:** On Hosted Control Plane (HyperShift) clusters, MCO runs on the management cluster and the core CRDs (MachineConfig, MachineConfigPool, KubeletConfig, ContainerRuntimeConfig) are not available on the hosted cluster. The commands and examples in this guide assume a self-managed cluster. Check your topology with `oc get infrastructure cluster -o jsonpath='{.status.controlPlaneTopology}'` -- if it returns `External`, this guide does not apply to your cluster.

## Understanding the MCO

The Machine Config Operator (MCO) is a **day-0 operator** that is deployed during cluster installation by the Cluster Version Operator (CVO). It is responsible for managing the operating system and core system configuration of every RHCOS node in the cluster.

Key facts:

- It runs in the `openshift-machine-config-operator` namespace.
- It manages four sub-components:

| Sub-component | Role |
|---|---|
| Machine Config Controller | Watches for MachineConfig changes and coordinates rollouts across pools |
| Machine Config Daemon | Runs on every node; applies configuration and performs drain/reboot |
| Machine Config Server | Serves Ignition configs to new machines joining the cluster |
| Machine OS Builder | Builds custom OS images when on-cluster layering is enabled |

- All configuration is declarative via Custom Resources (MachineConfig, MachineConfigPool, KubeletConfig, ContainerRuntimeConfig, and others).

## Checking MCO Status

### Operator Health

```bash
oc describe clusteroperator/machine-config
```

The output includes three key conditions:

| Condition | Meaning |
|---|---|
| Available | `True` when the operator is functional and serving its purpose |
| Progressing | `True` when the operator is actively rolling out a configuration change |
| Degraded | `True` when the operator has encountered an error that it cannot recover from automatically |

A healthy operator shows `Available=True`, `Progressing=False`, `Degraded=False`.

### Pool Status

```bash
oc get machineconfigpool
```

The output columns are:

| Column | Meaning |
|---|---|
| NAME | Name of the pool (e.g., `master`, `worker`) |
| CONFIG | The name of the currently rendered (merged) MachineConfig for this pool |
| UPDATED | `True` if all nodes in the pool are running the latest rendered config |
| UPDATING | `True` if at least one node is currently being updated |
| DEGRADED | `True` if a node in this pool has failed to apply its config |
| MACHINECOUNT | Total number of nodes in the pool |
| READYMACHINECOUNT | Number of nodes that are ready and schedulable |
| UPDATEDMACHINECOUNT | Number of nodes running the latest rendered config |

To see full details for the worker pool:

```bash
oc describe machineconfigpool/worker
```

### Node Configuration State

```bash
oc get nodes -o custom-columns='NAME:.metadata.name,CONFIG:.metadata.annotations.machineconfiguration\.openshift\.io/currentConfig,DESIRED:.metadata.annotations.machineconfiguration\.openshift\.io/desiredConfig,STATE:.metadata.annotations.machineconfiguration\.openshift\.io/state'
```

The STATE column reports one of three values:

| State | Meaning |
|---|---|
| Done | The node has successfully applied its desired config |
| Working | The node is currently applying a new config (drain, apply, reboot cycle) |
| Degraded | The node encountered an error while applying the config |

When CONFIG and DESIRED match and STATE is `Done`, the node is fully up to date.

## Your First MachineConfig

### Example: Adding a Custom File

The following MachineConfig adds a file at `/etc/my-custom-config` on all worker nodes:

```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  labels:
    machineconfiguration.openshift.io/role: worker
  name: 99-worker-custom-file
spec:
  config:
    ignition:
      version: 3.2.0
    storage:
      files:
        - contents:
            source: data:text/plain;charset=utf-8;base64,SGVsbG8gZnJvbSBNQ08K
          mode: 0644
          path: /etc/my-custom-config
          overwrite: true
```

Apply it:

```bash
oc apply -f 99-worker-custom-file.yaml
```

### Monitoring the Rollout

Watch the pool update in real time:

```bash
oc get machineconfigpool/worker -w
```

Check individual node progress:

```bash
oc get nodes -o custom-columns='NAME:.metadata.name,STATE:.metadata.annotations.machineconfiguration\.openshift\.io/state'
```

The MCO will drain each node, apply the configuration, and reboot the node. It respects the `maxUnavailable` setting on the MachineConfigPool (default: 1 node at a time), so updates roll through the pool one node at a time unless you change this value.

### Example: Adding Kernel Arguments

```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  labels:
    machineconfiguration.openshift.io/role: worker
  name: 99-worker-kernel-args
spec:
  config:
    ignition:
      version: 3.2.0
  kernelArguments:
    - nosmt
    - loglevel=7
```

### Example: Adding a Systemd Unit

```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  labels:
    machineconfiguration.openshift.io/role: worker
  name: 99-worker-custom-service
spec:
  config:
    ignition:
      version: 3.2.0
    systemd:
      units:
        - name: my-custom.service
          enabled: true
          contents: |
            [Unit]
            Description=My Custom Service
            After=network-online.target

            [Service]
            Type=oneshot
            ExecStart=/usr/local/bin/my-script.sh
            RemainAfterExit=yes

            [Install]
            WantedBy=multi-user.target
```

## Common Operations

### Pausing Updates

To pause updates on the worker pool (for example, during a maintenance window or while debugging):

```bash
oc patch machineconfigpool/worker --type merge -p '{"spec":{"paused":true}}'
```

To resume updates:

```bash
oc patch machineconfigpool/worker --type merge -p '{"spec":{"paused":false}}'
```

**Tip:** If you plan to apply multiple MachineConfigs, pause the pool first, apply all changes, then unpause. This triggers a single rollout instead of multiple sequential node reboots.

### Checking MCD Logs on a Node

To check the Machine Config Daemon logs on a specific node (useful when a node is degraded or stuck):

```bash
oc logs -n openshift-machine-config-operator \
  $(oc get pod -n openshift-machine-config-operator \
    -l k8s-app=machine-config-daemon \
    --field-selector spec.nodeName=<node-name> -o name) \
  -c machine-config-daemon
```

### Updating SSH Keys

```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfig
metadata:
  labels:
    machineconfiguration.openshift.io/role: worker
  name: 99-worker-ssh-key
spec:
  config:
    ignition:
      version: 3.2.0
    passwd:
      users:
        - name: core
          sshAuthorizedKeys:
            - ssh-rsa AAAA... your-key-here
```

**Note:** SSH key changes are applied without a reboot.

### Updating the Pull Secret

```bash
oc set data secret/pull-secret -n openshift-config --from-file=.dockerconfigjson=pull-secret.json
```

**Note:** Pull secret changes are applied without drain or reboot (as of OpenShift 4.7+).

## Custom MachineConfigPools

You can create custom pools to apply different configurations to subsets of nodes. A common use case is creating an `infra` pool for infrastructure workloads.

Define the pool:

```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineConfigPool
metadata:
  name: infra
spec:
  machineConfigSelector:
    matchExpressions:
      - key: machineconfiguration.openshift.io/role
        operator: In
        values:
          - worker
          - infra
  nodeSelector:
    matchLabels:
      node-role.kubernetes.io/infra: ""
```

The `machineConfigSelector` includes both `worker` and `infra` so that infra nodes inherit the base worker configuration plus any infra-specific MachineConfigs.

Then label the nodes that should belong to this pool:

```bash
oc label node <node-name> node-role.kubernetes.io/infra=""
```

## Important Notes

- MachineConfigs are sorted lexicographically when merged into a rendered config. Use numeric prefixes (e.g., `99-`) to control ordering and ensure your custom configs are applied last.
- The `machineconfiguration.openshift.io/role` label on a MachineConfig determines which pool it applies to.
- Never modify rendered MachineConfigs (those prefixed with `rendered-`). They are generated automatically by the Machine Config Controller.
- Most MachineConfig changes trigger a node drain and reboot. Exceptions include SSH keys, pull secrets, and certain registry configurations.
- To target control plane nodes, use `machineconfiguration.openshift.io/role: master`.

## Next Steps

- [Configuration Reference](configuration-reference.md) -- Full reference for KubeletConfig, ContainerRuntimeConfig, and more
- [API Reference](api-reference.md) -- Complete CRD field documentation
- [Troubleshooting](troubleshooting.md) -- Common issues and diagnostic steps
