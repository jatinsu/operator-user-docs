---
name: okd-branding
description: Convert OpenShift Container Platform documentation to OKD branding. Applies all product name, URL, OS, operator, registry, support, and feature substitutions derived from the official openshift-docs conditional system.
argument-hint: "[source-dir] [file-or-directory] [--dry-run] [--check]"
---

You are an expert at converting OpenShift Container Platform (OCP) documentation into OKD documentation. You know every branding rule derived from the official `openshift-docs` repository's conditional system (`ifdef::openshift-origin`, attribute overrides, distro maps, and topic maps).

## Arguments

- `source-dir` (optional): Path to the source repository/codebase directory to use as context when converting documentation. Defaults to the current working directory. Use this when the repository being documented is in a different location from the docs.
- `file-or-directory` (optional): Path to a file or directory of docs to convert. Defaults to current directory.
- `--dry-run`: Show what would change without modifying files.
- `--check`: Validate existing docs for missed OCP references that should be OKD.

Parse from: $ARGUMENTS

If `source-dir` is provided, use it as the root directory for reading source code context (CRDs, Go structs, API types, configuration) that informs branding decisions. The `file-or-directory` argument still controls which documentation files are converted.

## How to Use This Skill

When given documentation text that was written for OpenShift Container Platform, apply ALL of the rules below to produce the OKD equivalent. Work systematically through each category. If `--check` is passed, scan and report violations without changing anything.

---

## COMPLETE BRANDING RULES: OpenShift Container Platform → OKD

These rules are exhaustive — derived from every `ifdef::openshift-origin` / `ifndef::openshift-origin` block, every attribute override, and every conditional content pattern across the entire `openshift-docs` repository (778+ files, 175+ modules).

---

### CATEGORY 1: Product Names

| OCP Value                        | OKD Value | Notes                                                                                                                     |
| -------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------- |
| OpenShift Container Platform     | OKD       | The primary product name (`{product-title}`)                                                                              |
| OpenShift Container Platform X.Y | OKD X.Y   | Version follows the same pattern                                                                                          |
| {product-title}                  | OKD       | When rendered                                                                                                             |
| OpenShift                        | OKD       | ONLY when referring to the platform itself, NOT when part of a sub-product name like "OpenShift CLI" which stays the same |

**Important:** The word "OpenShift" in sub-product names does NOT always change. See Category 3 for which sub-products change and which don't.

---

### CATEGORY 2: Operating System References

| OCP Value                               | OKD Value            | Attribute               |
| --------------------------------------- | -------------------- | ----------------------- |
| Red Hat Enterprise Linux CoreOS (RHCOS) | Stream CoreOS (SCOS) | `{op-system-first}`     |
| RHCOS                                   | SCOS                 | `{op-system}`           |
| rhcos                                   | scos                 | `{op-system-lowercase}` |
| RHEL                                    | Stream CoreOS        | `{op-system-base}`      |
| Red Hat Enterprise Linux (RHEL)         | Stream CoreOS        | `{op-system-base-full}` |
| 9.x                                     | 35                   | `{op-system-version}`   |

**Apply everywhere** these OS names appear — in prose, prerequisites, system requirements, commands, YAML examples, and file paths.

Example transformation:

- OCP: "One provisioner node with Red Hat Enterprise Linux (RHEL) 9.x installed"
- OKD: "One provisioner node with Stream CoreOS (SCOS) installed"

---

### CATEGORY 3: Sub-Product and Component Names

These sub-products have EXPLICIT OKD overrides in the attribute system:

| OCP Value                          | OKD Value                                | Attribute                              |
| ---------------------------------- | ---------------------------------------- | -------------------------------------- |
| OpenShift Virtualization           | OKD Virtualization                       | `{VirtProductName}`                    |
| OpenShift Virtualization Operator  | KubeVirt HyperConverged Cluster Operator | `{CNVOperatorDisplayName}`             |
| Builds for Red Hat OpenShift       | Shipwright                               | `{builds-v2title}`                     |
| OpenShift Builds v2                | Shipwright                               | `{builds-v2shortname}`                 |
| OpenShift Builds v1                | Builds v1                                | `{builds-v1shortname}`                 |
| Red Hat OpenStack Platform (RHOSP) | OpenStack                                | `{rh-openstack-first}`                 |
| RHOSP                              | OpenStack                                | `{rh-openstack}`                       |
| single-node OpenShift              | single-node OKD                          | `{sno-okd}` replaces `{sno}`           |
| Single-node OpenShift              | Single-node OKD                          | `{sno-caps-okd}` replaces `{sno-caps}` |

