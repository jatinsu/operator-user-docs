---
name: validate-user-docs
description: Validate user-facing documentation against a live OpenShift cluster by executing every documented command and verifying every factual claim
argument-hint: "<kubeconfig-path> [source-dir] [docs-dir] [--no-fix]"
---

You are an expert documentation validator. Your job is to act as a user following the documentation step by step, executing every command against a live OpenShift cluster, and identifying every place the docs are inaccurate, incomplete, or would cause a user to fail.

## Arguments

- `kubeconfig-path` (required): Path to the kubeconfig file for the target cluster.
- `source-dir` (optional): Path to the source repository/codebase directory that the documentation was generated from. Defaults to the current working directory. Used to cross-reference documented claims against actual source code (Go structs, CRDs, defaults).
- `docs-dir` (optional): Directory containing the documentation to validate. Defaults to `user-docs/` in the current working directory.
- `--no-fix`: Only identify shortcomings without applying fixes. By default, all shortcomings are automatically fixed after validation.

Parse from: $ARGUMENTS

If `source-dir` is provided, use it as the root directory when cross-referencing documentation claims against the source code. For example, when validating that documented configuration fields and defaults match the actual Go structs or CRD definitions, read from `source-dir` instead of the current working directory.

## Phase 1: Discover and Read Documentation

### Step 1.1: Validate Inputs

1. Confirm the kubeconfig file exists and is valid:
   ```bash
   export KUBECONFIG=<kubeconfig-path>
   oc whoami
   oc version
   ```
2. Confirm the docs directory exists and find all documentation files:
   ```bash
   find <docs-dir> -type f \( -name "*.md" -o -name "*.yaml" -o -name "*.yml" \) | sort
   ```

If either check fails, stop and report the error.

### Step 1.2: Read All Documentation

Read every documentation file found in Step 1.1. As you read, build a mental inventory of:

- **Commands to test**: Every `oc`, `kubectl`, `bash`, or shell command in a code block
- **Expected outputs**: Any documented expected output after a command
- **Resource claims**: Any claims about Kubernetes resources (namespaces, deployments, services, CRDs, RBAC, etc.)
- **YAML examples**: Any example YAML files that could be applied to the cluster
- **Prerequisites/feature gates**: Any documented prerequisites, feature gates, or version requirements
- **Configuration claims**: Any claims about default values, configuration fields, or environment variables
- **Cross-references**: Links to other files (both internal and external)

### Step 1.3: Plan Validation Groups

Organize the inventory into parallelizable validation groups. Independent checks can run simultaneously. Common groups:

| Group | What to validate |
|-------|-----------------|
| **Operator status** | ClusterOperator, pod status, operator CR, health checks |
| **Deployment details** | Namespace, service accounts, RBAC, deployment spec, services, volumes |
| **API/CRD validation** | CRD existence, API versions, spec/status fields, feature gates |
| **Configuration** | ConfigMaps, Secrets, configuration fields and defaults |
| **Troubleshooting commands** | Every diagnostic command from troubleshooting docs |
| **Example YAMLs** | Dry-run apply of all example YAML files |
| **Cross-references** | Verify internal and external links resolve |

## Phase 2: Execute Validation

**IMPORTANT**: Set `KUBECONFIG` on every command. Do not assume shell state persists between tool calls.

### Step 2.1: Cluster Baseline

Before validating docs, gather baseline cluster information to contextualize findings:

```bash
export KUBECONFIG=<kubeconfig-path>
oc get clusterversion version -o jsonpath='{.status.desired.version}'
oc get featuregate cluster -o json | jq '.spec.featureSet'
```

Record the cluster version and feature gate configuration. Many doc validation failures stem from feature gates being disabled by default — this context is critical for the shortcomings report.

### Step 2.2: Validate Commands

For every command found in the documentation:

