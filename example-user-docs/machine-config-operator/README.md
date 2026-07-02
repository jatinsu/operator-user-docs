# Machine Config Operator Documentation

## Overview

The Machine Config Operator (MCO) is a core OpenShift 4 operator that manages the operating system and machine-level configuration for every node in the cluster. It handles updates and configuration changes to everything between the kernel and kubelet -- including systemd, CRI-O, kubelet, kernel arguments, NetworkManager, and more.

The MCO treats the operating system as "just another Kubernetes component" that you can inspect and manage with `oc`.

> **Hosted Control Plane (HyperShift) clusters:** On clusters with an external control plane topology (such as ROSA HCP or HyperShift), the MCO control plane runs on the management cluster, not on the hosted cluster. The core CRDs -- MachineConfig, MachineConfigPool, KubeletConfig, and ContainerRuntimeConfig -- are not available on the hosted cluster API. The MCO Deployments, DaemonSets, and the `machine-config` ClusterOperator are also absent. Most commands and examples in this documentation apply only to self-managed OpenShift clusters. You can check your cluster topology with:
>
> ```bash
> oc get infrastructure cluster -o jsonpath='{.status.controlPlaneTopology}'
> ```
>
> If the result is `External`, your cluster uses a hosted control plane and MCO is managed externally.

## Key Concepts

- **MachineConfig** -- Declarative configuration objects that define the desired state of a node's OS. Uses CoreOS Ignition format. You can manage files, systemd units, kernel arguments, extensions, FIPS mode, and kernel type.

- **MachineConfigPool** -- Groups nodes by role (master, worker) or custom labels. Controls how updates are rolled out (MaxUnavailable, pausing). Default pools: master, worker.

- **Rendered MachineConfig** -- The merged result of all applicable MachineConfig fragments for a pool. Named with `rendered-` prefix. This is what actually gets applied to nodes.

- **Ignition** -- The configuration format used by MachineConfig. JSON-based, declarative OS configuration from CoreOS.

- **rpm-ostree** -- Atomic OS update system used by Red Hat CoreOS (RHCOS). Updates are encapsulated in container images.

- **On-Cluster Layering** -- (4.12+) Allows building custom OS images using Containerfile/Dockerfile syntax directly on the cluster.

## Components

| Component | Description | Runs As |
|-----------|-------------|---------|
| Machine Config Operator | Top-level operator coordinating all sub-components | Deployment on control plane |
| Machine Config Controller | Orchestrates configuration rendering and update coordination (TemplateController, RenderController, UpdateController, KubeletConfigController) | Deployment on control plane |
| Machine Config Daemon | Applies configuration to nodes, performs OS updates, detects drift | DaemonSet on all nodes |
| Machine Config Server | Serves Ignition configs to nodes joining the cluster | DaemonSet on control plane |
| Machine OS Builder | Builds custom OS images on-cluster for layering (4.12+) | Deployment |

## Documentation Index

- [Getting Started](getting-started.md) -- Prerequisites, quick start, first operations
- [Configuration Reference](configuration-reference.md) -- All user-facing configuration options
- [API Reference](api-reference.md) -- CRD spec and status field reference
- [Deployment](deployment.md) -- Architecture, components, RBAC, bootstrap
- [Troubleshooting](troubleshooting.md) -- Common issues, diagnostics, recovery
- [Examples](examples/) -- Example YAML manifests

## Quick Status Check

```bash
# Check MCO operator status
oc describe clusteroperator/machine-config

# Check pool update status
oc get machineconfigpool

# View all MachineConfigs
oc get machineconfigs

# Check node configuration state
oc get nodes -o custom-columns='NAME:.metadata.name,CONFIG:.metadata.annotations.machineconfiguration\.openshift\.io/currentConfig,STATE:.metadata.annotations.machineconfiguration\.openshift\.io/state'
```