These sub-products DO NOT change for OKD (keep the OCP name):

| Product Name                                   | Stays the Same? | Notes                                                                  |
| ---------------------------------------------- | --------------- | ---------------------------------------------------------------------- |
| OpenShift CLI (`oc`)                           | YES             | CLI tool name unchanged                                                |
| OpenShift Cluster Manager                      | YES             | But URLs change (see Category 5)                                       |
| Red Hat OpenShift GitOps                       | YES             | Attribute unchanged                                                    |
| Red Hat OpenShift Pipelines                    | YES             | Attribute unchanged                                                    |
| OpenShift Serverless                           | YES             | Attribute unchanged                                                    |
| Red Hat OpenShift Service Mesh                 | YES             | Attribute unchanged                                                    |
| Red Hat OpenShift Distributed Tracing Platform | YES             | Attribute unchanged                                                    |
| Red Hat OpenShift Logging                      | YES             | Attribute unchanged                                                    |
| Red Hat OpenShift Data Foundation              | YES             | Attribute unchanged                                                    |
| OpenShift API for Data Protection (OADP)       | YES             | Attribute unchanged                                                    |
| OpenShift image registry                       | YES             | Attribute unchanged                                                    |
| Red Hat OpenShift Networking                   | YES             | Has a TODO for OKD override ("OKD Networking") but NOT yet implemented |
| Red Hat OpenShift Lightspeed                   | YES             | Attribute unchanged                                                    |
| OpenShift Kubernetes Engine                    | YES             | OCP-only product                                                       |

---

### CATEGORY 4: Operator and Namespace Technical Values

| OCP Value                 | OKD Value                           | Context                                                           |
| ------------------------- | ----------------------------------- | ----------------------------------------------------------------- |
| `openshift-cnv`           | `kubevirt-hyperconverged`           | CNV namespace (`{CNVNamespace}`)                                  |
| `redhat-operators`        | `community-operators`               | Catalog source for virtualization (`{CNVSubscriptionSpecSource}`) |
| `kubevirt-hyperconverged` | `community-kubevirt-hyperconverged` | Subscription name (`{CNVSubscriptionSpecName}`)                   |

**General rule for operator catalog sources:** When documentation references `redhat-operators` as a catalog source in a Subscription YAML, for OKD this becomes `community-operators` UNLESS the OKD user has explicitly configured the Red Hat pull secret (in which case `redhat-operators` is also valid but requires extra setup steps).

When converting operator installation docs, add this OKD-specific note:

> If you have the pull secret, add the `redhat-operators` catalog to the OperatorHub custom resource (CR) as shown in "Configuring OKD to use Red Hat Operators".

---

### CATEGORY 5: URLs and Download Locations

| Context                        | OCP URL                                                                                          | OKD URL                                                                               |
| ------------------------------ | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| Installation program download  | `console.redhat.com/openshift/install` → "Cluster Type page on the Red Hat Hybrid Cloud Console" | `https://github.com/okd-project/okd/releases`                                         |
| CLI (`oc`) download            | `access.redhat.com/downloads/content/290` → "Red Hat Customer Portal"                            | `https://mirror.openshift.com/pub/openshift-v4/clients/oc/latest/`                    |
| Release binaries               | `mirror.openshift.com/pub/openshift-v4/clients/ocp/`                                             | `https://github.com/okd-project/okd/releases`                                         |
| Pull secret                    | `console.redhat.com/openshift/install/pull-secret` (required)                                    | Same URL but OPTIONAL (see Category 7)                                                |
| Customer Portal                | `access.redhat.com/...`                                                                          | Remove or replace — not available for OKD                                             |
| Cluster registration           | `console.redhat.com/openshift/register`                                                          | Remove — not applicable                                                               |
| Red Hat Ecosystem Catalog      | `catalog.redhat.com/software/containers/explore`                                                 | Note: content not available without pull secret                                       |
| OpenID Connect provider docs   | `access.redhat.com/documentation/.../red_hat_single_sign-on/` ("Red Hat Single Sign-On")         | `https://www.keycloak.org/docs/latest/server_admin/index.html#openshift` ("Keycloak") |
| Red Hat support/knowledge base | Any `access.redhat.com/solutions/...` or `access.redhat.com/articles/...`                        | Remove or note as "Red Hat subscription required"                                     |

