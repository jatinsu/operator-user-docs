# Deployment and Architecture

## Overview
The Machine Config Operator is a core OpenShift component deployed automatically during cluster installation by the Cluster Version Operator (CVO). It cannot be installed or removed independently — it is part of the OpenShift release payload.

> **Hosted Control Plane (HyperShift) clusters:** On clusters with `controlPlaneTopology: External`, the MCO control plane components (operator, controller, server, builder) run on the management cluster, not on the hosted cluster. Only metrics proxy pods (`kube-rbac-proxy-crio`) exist in the `openshift-machine-config-operator` namespace on the hosted cluster. The `machine-config` ClusterOperator, MCO Deployments, DaemonSets, and most service accounts described below are absent. The component topology described in this document applies to self-managed OpenShift clusters only.

## Namespace
All MCO components run in the `openshift-machine-config-operator` namespace.

## Component Topology

### Machine Config Operator
- **Type:** Deployment (1 replica)
- **Runs on:** Control plane nodes (`node-role.kubernetes.io/master`)
- **Priority:** `system-cluster-critical`
- **Binary:** `/usr/bin/machine-config-operator start`
- **Purpose:** Top-level operator that manages the lifecycle of all sub-components
- **Resources:** 20m CPU, 50Mi memory (request, no limits)

### Machine Config Controller
- **Type:** Deployment (runs on control plane)
- **Runs on:** Control plane nodes
- **Priority:** `system-cluster-critical`
- **Containers:**
  - `machine-config-controller` — Main controller
  - `kube-rbac-proxy` — Metrics proxy (port 9001)
- **Sub-controllers:**
  - **TemplateController** — Generates platform-owned MachineConfig objects from templates
  - **RenderController** — Merges MachineConfig fragments into rendered configs
  - **UpdateController** — Coordinates rolling updates to nodes
  - **KubeletConfigController** — Manages KubeletConfig CRD processing
  - **ContainerRuntimeConfigController** — Manages ContainerRuntimeConfig CRD processing
  - **NodeManagementController** — Tracks per-node configuration state via MachineConfigNode CRs
- **Resources:** 20m CPU, 50Mi memory per container

### Machine Config Daemon
- **Type:** DaemonSet (runs on ALL nodes)
- **Priority:** `system-node-critical`
- **Host Access:** `hostNetwork: true`, `hostPID: true`, privileged security context
- **Containers:**
  - `machine-config-daemon` — Main daemon
  - `kube-rbac-proxy` — Metrics proxy (port 9001)
- **Tolerations:** Tolerates ALL taints
- **Termination Grace Period:** 600 seconds (10 minutes)
- **Resources:** 20m CPU, 50Mi memory per container
- **Purpose:** Applies configuration to nodes, performs OS updates, detects configuration drift

### Machine Config Server
- **Type:** DaemonSet (runs on control plane nodes)
- **Runs on:** Control plane nodes (`node-role.kubernetes.io/master`)
- **Priority:** `system-cluster-critical`
- **Host Access:** `hostNetwork: true`
- **Ports:**
  - 22623 (HTTPS) — Secure Ignition config serving
  - 22624 (HTTP) — Insecure Ignition config serving
- **Endpoints:** Serves configs at `/config/<pool-name>` (e.g., `/config/master`, `/config/worker`)
- **Injected Data:** In addition to the rendered MachineConfig, MCS injects a node annotations file (seeding `currentConfig`/`desiredConfig` annotations) and a KubeConfig file into the Ignition config it serves
- **Resources:** 20m CPU, 50Mi memory
- **Purpose:** Serves Ignition configs to nodes joining the cluster

### Machine OS Builder
- **Type:** Deployment (1 replica)
- **Runs on:** Control plane nodes
- **Priority:** `system-cluster-critical`
- **Resources:** 20m CPU, 50Mi memory
- **Purpose:** Builds custom OS images on-cluster for CoreOS layering (available since OpenShift 4.16+ with TechPreview). Uses Buildah-based build pods to produce layered OS images from user-provided Containerfiles.

## Services

| Service | Port(s) | Description |
|---------|---------|-------------|
| `machine-config-controller` | 9001 | Metrics endpoint (via kube-rbac-proxy) |
| `machine-config-daemon` | 9001 | Metrics endpoint (via kube-rbac-proxy) |
| `machine-config-server` | 22623, 22624 | Ignition config serving (HTTPS, HTTP) |
| `kube-rbac-proxy-crio` | 9637 | CRI-O metrics proxy |

> **Note:** On HyperShift clusters, the Service objects may exist without backing Deployments or DaemonSets, since the MCO control plane runs on the management cluster. The `kube-rbac-proxy-crio` pods are the only MCO-namespace pods on the hosted cluster.

## RBAC

