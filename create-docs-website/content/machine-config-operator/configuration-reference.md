# Configuration Reference

> **Hosted Control Plane (HyperShift) clusters:** On clusters with `controlPlaneTopology: External`, the core MCO CRDs -- MachineConfig, MachineConfigPool, KubeletConfig, and ContainerRuntimeConfig -- are not available on the hosted cluster API. Node Disruption Policy (MachineConfiguration), MachineOSConfig, and PinnedImageSet CRDs remain available. Check your topology with `oc get infrastructure cluster -o jsonpath='{.status.controlPlaneTopology}'`.

## MachineConfig

### Spec Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `config` | Ignition Config (RawExtension) | No | — | Ignition v3.2.0+ configuration object. Contains files, systemd units, and passwd entries. |
| `kernelArguments` | []string | No | — | Kernel arguments to add to the node bootloader. |
| `extensions` | []string | No | — | Additional RHCOS extensions to enable (e.g., `usbguard`, `sandboxed-containers`). |
| `fips` | bool | No | false | Enable FIPS 140-2 mode on the node. |
| `kernelType` | string | No | `default` | Kernel type: `default`, `realtime`, or `64k-pages` (aarch64 only). |
| `osImageURL` | string | No | — | Override OS image URL for this config (advanced use). |
| `baseOSExtensionsContainerImage` | string | No | — | Override extensions container image. |

### Labels
MachineConfigs use the label `machineconfiguration.openshift.io/role` to target a pool:
- `worker` — applies to worker pool
- `master` — applies to master pool
- Custom values for custom pools

### Ignition Config Structure
Brief explanation of the Ignition config structure within `spec.config`:
- `storage.files[]` — Files to write (path, contents as data URI or base64, mode, overwrite)
- `systemd.units[]` — Systemd units (name, enabled, contents, dropins)
- `passwd.users[]` — User configuration (only `core` user SSH keys supported)

### Naming Convention
- User-created: Use `99-<role>-<description>` format (e.g., `99-worker-chrony`)
- Platform-generated: Use `00-<role>` or `01-<role>-<component>` format
- Rendered: Auto-generated with `rendered-<role>-<hash>` format
- MachineConfigs are merged in lexicographic order by name

---

## MachineConfigPool

### Spec Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `machineConfigSelector` | LabelSelector | No | — | Selects which MachineConfigs apply to this pool. |
| `nodeSelector` | LabelSelector | No | — | Selects which nodes belong to this pool. |
| `paused` | bool | No | false | Pauses all updates to the pool. |
| `maxUnavailable` | IntOrString | No | 1 | Maximum nodes that can be unavailable during update. Can be a number or percentage. Cannot be 0. |
| `pinnedImageSets` | []PinnedImageSetRef | No | — | References to PinnedImageSet objects for image preloading (max 100). |

### Status Fields

| Field | Type | Description |
|-------|------|-------------|
| `configuration` | object | Current rendered MachineConfig for the pool. |
| `machineCount` | int32 | Total machines in the pool. |
| `updatedMachineCount` | int32 | Machines running the current rendered config. |
| `readyMachineCount` | int32 | Machines that are Ready. |
| `unavailableMachineCount` | int32 | Machines not Ready. |
| `degradedMachineCount` | int32 | Machines in degraded state. |
| `conditions` | []Condition | Pool conditions (Updated, Updating, Degraded, NodeDegraded, RenderDegraded). |

### Default Pools
- **master** — Selects MachineConfigs with label `machineconfiguration.openshift.io/role: master` and nodes with `node-role.kubernetes.io/master`
- **worker** — Selects MachineConfigs with label `machineconfiguration.openshift.io/role: worker` and nodes with `node-role.kubernetes.io/worker`

---

## KubeletConfig

Customizes the kubelet configuration for nodes in targeted pools.

### Spec Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `machineConfigPoolSelector` | LabelSelector | No | — | Selects which pools this config applies to. |
| `kubeletConfig` | object (RawExtension) | No | — | Upstream Kubernetes kubelet configuration fields. Validated by kubelet. |
| `autoSizingReserved` | *bool | No | true (workers), false (control plane) | Auto-calculate system-reserved CPU/memory based on node capacity. |
| `logLevel` | *int32 | No | 2 | Kubelet log verbosity (0-10). |
| `tlsSecurityProfile` | TLSSecurityProfile | No | From apiservers.config.openshift.io/cluster | TLS settings. Types: Old, Intermediate, Modern, Custom. |