---

### CATEGORY 6: Registry and Release Image References

| Context                     | OCP Value                                                                | OKD Value                                                                         |
| --------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------- |
| Product repository variable | `PRODUCT_REPO='openshift-release-dev'`                                   | `PRODUCT_REPO='okd'`                                                              |
| Release name variable       | `RELEASE_NAME="ocp-release"`                                             | `RELEASE_NAME="scos-release"`                                                     |
| Release image tag format    | `quay.io/${PRODUCT_REPO}/${RELEASE_NAME}:${OCP_RELEASE}-${ARCHITECTURE}` | `quay.io/${PRODUCT_REPO}/${RELEASE_NAME}:${OCP_RELEASE}` (NO architecture suffix) |
| Mirror command              | Includes `-${ARCHITECTURE}` in tag                                       | NO `-${ARCHITECTURE}` suffix                                                      |
| Extract command             | Includes `-${ARCHITECTURE}` in tag                                       | NO `-${ARCHITECTURE}` suffix                                                      |
| Container image registry    | `registry.redhat.io/...`                                                 | Not available without pull secret — note this                                     |
| Red Hat container catalog   | Available                                                                | Not available without pull secret                                                 |

**Critical:** OKD release image tags do NOT include an architecture suffix. Every `oc adm release mirror` and `oc adm release extract` command that appends `-${ARCHITECTURE}` to the tag must have that suffix removed for OKD.

#### Per-Module Container Image Overrides

Individual modules define local attribute overrides that swap Red Hat container images for community equivalents. These are NOT in `common-attributes.adoc` — they live inside the module files themselves:

| Context                          | OCP Image                                                                      | OKD Image                                                      |
| -------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| OLM operator registry base image | `registry.redhat.io/openshift4/ose-operator-registry-rhel9:v{product-version}` | `quay.io/operator-framework/opm:latest`                        |
| OLM catalog index image          | `registry.redhat.io/redhat/redhat-operator-index:v{product-version}`           | `quay.io/operatorhubio/catalog:latest`                         |
| OLM catalog index name           | `redhat-operator-index`                                                        | `catalog`                                                      |
| OLM catalog name                 | `redhat-operators`                                                             | `catalog`                                                      |
| OLM pruning registry image       | `registry.redhat.io/openshift4/ose-operator-registry-rhel9:v{product-version}` | `quay.io/openshift/origin-operator-registry:{product-version}` |
| OLM example packages             | `advanced-cluster-management`, `jaeger-product`, `quay-operator`               | `couchdb-operator`, `eclipse-che`, `etcd`                      |
| Network tools image              | `registry.redhat.io/openshift4/network-tools-rhel8`                            | `quay.io/openshift/origin-network-tools:latest`                |
| Egress router pod image          | `registry.redhat.io/openshift3/ose-pod`                                        | `quay.io/openshift/origin-pod`                                 |
| Cluster logging must-gather      | Extracted from cluster-logging-operator deployment                             | `quay.io/openshift/origin-cluster-logging-operator`            |

**OKD must-gather images** use entirely different community image references:

| Feature              | OKD Must-Gather Image                                   |
| -------------------- | ------------------------------------------------------- |
| KubeVirt             | `quay.io/kubevirt/must-gather`                          |
| Knative (Serverless) | `quay.io/openshift-knative/must-gather`                 |
| Service Mesh         | `docker.io/maistra/istio-must-gather`                   |
| Migration Toolkit    | `quay.io/konveyor/must-gather`                          |
| OCS/ODF Storage      | `quay.io/ocs-dev/ocs-must-gather`                       |
| Logging              | `quay.io/openshift/origin-cluster-logging-operator`     |
| Local Storage        | `quay.io/openshift/origin-local-storage-mustgather`     |
| Secrets Store CSI    | `quay.io/openshift/origin-secrets-store-csi-mustgather` |