### Service Accounts
All in `openshift-machine-config-operator` namespace:
- `machine-config-operator` — Bound to `cluster-admin`
- `machine-config-controller` — Custom ClusterRole with access to MCO CRDs, nodes, secrets, config resources, machine resources
- `machine-config-daemon` — Custom ClusterRole with access to nodes, MCO CRDs, MachineConfigNodes, privileged SCC
- `machine-config-server` — Custom ClusterRole with access to MCO CRDs, ConfigMaps, hostnetwork SCC
- `node-bootstrapper` — Bootstrap-specific for CSR creation

### Security Context Constraints
| Component | SCC |
|-----------|-----|
| Machine Config Operator | restricted-v2 (runs as nobody/65534) |
| Machine Config Controller | restricted-v2 |
| Machine Config Daemon | privileged (required for OS management) |
| Machine Config Server | hostnetwork (required for bootstrap serving) |

## Bootstrap Process

During cluster installation, the MCO bootstraps through these phases:

### 1. Bootstrap Pod Creation
The installer creates a static bootstrap pod (`bootstrap-machine-config-operator`) on the bootstrap machine:
- **Init container:** `machine-config-controller` in bootstrap mode — generates initial MachineConfig and MachineConfigPool objects
- **Main container:** `machine-config-server` in bootstrap mode — serves Ignition configs

### 2. Bootstrap Dependencies
The bootstrap process requires:
- Root MCS CA certificate
- kube-apiserver serving CA bundle
- Container image pull secret
- ClusterConfig, Infrastructure, Network, DNS, and Proxy configurations
- Optional: cloud provider config, additional trust bundles

### 3. Bootstrap Manifests Generated
- `master.machineconfigpool.yaml` — Master pool definition
- `worker.machineconfigpool.yaml` — Worker pool definition
- `machineconfigcontroller-controllerconfig.yaml` — ControllerConfig
- Bootstrap pod manifest
- Platform-specific manifests

### 4. Node Bootstrap Flow
1. Machine Config Server serves Ignition configs on ports 22623/22624
2. New nodes fetch their pool's Ignition config during first boot
3. `machine-config-daemon-firstboot.service` runs before kubelet
4. Performs initial OS update via rpm-ostree if needed
5. Applies any configuration that Ignition does not handle (kernel args, extensions)
6. Reboots if OS was updated
7. Kubelet starts after base OS is ready

## Upgrade Process

### CVO-Driven Upgrades
The MCO is upgraded as part of the OpenShift cluster upgrade managed by the Cluster Version Operator:

1. CVO updates the MCO operator Deployment with the new image from the release payload
2. MCO operator starts with the new version
3. MCO updates the Machine Config Controller deployment
4. MCO updates the Machine Config Daemon DaemonSet (rolling update, `maxUnavailable: 10%`)
5. MCO updates the Machine Config Server DaemonSet

### OS Upgrades
1. The release payload includes a new `rhel-coreos` container image
2. MCO updates the ControllerConfig with the new base OS image
3. RenderController generates new rendered MachineConfigs
4. UpdateController coordinates the rolling update across nodes
5. Machine Config Daemon on each node performs the OS update via rpm-ostree
6. Nodes reboot into the new OS version

### Checking Upgrade Status
```bash
# Overall operator status
oc describe clusteroperator/machine-config

# Pool rollout progress
oc get machineconfigpool

# Detailed pool status
oc describe machineconfigpool/worker

# Individual node status
oc get nodes -o custom-columns='NAME:.metadata.name,STATE:.metadata.annotations.machineconfiguration\.openshift\.io/state'
```

## ClusterOperator Resource
The MCO reports its status through the `machine-config` ClusterOperator resource:

```bash
oc get clusteroperator machine-config -o yaml
```

Key status conditions:
- **Available** — MCO is functioning correctly
- **Progressing** — MCO is rolling out changes
- **Degraded** — MCO has encountered an error

Related objects tracked:
- MachineConfigs
- MachineConfigPools
- ControllerConfigs
- Nodes

## Monitoring
MCO exposes Prometheus metrics via kube-rbac-proxy sidecars:
- Machine Config Controller metrics: port 9001
- Machine Config Daemon metrics: port 9001

Metrics are scraped by the in-cluster Prometheus via PrometheusRule resources (`machine-config-controller`, `machine-config-daemon`).

> **Note:** On HyperShift clusters, ServiceMonitor resources may not be present in the `openshift-machine-config-operator` namespace. PrometheusRules are typically available.

## Related Documentation
- [Getting Started](getting-started.md) — Prerequisites and quick start
- [Configuration Reference](configuration-reference.md) — All configuration options
- [Troubleshooting](troubleshooting.md) — Common issues and diagnostics

## Writing Standards
- No emojis
- Use tables for structured data
- Include commands for checking status
- Cross-link to other docs
