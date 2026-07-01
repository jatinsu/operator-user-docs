# API Reference

Complete Custom Resource Definition (CRD) reference for all MCO resources. All CRDs are cluster-scoped and belong to the `machineconfiguration.openshift.io` API group (v1) unless otherwise noted.

> **Hosted Control Plane (HyperShift) clusters:** On clusters with `controlPlaneTopology: External`, the following CRDs are **not available** on the hosted cluster: MachineConfig, MachineConfigPool, KubeletConfig, ContainerRuntimeConfig. The following CRDs **are available**: ControllerConfig, MachineConfigNode, MachineOSConfig, MachineOSBuild, PinnedImageSet, and MachineConfiguration (`operator.openshift.io/v1`). However, ControllerConfig and MachineConfigNode instances may not be populated.

## MachineConfig

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `MachineConfig`
**Scope:** Cluster
**Short Name:** `mc`

### Spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `config` | `runtime.RawExtension` | No | Ignition Config object (v3.2.0+). Contains storage (files), systemd (units), and passwd (users) sections. |
| `kernelArguments` | `[]string` | No | List of kernel arguments to add to bootloader. |
| `extensions` | `[]string` | No | Additional RHCOS extensions to enable on the host. |
| `fips` | `bool` | No | Controls FIPS 140-2 mode. |
| `kernelType` | `string` | No | Kernel variant: `default`, `realtime`, or `64k-pages` (aarch64 only). |
| `osImageURL` | `string` | No | Remote location for OS image. |
| `baseOSExtensionsContainerImage` | `string` | No | Remote location for OS extensions container image. |

MachineConfig has no status subresource.

---

## MachineConfigPool

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `MachineConfigPool`
**Scope:** Cluster
**Short Name:** `mcp`

### Spec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `machineConfigSelector` | `*metav1.LabelSelector` | No | — | Label selector for applicable MachineConfigs. |
| `nodeSelector` | `*metav1.LabelSelector` | No | — | Label selector for nodes belonging to this pool. |
| `paused` | `bool` | No | `false` | Stops all changes to the pool, including new rendered config generation. |
| `maxUnavailable` | `*intstr.IntOrString` | No | `1` | Maximum unavailable nodes during update. Accepts integer or percentage string. Cannot be 0. |
| `configuration` | `MachineConfigPoolStatusConfiguration` | No | — | Targeted MachineConfig for the pool. |
| `pinnedImageSets` | `[]PinnedImageSetRef` | No | — | Ordered list of PinnedImageSet references (max 100). |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `observedGeneration` | `int64` | Most recent generation observed by the controller. |
| `configuration` | `MachineConfigPoolStatusConfiguration` | The current rendered MachineConfig object for the pool. Contains `name` and `source` (list of contributing MachineConfigs). |
| `machineCount` | `int32` | Total machines in the pool. |
| `updatedMachineCount` | `int32` | Machines running the current rendered MachineConfig. |
| `readyMachineCount` | `int32` | Machines in Ready state. |
| `unavailableMachineCount` | `int32` | Machines not in Ready state. |
| `degradedMachineCount` | `int32` | Machines marked degraded or unreconcilable. |
| `conditions` | `[]MachineConfigPoolCondition` | Pool status conditions. |
| `certExpirys` | `[]CertExpiry` | Certificate expiration tracking. |

### Condition Types
- `Updated` — Pool is fully updated to the current rendered config.
- `Updating` — Pool is in the process of updating nodes.
- `NodeDegraded` — One or more nodes cannot complete the update.
- `RenderDegraded` — Rendered configuration cannot be generated.
- `Degraded` — General degraded state.
- `BuildPending` — On-cluster build is pending.
- `Building` — On-cluster build is in progress.
- `BuildSuccess` — On-cluster build completed.
- `BuildFailed` — On-cluster build failed.
- `BuildInterrupted` — On-cluster build was interrupted.
- `PinnedImageSetsDegraded` — Pinned images cannot be populated.

---

## KubeletConfig

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `KubeletConfig`
**Scope:** Cluster