**OLM `opm` command difference:**

- OCP: `opm generate dockerfile <catalog_dir> -i {registry-image}` (with `-i` flag to specify base image)
- OKD: `opm generate dockerfile <catalog_dir>` (no `-i` flag — uses default)

---

### CATEGORY 7: Pull Secret Handling

OKD has fundamentally different pull secret requirements:

**OCP behavior:** Pull secret from `console.redhat.com` is REQUIRED. It authenticates with `registry.redhat.io`, `quay.io`, and Red Hat services.

**OKD behavior:** Pull secret is OPTIONAL. When writing OKD docs:

1. State that a pull secret from Red Hat is not required
2. Mention that users can use a pull secret for another private registry
3. Include this alternative: users can use `{"auths":{"fake":{"auth":"aWQ6cGFzcwo="}}}` as the pull secret when prompted
4. Document what is lost without the Red Hat pull secret:
   - Red Hat Operators are not available
   - The Telemetry and Insights Operators do not send data to Red Hat
   - Content from the Red Hat Ecosystem Catalog Container images registry (image streams and Operators) is not available

For mirror registry setup:

- OCP: "You downloaded the pull secret from Red Hat OpenShift Cluster Manager"
- OKD: "You have created a pull secret for your mirror repository"

For adding registry pull secrets:

- OCP: Download from `console.redhat.com`, edit the existing JSON
- OKD: Create a new `.json` file from scratch with custom registry credentials

---

### CATEGORY 8: Telemetry, Support, and Subscription References

**Remove or rewrite entirely for OKD:**

| OCP Content                                           | OKD Action                                   |
| ----------------------------------------------------- | -------------------------------------------- |
| "Telemetry access for {product-title}" sections       | Remove entire section                        |
| "registers your cluster to OpenShift Cluster Manager" | Remove                                       |
| "use subscription watch to track your subscriptions"  | Remove                                       |
| References to Red Hat Support or support cases        | Replace with community support or remove     |
| "provide diagnostic information to Red Hat Support"   | Replace with "debugging or admin tools"      |
| Cluster registration steps                            | Remove                                       |
| Subscription requirements                             | Remove                                       |
| "you must have an active subscription"                | Remove                                       |
| Insights Operator sending data to Red Hat             | Note: does not send data without pull secret |

**toolbox description transformation:**

- OCP: "primarily used to start a container for gathering diagnostic information and providing it to Red Hat Support" (references `sosreport` command)
- OKD: "primarily used to start a container that includes required binaries and packages for your favorite debugging or admin tools" (no `sosreport` reference)

**Audit log must-gather upload:**

- OCP: Section about creating a compressed file and attaching it to a support case on the Red Hat Customer Portal
- OKD: Remove entire upload-to-support-case section

**`subscription-manager` steps:**

- OCP IPI provisioner setup includes `subscription-manager register` and `subscription-manager repos` steps
- OKD: Remove entire subscription-manager registration block — not applicable

---

### CATEGORY 9: FIPS Mode

**Remove all FIPS content for OKD:**

- Remove `fips: false` / `fips: true` from YAML examples
- Remove FIPS parameter descriptions ("Specifies either enabling or disabling FIPS mode...")
- Remove FIPS-related notes about cryptographic modules
- Remove any "RHCOS machines bypass the default Kubernetes cryptography suite" content
- Remove FIPS prerequisites sections

FIPS is an enterprise feature tied to Red Hat's certified cryptographic modules and is not applicable to OKD.

---

### CATEGORY 10: Architecture Support Limitations

When documenting platform architecture support for OKD:

| Context                            | OCP Value                            | OKD Value     |
| ---------------------------------- | ------------------------------------ | ------------- |
| Compute machine architecture       | `amd64`, `arm64`, `ppc64le`, `s390x` | `amd64` only  |
| Control plane architecture         | `amd64`, `arm64`, `ppc64le`, `s390x` | `amd64` only  |
| Mixed/varied architecture clusters | Supported                            | Not supported |

Replace multi-architecture lists with: "The valid value is the default: `amd64`"

Add note: "Currently, clusters with varied architectures are not supported on OKD."

**IPI-specific architecture naming:** In IPI (bare metal) docs, architecture uses `x86_64`/`aarch64` naming instead of `amd64`/`arm64`. For OKD, remove `aarch64` — only `x86_64` is supported.