### Example: Setting maxPods
```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: KubeletConfig
metadata:
  name: set-max-pods
spec:
  machineConfigPoolSelector:
    matchLabels:
      pools.operator.machineconfiguration.openshift.io/worker: ""
  kubeletConfig:
    maxPods: 500
```

### Example: Setting system reserved resources
```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: KubeletConfig
metadata:
  name: set-system-reserved
spec:
  machineConfigPoolSelector:
    matchLabels:
      pools.operator.machineconfiguration.openshift.io/worker: ""
  kubeletConfig:
    systemReserved:
      cpu: 500m
      memory: 512Mi
    kubeReserved:
      cpu: 500m
      memory: 512Mi
  autoSizingReserved: false
```

---

## ContainerRuntimeConfig

Customizes CRI-O container runtime configuration.

### Spec Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `machineConfigPoolSelector` | LabelSelector | No | — | Selects which pools this config applies to. |
| `containerRuntimeConfig` | ContainerRuntimeConfiguration | No | — | CRI-O runtime configuration fields. |

### ContainerRuntimeConfiguration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pidsLimit` | *int64 | — | Maximum number of processes per container. |
| `logLevel` | string | — | CRI-O log verbosity: fatal, panic, error, warn, info, debug. |
| `logSizeMax` | Quantity | — | Max container log file size. Must be >= 8192 bytes if positive. Negative value = unlimited. |
| `overlaySize` | Quantity | 10GB | Max container image size quota. |
| `defaultRuntime` | string | crun | Default OCI runtime: `crun` or `runc`. |
| `additionalLayerStores` | []AdditionalLayerStore | — | Read-only container image layer store locations (max 5). Requires AdditionalStorageConfig feature gate. |
| `additionalImageStores` | []AdditionalImageStore | — | Read-only container image store locations (max 10). Requires AdditionalStorageConfig feature gate. |
| `additionalArtifactStores` | []AdditionalArtifactStore | — | Read-only OCI artifact store locations (max 10). Requires AdditionalStorageConfig feature gate. |

**Important:** An empty `machineConfigPoolSelector` (`{}`) selects no pools, not all pools. You must specify labels to match.

### Example: Setting pids limit
```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: ContainerRuntimeConfig
metadata:
  name: set-pids-limit
spec:
  machineConfigPoolSelector:
    matchLabels:
      pools.operator.machineconfiguration.openshift.io/worker: ""
  containerRuntimeConfig:
    pidsLimit: 4096
    logLevel: warn
    logSizeMax: "50Mi"
```

---

## Node Disruption Policy (MachineConfiguration)

The MachineConfiguration CR (`operator.openshift.io/v1`) allows fine-grained control over how MachineConfig changes affect nodes. This is a singleton resource that must be named `cluster`.

### Spec Fields (nodeDisruptionPolicy)

| Field | Type | Description |
|-------|------|-------------|
| `files` | []NodeDisruptionPolicySpecFile | File-based policies (max 50). |
| `units` | []NodeDisruptionPolicySpecUnit | Systemd unit policies (max 50). |
| `sshkey` | NodeDisruptionPolicySpecSSHKey | SSH key change policies. |

### Supported Actions

| Action | Description |
|--------|-------------|
| `None` | No action needed — change applied in place. |
| `Drain` | Drain node workloads and reboot. |
| `Reload` | Reload a specific systemd service (`systemctl reload`). |
| `Restart` | Restart a specific systemd service (`systemctl restart`). |
| `DaemonReload` | Reload systemd manager configuration (`systemctl daemon-reload`). |
| `Reboot` | Full drain and reboot (default for unspecified changes). |
| `Special` | Internal MCO action (cannot be set by users, appears in status only). |

### Default Cluster Policies (built-in)
| Change | Default Action |
|--------|---------------|
| Pull secrets (`/var/lib/kubelet/config.json`) | None |
| SSH keys | None |
| Container GPG keys | Reload crio |
| Container policies (`policy.json`) | Reload crio |
| Registry configuration (`/etc/containers/registries.conf`) | Special (internal MCO handling) |
| Registry sigstore configs (`/etc/containers/registries.d/`) | Reload crio |
| NMState config (`/etc/nmstate/openshift/`) | None |
| CA bundle | Restart crio + coreos-update-ca-trust |