### Spec

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `machineConfigPoolSelector` | `*metav1.LabelSelector` | No | — | Selects target MachineConfigPools. |
| `kubeletConfig` | `*runtime.RawExtension` | No | — | Upstream Kubernetes kubelet configuration fields. Validated by kubelet. |
| `autoSizingReserved` | `*bool` | No | `true` (workers), `false` (control plane) | Auto-calculate system-reserved CPU/memory. |
| `logLevel` | `*int32` | No | `2` | Kubelet log verbosity (0=minimal, 10=trace). |
| `tlsSecurityProfile` | `*configv1.TLSSecurityProfile` | No | Inherited from `apiservers.config.openshift.io/cluster` | TLS settings for kubelet HTTPS serving. Types: Old, Intermediate, Modern, Custom. |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `observedGeneration` | `int64` | Most recent generation observed by the controller. |
| `conditions` | `[]KubeletConfigCondition` | Status conditions: `Success`, `Failure`. |

---

## ContainerRuntimeConfig

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `ContainerRuntimeConfig`
**Scope:** Cluster
**Short Name:** `ctrcfg`

### Spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `machineConfigPoolSelector` | `*metav1.LabelSelector` | No | Selects target MachineConfigPools. |
| `containerRuntimeConfig` | `*ContainerRuntimeConfiguration` | No | CRI-O runtime configuration. |

### ContainerRuntimeConfiguration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pidsLimit` | `*int64` | — | Maximum processes per container. |
| `logLevel` | `string` | — | CRI-O log level: `fatal`, `panic`, `error`, `warn`, `info`, `debug`. |
| `logSizeMax` | `*resource.Quantity` | — | Maximum container log file size. Must be >= 8192 if positive. Negative = unlimited. |
| `overlaySize` | `*resource.Quantity` | `10GB` | Maximum container image size quota. |
| `defaultRuntime` | `string` | `crun` | Default OCI runtime: `crun` or `runc`. |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `observedGeneration` | `int64` | Most recent generation observed. |
| `conditions` | `[]ContainerRuntimeConfigCondition` | Status conditions: `Success`, `Failure`. |

---

## ControllerConfig

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `ControllerConfig`
**Scope:** Cluster

This resource is managed by the MCO operator and drives the MachineConfigController's template rendering. Users typically do not create or modify this directly.

### Key Spec Fields

| Field | Type | Description |
|-------|------|-------------|
| `clusterDNSIP` | `string` | Cluster DNS IP address. |
| `cloudProviderConfig` | `string` | Cloud provider configuration. |
| `kubeAPIServerServingCAData` | `[]byte` | Kubelet-to-API-Server certificate. |
| `rootCAData` | `[]byte` | Root CA data. |
| `additionalTrustBundle` | `[]byte` | Additional certificates for node trusted store. |
| `pullSecret` | `*corev1.ObjectReference` | Reference to default pull secret. |
| `images` | `map[string]string` | Images used by controller for template rendering. |
| `baseOSContainerImage` | `string` | New-format OS container image. |
| `releaseImage` | `string` | Image used during cluster installation. |
| `proxy` | `*configv1.ProxyStatus` | Cluster proxy configuration. |
| `infra` | `*configv1.Infrastructure` | Infrastructure details. |
| `dns` | `*configv1.DNS` | Cluster DNS configuration. |
| `ipFamilies` | `IPFamiliesType` | IP families: `IPv4`, `IPv6`, `DualStack`, `DualStackIPv6Primary`. |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `observedGeneration` | `int64` | Most recent generation observed. |
| `conditions` | `[]ControllerConfigStatusCondition` | Template controller conditions: Running, Completed, Failing. |
| `controllerCertificates` | `[]ControllerCertificate` | Auto-rotating certificates with subject, signer, notBefore, notAfter. |

---

## MachineConfigNode

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `MachineConfigNode`
**Scope:** Cluster

Tracks the health and configuration state of individual nodes.

### Spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `node` | `MCOObjectReference` | Yes | Reference to the node. Name must match metadata.name. |
| `pool` | `MCOObjectReference` | Yes | Reference to the MachineConfigPool. |
| `configVersion` | `MachineConfigNodeSpecMachineConfigVersion` | Yes | Desired config version. Contains `desired` field. |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `conditions` | `[]metav1.Condition` | Node update conditions. |
| `observedGeneration` | `int64` | Most recent generation observed by MCO. |
| `configVersion` | `*MachineConfigNodeStatusMachineConfigVersion` | Current and desired config versions. |
| `pinnedImageSets` | `[]MachineConfigNodeStatusPinnedImageSet` | Status of pinned image sets on this node. |

### Condition Types
- `UpdatePrepared` — Update preparation complete.
- `UpdateExecuted` — Update executed.
- `UpdatePostActionComplete` — Post-update action complete.
- `UpdateComplete` — Full update cycle complete.
- `Updated` — Node is up to date.
- `Resumed` — Node resumed after update.
- `Drained` — Node drained.
- `Cordoned` — Node cordoned.
- `Uncordoned` — Node uncordoned.
- `AppliedFilesAndOS` — Files and OS changes applied.
- `RebootedNode` — Node rebooted.
- `NodeDegraded` — Node is degraded.
- `PinnedImageSetsProgressing` — Pinned images being pulled.
- `PinnedImageSetsDegraded` — Pinned images degraded.

---

## MachineOSConfig

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `MachineOSConfig`
**Scope:** Cluster

Configures on-cluster OS image builds. One MachineOSConfig per MachineConfigPool. Name must match the referenced pool name.

### Spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `machineConfigPool` | `MachineConfigPoolReference` | Yes | Pool to build for. |
| `imageBuilder` | `MachineOSImageBuilder` | Yes | Image builder backend. `imageBuilderType: Job`. |
| `baseImagePullSecret` | `*ImageSecretObjectReference` | No | Secret for pulling base image (in openshift-machine-config-operator namespace). |
| `renderedImagePushSecret` | `ImageSecretObjectReference` | Yes | Secret for pushing the built image. |
| `renderedImagePushSpec` | `ImageTagFormat` | Yes | Registry location for final image. Format: `host[:port][/namespace]/name:<tag>`. Max 447 chars. |
| `containerFile` | `[]MachineOSContainerfile` | No | Custom Containerfile content per architecture (max 4 entries, max 4096 chars each). |

### MachineOSContainerfile

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `containerfileArch` | `string` | No | Architecture: `NoArch` (default), `AMD64`, `ARM64`, `PPC64LE`, `S390X`. |
| `content` | `string` | Yes | Containerfile/Dockerfile content. Max 4096 characters. |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `conditions` | `[]metav1.Condition` | Configuration state conditions. |
| `observedGeneration` | `int64` | Most recent generation observed. |
| `currentImagePullSpec` | `ImageDigestFormat` | Current built image pull spec with digest. |
| `machineOSBuild` | `*ObjectReference` | Reference to the active MachineOSBuild. |

---

## MachineOSBuild

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `MachineOSBuild`
**Scope:** Cluster

Represents a single OS image build process. Spec is immutable once set.

### Spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `machineConfig` | `MachineConfigReference` | Yes | Rendered MachineConfig to include in the build. Name 10-253 chars. |
| `machineOSConfig` | `MachineOSConfigReference` | Yes | Referenced MachineOSConfig. Name 1-253 chars. |
| `renderedImagePushSpec` | `ImageTagFormat` | Yes | Final image location. Max 447 chars. |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `conditions` | `[]metav1.Condition` | Build state: Prepared, Building, Failed, Interrupted, Succeeded. Immutable once terminal. |
| `builder` | `*MachineOSBuilderReference` | Image builder backend used. Contains job reference. |
| `relatedObjects` | `[]ObjectReference` | Ephemeral build objects (ConfigMaps, Secrets). Max 10. |
| `buildStart` | `*metav1.Time` | When build initiated. Immutable. |
| `buildEnd` | `*metav1.Time` | When build completed. Immutable. Must be after buildStart. |
| `digestedImagePushSpec` | `ImageDigestFormat` | Final image pull spec with digest. |