---

### CATEGORY 11: Installation Configuration (install-config.yaml)

When converting install-config.yaml examples:

1. **Remove FIPS field** (`fips: false` / `fips: true`)
2. **Change pull secret references** from Red Hat pull secret to user-created pull secret
3. **Change OS references** in comments (RHCOS → SCOS, RHEL → Stream CoreOS)
4. **Remove architecture fields** for multi-arch (keep only amd64 or remove the field)
5. **Change image references** if they reference `registry.redhat.io`

---

### CATEGORY 12: Diagrams and Images

Some diagrams differ between OCP and OKD:

| Context                                | OCP Image          | OKD Image                                             |
| -------------------------------------- | ------------------ | ----------------------------------------------------- |
| Installation process bootstrap diagram | `create-nodes.png` | `150_OpenShift_VMware_on_AWS_1021_installer_FCOS.png` |

When generating docs, note if diagrams reference RHCOS — they should reference SCOS for OKD.

---

### CATEGORY 13: Update Channels

OKD has a fundamentally simpler update channel model:

| OCP Channels                        | OKD Channel                 |
| ----------------------------------- | --------------------------- |
| `fast-{product-version}`            | `stable-4` (single channel) |
| `stable-{product-version}`          | `stable-4`                  |
| `candidate-{product-version}`       | `stable-4`                  |
| `eus-4.y` (Extended Update Support) | Not available               |

- OKD uses only ONE update channel: `stable-4`
- EUS (Extended Update Support) is entirely OCP-only — remove all EUS sections, references, and the `eus-4.y` channel
- Remove references to switching between `fast`, `stable`, and `candidate` channels
- Remove the EUS terminology section from API compatibility docs

---

### CATEGORY 14: SNO Installation Specifics

When converting single-node OpenShift installation docs, several technical values change beyond just the product name:

| Context                | OCP Value                                                                                        | OKD Value                                                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Install directory      | `--dir=ocp` / `mkdir ocp`                                                                        | `--dir=sno` / `mkdir sno`                                                                                       |
| ISO filename           | `rhcos-live.iso`                                                                                 | `fcos-live.iso`                                                                                                 |
| Version variable name  | `OCP_RELEASE=<ocp_version>`                                                                      | `OKD_VERSION=<okd_version>`                                                                                     |
| Version example value  | `latest-{product-version}`                                                                       | `4.14.0-0.okd-2024-01-26-175629`                                                                                |
| Client download URL    | Red Hat console                                                                                  | `https://github.com/okd-project/okd/releases/download/$OKD_VERSION/openshift-client-linux-$OKD_VERSION.tar.gz`  |
| Installer download URL | Red Hat console                                                                                  | `https://github.com/okd-project/okd/releases/download/$OKD_VERSION/openshift-install-linux-$OKD_VERSION.tar.gz` |
| Ignition embed command | `coreos-installer iso ignition embed -fi ocp/bootstrap-in-place-for-live-iso.ign rhcos-live.iso` | `coreos-installer iso ignition embed -fi sno/bootstrap-in-place-for-live-iso.ign fcos-live.iso`                 |

---

### CATEGORY 15: Content That Is OCP-Only (Remove for OKD)

These features/sections exist ONLY in OCP docs and should be removed or marked as not applicable for OKD:

- OpenShift Kubernetes Engine (OKE) overview
- FIPS mode configuration
- Red Hat Marketplace operators
- Certified Operators catalog
- Red Hat subscription tracking
- Telemetry access sections
- Cluster registration with Red Hat
- Red Hat Customer Portal download instructions
- Red Hat support case references
- Glossary entry for OKE
- EUS (Extended Update Support) — entire concept and all sections
- `fast-{product-version}` and `candidate-{product-version}` update channel documentation
- AWS `platform.aws.lbType` configuration parameter
- AWS Graviton processor regional availability notes
- `subscription-manager register` / `subscription-manager repos` steps in IPI provisioner setup
- Must-gather upload to Red Hat Customer Portal instructions
- `sosreport` diagnostic tool references

---

### CATEGORY 16: Content That Is OKD-Only (Add for OKD)

These items appear ONLY in OKD docs:

- "Understanding OKD development" topic (architecture section)
- "Stream CoreOS" topic (instead of "Red Hat Enterprise Linux CoreOS")
- Keycloak as OpenID Connect identity provider (instead of Red Hat SSO)
- Fake pull secret option: `{"auths":{"fake":{"auth":"aWQ6cGFzcwo="}}}`
- Instructions for adding `redhat-operators` catalog manually (optional, requires pull secret)
- OKD-specific installer download from GitHub releases (`https://github.com/okd-project/okd/releases`)
- OKD-specific CLI download from mirror.openshift.com
- Community must-gather images (see Category 6 table)
- `OKD_VERSION` variable naming pattern (instead of `OCP_RELEASE`)

---

### CATEGORY 17: Networking Plugin Descriptions

| Context                    | OCP Value                                                                                                                                                                                | OKD Value                               |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| OVN-Kubernetes description | "`OVNKubernetes` is a Container Network Interface (CNI) plugin for Linux networks and hybrid networks that contain both Linux and Windows servers. The default value is `OVNKubernetes`" | "`OVNKubernetes`" (minimal description) |

---

### CATEGORY 18: Attributes Without OKD Overrides (Watch For)

These attributes exist in `common-attributes.adoc` with Red Hat branding but have NO `ifdef::openshift-origin` override. If they appear in content you are converting, flag them:

| Attribute                | Current Value                  | OKD Issue                                                                                                               |
| ------------------------ | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------- |
| `{op-system-version-9}`  | `9`                            | No OKD override — would still show "9" in Stream CoreOS context. Drop or replace with Stream CoreOS version.            |
| `{op-system-ai}`         | `Red Hat Enterprise Linux AI`  | No OKD override — not applicable to OKD. Remove references.                                                             |
| `{openshift-networking}` | `Red Hat OpenShift Networking` | Has a TODO for "OKD Networking" but not yet implemented. Keep as-is or use "OKD Networking" if the upstream TODO lands. |

---

### CATEGORY 19: Red Hat Branding Patterns to Watch For

These are hardcoded Red Hat references that appear outside the attribute system and need manual conversion:

| Pattern                                      | Action                                   |
| -------------------------------------------- | ---------------------------------------- |
| `Red{nbsp}Hat` or `Red Hat` in product names | Apply rules from Categories 1-3          |
| `console.redhat.com` URLs                    | Apply rules from Category 5              |
| `access.redhat.com` URLs                     | Apply rules from Category 5              |
| `registry.redhat.io` image references        | Note as unavailable without pull secret  |
| "Red Hat account"                            | Remove or replace with "an account"      |
| "Red Hat credentials"                        | Remove or replace                        |
| "Red Hat Hybrid Cloud Console"               | Remove or replace with direct URL/action |
| "Red Hat Customer Portal"                    | Remove — not available                   |

---

## CONVERSION PROCEDURE

When converting a document, work through these steps in order:

### Step 1: Product Name Sweep

Replace all instances of "OpenShift Container Platform" with "OKD". Be careful NOT to replace "OpenShift" when it's part of a sub-product name that doesn't change (see Category 3).

### Step 2: OS Name Sweep

Replace all RHCOS → SCOS, RHEL → Stream CoreOS references (see Category 2).

### Step 3: Sub-Product Name Sweep

Apply the sub-product name changes from Category 3 (Virtualization, Builds, OpenStack, SNO).

### Step 4: Technical Values Sweep

Update namespaces, catalog sources, subscription names, container image references, and registry references (Categories 4, 6). Pay special attention to per-module image overrides (OLM, network-tools, egress-router, must-gather).

### Step 5: URL Sweep

Replace all download URLs, support URLs, and documentation links (Category 5). Use `okd-project/okd` (not `openshift/okd`) for GitHub URLs.

### Step 6: Pull Secret Sweep

Rewrite pull secret handling to make it optional (Category 7).

### Step 7: Remove Enterprise-Only Content

Remove FIPS, telemetry, EUS, subscription tracking, Red Hat Support references, `subscription-manager` steps, AWS-specific OCP parameters (Categories 8, 9, 13, 15).

### Step 8: Architecture Sweep

Limit architecture references to amd64/x86_64 only (Category 10).

### Step 9: Update Channel Sweep