### Example: Custom disruption policy
```yaml
apiVersion: operator.openshift.io/v1
kind: MachineConfiguration
metadata:
  name: cluster
spec:
  nodeDisruptionPolicy:
    files:
      - path: /etc/my-app/config.json
        actions:
          - type: None
      - path: /etc/my-app/daemon.conf
        actions:
          - type: Restart
            restart:
              serviceName: my-app.service
    units:
      - name: my-app.service
        actions:
          - type: DaemonReload
    sshkey:
      actions:
        - type: None
```

---

## On-Cluster Layering (MachineOSConfig)

Available since OpenShift 4.16+ with TechPreviewNoUpgrade feature gate enabled. Allows building custom OS images using Containerfile syntax on the cluster.

### MachineOSConfig Spec Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `machineConfigPool` | MachineConfigPoolReference | Yes | The pool to build for. Name must match the MachineOSConfig name. |
| `imageBuilder` | MachineOSImageBuilder | Yes | Image builder backend. Currently only `Job` type supported. |
| `baseImagePullSecret` | ImageSecretObjectReference | No | Secret for pulling base OS image (in openshift-machine-config-operator namespace). |
| `renderedImagePushSecret` | ImageSecretObjectReference | Yes | Secret for pushing the built image. |
| `renderedImagePushSpec` | string | Yes | Registry location for the final image (e.g., `registry.example.com/my-os:latest`). |
| `containerFile` | []MachineOSContainerfile | No | Custom Containerfile content per architecture (max 4 entries, max 4096 chars each). |

### Containerfile Architectures
- `NoArch` (default) — Architecture-independent
- `AMD64`
- `ARM64`
- `PPC64LE`
- `S390X`

### Example
```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: MachineOSConfig
metadata:
  name: worker
spec:
  machineConfigPool:
    name: worker
  imageBuilder:
    imageBuilderType: Job
  renderedImagePushSecret:
    name: my-registry-secret
  renderedImagePushSpec: registry.example.com/custom-rhcos:latest
  containerFile:
    - containerfileArch: NoArch
      content: |
        FROM configs AS machineconfig
        FROM base AS final
        RUN rpm -ivh https://example.com/my-package.rpm
```

---

## PinnedImageSet

Preload container images to nodes for faster pod startup.

### Spec Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pinnedImages` | []PinnedImageRef | Yes | OCI images to pin (1-500 images, must use digest format). |

### Example
```yaml
apiVersion: machineconfiguration.openshift.io/v1
kind: PinnedImageSet
metadata:
  name: my-pinned-images
spec:
  pinnedImages:
    - name: quay.io/my-org/my-app@sha256:abc123...
    - name: quay.io/my-org/my-sidecar@sha256:def456...
```

Reference the PinnedImageSet from a MachineConfigPool:
```yaml
spec:
  pinnedImageSets:
    - name: my-pinned-images
```

---

## Node Annotations

Key annotations set by the MCO on nodes:

| Annotation | Description |
|-----------|-------------|
| `machineconfiguration.openshift.io/currentConfig` | Currently applied MachineConfig name. |
| `machineconfiguration.openshift.io/desiredConfig` | Target MachineConfig name. |
| `machineconfiguration.openshift.io/state` | Daemon state: Done, Working, Degraded, Rebooting, Unreconcilable. |
| `machineconfiguration.openshift.io/reason` | Human-readable reason for current state. |
| `machineconfiguration.openshift.io/currentImage` | Current OS image pullspec. |
| `machineconfiguration.openshift.io/desiredImage` | Target OS image pullspec. |

---

## Environment Variables

| Variable | Used By | Description |
|----------|---------|-------------|
| `NODE_NAME` | MCD | Kubernetes node name (fallback for `--node-name` flag). |

---

## Related Documentation
- [Getting Started](getting-started.md) — Quick start guide
- [API Reference](api-reference.md) — Complete CRD field reference
- [Troubleshooting](troubleshooting.md) — Diagnostic steps and common issues
- [Examples](examples/) — Example YAML manifests

## Writing Standards
- No emojis
- Use tables for all reference data
- Include working YAML examples with every CRD section
- Cross-link to other docs with relative links