---

## PinnedImageSet

**API Version:** `machineconfiguration.openshift.io/v1`
**Kind:** `PinnedImageSet`
**Scope:** Cluster

Defines images to preload on nodes via CRI-O pinning.

### Spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pinnedImages` | `[]PinnedImageRef` | Yes | OCI images referenced by digest (1-500 images). |

### PinnedImageRef

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `ImageDigestFormat` | Yes | Image reference by digest. Format: `host[:port][/namespace]/name@sha256:<64-hex-chars>`. Max 447 chars. |

---

## MachineConfiguration (operator.openshift.io/v1)

**API Version:** `operator.openshift.io/v1`
**Kind:** `MachineConfiguration`
**Scope:** Cluster (singleton named `cluster`)

Configures MCO operator behavior including node disruption policies and boot image management.

### Spec

| Field | Type | Description |
|-------|------|-------------|
| `nodeDisruptionPolicy` | `NodeDisruptionPolicyConfig` | Granular node disruption policies. |
| `managedBootImages` | `ManagedBootImages` | Boot image management configuration. |

### nodeDisruptionPolicy Fields

| Field | Type | Max | Description |
|-------|------|-----|-------------|
| `files` | `[]NodeDisruptionPolicySpecFile` | 50 | File-path-based policies. Each has `path` and `actions[]`. |
| `units` | `[]NodeDisruptionPolicySpecUnit` | 50 | Systemd unit policies. Each has `name` and `actions[]`. |
| `sshkey` | `NodeDisruptionPolicySpecSSHKey` | — | SSH key change policy. Has `actions[]`. |

### Action Types
- `Reboot` — Drain and reboot the node.
- `Drain` — Drain workloads from the node.
- `Reload` — Reload a systemd service. Requires `reload.serviceName`.
- `Restart` — Restart a systemd service. Requires `restart.serviceName`.
- `DaemonReload` — Reload systemd manager (`systemctl daemon-reload`).
- `None` — No action required.
- `Special` — Internal MCO action (status only, cannot be set by users).

### managedBootImages Fields

| Field | Type | Max | Description |
|-------|------|-----|-------------|
| `machineManagers` | `[]MachineManager` | 5 | Registered machine resources for boot image updates. |

### MachineManager

| Field | Type | Description |
|-------|------|-------------|
| `resource` | `string` | Resource type: `machinesets` or `controlplanemachinesets`. |
| `apiGroup` | `string` | API group: `machine.openshift.io`. |
| `selection` | `MachineManagerSelector` | Selection mode: `All`, `Partial`, or `None`. |

### Status

| Field | Type | Description |
|-------|------|-------------|
| `observedGeneration` | `int64` | Most recent generation observed. |
| `conditions` | `[]metav1.Condition` | Status conditions. |
| `nodeDisruptionPolicyStatus` | `NodeDisruptionPolicyStatus` | Merged cluster + user disruption policies. |
| `managedBootImagesStatus` | `ManagedBootImages` | Validated boot image configuration. |

---

## Common Types

### ImageDigestFormat
Format: `host[:port][/namespace]/name@sha256:<64-hex-chars>`
Length: 1-447 characters.

### ImageTagFormat
Format: `host[:port][/namespace]/name:<tag>` or `svc_name.namespace.svc[:port]/repository/name:<tag>`
Length: 1-447 characters.

### IPFamiliesType
Enum: `IPv4`, `IPv6`, `DualStack`, `DualStackIPv6Primary`.

## Related Documentation
- [Configuration Reference](configuration-reference.md) — User-focused configuration guide with examples
- [Getting Started](getting-started.md) — Quick start guide
- [Examples](examples/) — Example YAML manifests

## Writing Standards
- No emojis
- Use tables for all field definitions
- Include Go types for clarity
- Organize by CRD with clear headers