Replace multi-channel documentation with single `stable-4` channel (Category 13).

### Step 10: SNO-Specific Sweep

Update directory names (`ocp` → `sno`), ISO filenames (`rhcos-live.iso` → `fcos-live.iso`), version variables (`OCP_RELEASE` → `OKD_VERSION`), and download URLs (Category 14).

### Step 11: Add OKD-Only Content

Add Keycloak references, fake pull secret option, GitHub download links, community must-gather images (Category 16).

### Step 12: Final Validation

Scan for any remaining:

- "Red Hat" references that should have been converted
- `console.redhat.com` or `access.redhat.com` URLs
- `registry.redhat.io` references without caveat or image swap
- `RHCOS` or `RHEL` references
- `redhat-operators` without OKD context
- FIPS references
- EUS references
- `fast-` or `candidate-` update channel references
- `rhcos-live.iso` or `--dir=ocp` in SNO content
- `OCP_RELEASE` variable names (should be `OKD_VERSION`)
- `openshift/okd` GitHub URLs (should be `okd-project/okd`)
- Unoverridden attributes (`{op-system-version-9}`, `{op-system-ai}`) — see Category 18

---

## EDGE CASES AND GOTCHAS

1. **"OpenShift" in CLI names stays:** "OpenShift CLI (`oc`)" is the same for OKD
2. **`{product-title}` in links:** When the attribute appears inside a link text, it still resolves to "OKD"
3. **Version numbering:** OKD uses the same version numbers as OCP (4.x) but the "latest" build from `main` branch shows version as just "4"
4. **Conditional operator access:** OKD users CAN access `redhat-operators` IF they have the pull secret — document both paths
5. **`{sno}` vs `{sno-okd}`:** In OKD docs, use "single-node OKD" not "single-node OpenShift"
6. **`Red{nbsp}Hat`:** In AsciiDoc, `{nbsp}` is a non-breaking space. In markdown/plaintext output, just use "Red Hat" and then apply the substitution rules
7. **Nested conditionals:** Some content is conditioned on BOTH distro AND assembly context. When converting, the distro condition is the one that determines OKD branding
8. **Images/diagrams:** Some diagrams are distro-specific. If a diagram shows "RHCOS", the OKD version should show "SCOS"
9. **`openshift-networking` TODO:** The attribute for Red Hat OpenShift Networking has an incomplete TODO to add an OKD override ("OKD Networking"). Currently it stays as "Red Hat OpenShift Networking" — follow whatever the upstream docs settle on
10. **Release image architecture suffix:** This is the most commonly missed technical difference. OCP tags: `4.22.0-x86_64`. OKD tags: `4.22.0` (no suffix)
11. **GitHub org name:** The correct OKD GitHub org is `okd-project` (not `openshift`). URLs should be `https://github.com/okd-project/okd/releases`, NOT `https://github.com/openshift/okd/releases`
12. **Per-module image attributes:** Some modules define their OWN local attributes (`:registry-image:`, `:index-image:`, etc.) with `ifdef::openshift-origin` overrides INSIDE the module file. These are not in `common-attributes.adoc` and are easy to miss.
13. **OLM `opm` flag difference:** The `-i` flag (base image override) in `opm generate dockerfile` is used in OCP but omitted in OKD — OKD uses the default base image.
14. **Update channels are singular for OKD:** OKD has only `stable-4`. Do not reference `fast-`, `candidate-`, or `eus-` channels. This is a critical operational difference.
15. **SNO directory naming:** OKD SNO docs use `--dir=sno` and `mkdir sno`, NOT `--dir=ocp`. The ISO is `fcos-live.iso`, not `rhcos-live.iso`.
16. **IPI provisioner setup:** OKD removes the entire `subscription-manager register` and `subscription-manager repos` block. Stream CoreOS does not use subscription-manager.
17. **Version variable naming:** OKD uses `OKD_VERSION` as the shell variable name (with values like `4.14.0-0.okd-2024-01-26-175629`), not `OCP_RELEASE`.
18. **Unoverridden attributes:** `{op-system-version-9}` (value: "9") and `{op-system-ai}` (value: "Red Hat Enterprise Linux AI") have no OKD override. If they appear in content, they will render with incorrect Red Hat values — flag and handle manually.
