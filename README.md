# operator-user-docs

A Claude Code plugin that generates, validates, and brands user-facing documentation for OpenShift operators -- directly from source code.

## Quickstart

### 1. Load the plugin

**Option A:** Install permanently

```bash
claude plugin add jsuri/operator-user-docs
```

**Option B:** Load from a local directory for the current session only

```bash
claude --plugin-dir /path/to/operator-user-docs
```

### 2. Generate docs for an operator

```
/generate-user-docs-chai --source-dir /path/to/your-operator
```

### 3. Validate against a live cluster

```
/validate-user-docs --kubeconfig-path ~/.kube/config --docs-dir user-docs/
```

### 4. (Optional) Convert to OKD branding

```
/okd-branding --file-or-directory user-docs/
```

### 5. Build a browsable website

```bash
cd create-docs-website
python3 generate-site.py --docs-dir ../user-docs
# Open index.html in a browser
```

## Workflow - How the docs are generated/validated

Below is the end-to-end workflow for producing validated operator documentation.

```
+---------------------------+       +------------------------+
|  1. Generate Docs         |       |  2. Validate Docs      |
|  /generate-user-docs-     | ----> |  /validate-user-docs   |
|   chai              |       |                        |
+---------------------------+       +------------------------+
                                              |
                                              v
                                    +------------------------+       +------------------------+
                                    |  3. OKD Branding       |       |  4. Build Website      |
                                    |  /okd-branding         | ----> |  create-docs-website/  |
                                    |  (optional)            |       |                        |
                                    +------------------------+       +------------------------+
```

### Step 1: Generate Documentation (`/generate-user-docs-chai`)

Analyzes the operator's source code and produces a full set of Markdown documentation.

**How it works:** Spawns parallel research agents that scan the repository for architecture, CRD definitions, Go structs, configuration fields, existing docs, and platform details. A second wave of agents writes each documentation file (README, getting-started, configuration-reference, api-reference, troubleshooting, deployment, examples) using only facts found in the actual code -- nothing is fabricated. Finally, a verification phase cross-references the generated docs against team knowledge via the Chai MCP server (or falls back to the official `openshift-docs` repo) to catch inaccuracies.

**Output:** A `user-docs/` directory containing Markdown files and example YAMLs.

### Step 2: Validate Documentation (`/validate-user-docs`)

Runs every command and checks every claim in the generated docs against a live OpenShift cluster.

**How it works:** Reads each documentation file line by line and inventories every shell command, API resource reference, YAML example, and factual claim. Then, it executes each command against the cluster (using `--dry-run=server` to avoid mutations), applies example YAMLs, verifies CRD fields exist, and confirms that described resources, feature gates, and defaults match reality. Every failure is classified by severity -- CRITICAL (user will fail), SIGNIFICANT (incorrect but non-blocking), or MINOR (cosmetic). Issues are auto-fixed in the docs unless `--no-fix` is passed.

**Requires:** A valid `kubeconfig` pointing to a running cluster.

### Step 3: OKD Branding (`/okd-branding`) -- Optional

Converts OpenShift Container Platform (OCP) documentation to OKD branding.

**How it works:** Applies a 12-step conversion procedure that sweeps through every file, replacing product names (OCP to OKD), operating system references (RHCOS to SCOS), sub-product names, registry URLs, container image references, pull secret requirements, update channels, and architecture claims. It removes enterprise-only content (FIPS, subscriptions, support cases, Red Hat Marketplace) and adds OKD-specific content (Keycloak, community operators, GitHub release links). A final validation pass catches any remaining Red Hat branding that slipped through. Covers 19 transformation categories with rules for edge cases like release image tag formats, SNO directory naming, and OLM base image differences.

### Step 4: Build Website (`create-docs-website/`)

Generates a static, browsable documentation site from the Markdown files.

**How it works:** A Python script (`generate-site.py`) walks the docs directory, discovers all Markdown and config files, copies them into `content/`, and produces a `site-manifest.json` that describes the page hierarchy. The included `index.html` renders the manifest as an interactive sidebar with navigation -- open it in any browser, no server required.