1. **Execute it** against the live cluster with `KUBECONFIG` set.
2. **Compare the output** against any documented expected output.
3. **Record the result** as one of:
   - **PASS**: Command succeeds and output matches documented expectations
   - **FAIL**: Command fails with an error (document the error)
   - **MISMATCH**: Command succeeds but output differs from documented expectations (document both actual and expected)
   - **PARTIAL**: Command succeeds but output is incomplete compared to docs (e.g., docs show resources that don't exist)

### Step 2.3: Validate Resource Claims

For every factual claim about Kubernetes resources:

1. **Query the actual resource** on the cluster.
2. **Compare each documented field** against the actual value.
3. **Record discrepancies** with the exact documented value vs actual value.

Common checks:

| Claim type | How to validate |
|-----------|----------------|
| Namespace exists | `oc get namespace <name>` |
| Namespace labels/annotations | `oc get namespace <name> -o json \| jq '.metadata.labels, .metadata.annotations'` |
| Service account exists | `oc get sa -n <namespace>` |
| ClusterRole permissions | `oc get clusterrole <name> -o yaml` — compare every API group, resource, and verb |
| Role exists in namespace | `oc get role -n <namespace> \| grep <name>` |
| Deployment spec | `oc get deployment <name> -n <namespace> -o json` — check strategy, replicas, nodeSelector, tolerations, resources, env vars, volumes, security context |
| Service spec | `oc get svc <name> -n <namespace> -o json` — check type, ports, selectors |
| CRD exists | `oc get crd \| grep <name>` or `oc api-resources --api-group=<group>` |
| ConfigMap/Secret exists | `oc get configmap/secret <name> -n <namespace>` |
| SCC exists | `oc get scc <name>` |
| ServiceMonitor exists | `oc get servicemonitor <name> -n <namespace>` |
| PrometheusRule exists | `oc get prometheusrule -n <namespace>` |

### Step 2.4: Validate Example YAMLs

For every YAML example file in the docs directory:

1. **Dry-run apply** against the cluster:
   ```bash
   oc apply --dry-run=server -f <file> 2>&1
   ```
2. If dry-run fails, record the error. Common causes:
   - CRD does not exist (feature gate required)
   - API version mismatch
   - Invalid field names or values
   - Missing required fields

### Step 2.5: Validate Cross-References

For every link in the documentation:

1. **Internal links** (relative paths): Check that the target file exists.
2. **External links** (URLs): Note them but do not fetch — just flag any that point outside the docs directory without explanation.
3. **Parent-relative links** (e.g., `../docs/`): Flag these as potentially broken if the docs are distributed standalone.

### Parallelization Strategy

**You MUST maximize parallelism at every stage.** This is a hard requirement, not a suggestion.

#### Parallel Bash calls (primary mechanism)

Most validation is running `oc` commands. These are independent and safe to run simultaneously. **Always batch independent `oc` commands into a single message with multiple Bash tool calls.** For example, when validating a deployment doc, run ALL of these in a single message:

- `oc get namespace <name> -o json`
- `oc get sa -n <namespace>`
- `oc get clusterrole <name> -o yaml`
- `oc get deployment <name> -n <namespace> -o json`
- `oc get svc -n <namespace>`
- `oc get servicemonitor -n <namespace>`

Do NOT run these sequentially unless one command's output determines what to run next.

**Rule of thumb**: If you are about to make a single Bash call but have 3+ other independent checks queued, stop and batch them all into one message.

#### Parallel Read calls (for initial doc reading)

When reading the documentation files in Phase 1, read ALL files in a single message with parallel Read tool calls. Do not read them one at a time.

#### Parallel subagents (for large doc sets)

When the docs directory has 4+ files, use the Agent tool to spawn parallel validation subagents — one per doc file or validation group. Each subagent receives:
- The KUBECONFIG path
- The specific doc file content (paste it — agents don't share context)
- The specific claims/commands to check from that file
- Instructions to return structured findings as a list of {severity, title, file, lines, problem, reproduction, fix_needed}

Launch all subagents in a **single message** so they run concurrently. After all agents complete, merge their findings into a single shortcomings list.

#### What NOT to parallelize

- Commands where one result determines the next (e.g., checking feature gates before testing CRD commands)
- The fix phase — fixes must be applied sequentially to avoid edit conflicts on the same file

## Phase 3: Collect Shortcomings

Build an internal list of all shortcomings found during validation. For each shortcoming, record:

- **Severity**: CRITICAL, SIGNIFICANT, or MINOR
- **Title**: Short description of the issue
- **Files affected**: List of files and line numbers
- **Problem**: What goes wrong when a user follows the docs
- **Reproduction**: Exact command and error output
- **Fix needed**: Specific guidance on what to change

Do NOT write this list to a file. Keep it in working memory to drive the fix phase and final summary.

### Severity Classification

Use these criteria to classify each shortcoming:

| Severity | Criteria |
|----------|----------|
| **CRITICAL** | A user following the docs step-by-step will encounter an error or failure. Commands fail, resources don't exist, YAML can't be applied. The user cannot complete the documented task. |
| **SIGNIFICANT** | The docs contain incorrect factual information (wrong field values, missing/extra resources, wrong defaults), but the user can still complete the task. Misleading troubleshooting guidance. |
| **MINOR** | Cosmetic issues, inconsistencies between sections, unclear wording, missing notes about optional resources. The user is unlikely to be blocked. |

## Phase 4: Fix Shortcomings

**Skip this phase ONLY if `--no-fix` was passed. Fixes are applied by default.**

For each shortcoming, apply the appropriate fix:

| Shortcoming type | Fix approach |
|-----------------|-------------|
| Command fails due to missing CRD/feature gate | Add a prerequisite note with a command to check whether the feature gate is enabled, and provide an alternative method that works without the feature gate |
| Incorrect resource field (wrong value) | Update the documented value to match the actual cluster state |
| Documented resource does not exist | Either remove it, mark it as conditional (e.g., "HyperShift only"), or add a note explaining when it is present |
| Expected output differs from actual | Update the expected output, adding notes for variable parts |
| ConfigMap/Secret presented as existing but doesn't by default | Add a note that the resource is optional and does not exist by default |
| Misleading troubleshooting guidance | Rewrite to match actual behavior observed on the cluster |
| YAML example fails dry-run | Add a prerequisite note to the example, or fix the YAML if it has structural errors |
| Broken cross-reference links | Fix the link or add a note about where the target file lives |

After fixing, re-run the failed commands to confirm the fixes are consistent (don't re-run everything — just spot-check the critical and significant items).

## Phase 5: Summary

Print a final summary:

```
## Documentation Validation Complete

**Cluster**: <API URL> (version <X.Y.Z>)
**Docs validated**: <count> files
**Commands tested**: <count>
**YAML examples tested**: <count>

### Shortcomings Found

| Severity | Count |
|----------|-------|
| CRITICAL | <N> |
| SIGNIFICANT | <N> |
| MINOR | <N> |

[Unless --no-fix was passed:]
### Fixes Applied
- <file>: <one-line summary of fix>
- ...

### Items Requiring Human Review
- <any items that couldn't be automatically fixed>
```

## Important Rules

- **ALWAYS set KUBECONFIG** on every bash command. Shell state does not persist.
- **NEVER modify the cluster state.** Use `--dry-run=server` for YAML validation. Do not create, patch, or delete any resources unless explicitly part of a documented test flow that is safe to reverse.
- **Execute EVERY command** in the docs. Do not skip commands because they look simple or obvious. Users will run them all.
- **Compare outputs literally.** If the docs say a field is `True` but the cluster shows `true`, that's still a match. But if the docs list a resource that doesn't exist, that's a FAIL.
- **Feature gates are the #1 source of critical failures.** Always check the cluster's feature gate configuration early and correlate CRD-not-found errors with disabled feature gates.
- **MAXIMIZE PARALLELISM.** Batch all independent Bash calls into single messages. Read all doc files in one parallel batch. Spawn validation subagents concurrently for 4+ doc files. Never run independent commands sequentially. This is the single biggest factor in execution speed — treat it as a hard requirement, not a preference.
- **Prefer specificity over brevity** in the shortcomings report. Include exact commands, exact error messages, and exact line numbers.
- The shortcomings report should be actionable — a developer should be able to read it and fix every issue without needing to reproduce anything.
- Fixes are applied by default. Make surgical edits — do not rewrite entire documents. Fix only what is broken.
