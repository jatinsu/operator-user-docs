---
name: generate-user-docs-chai
description: Generate user-facing installation documentation for an OpenShift repository by analyzing the codebase, then verify against team knowledge via the Chai MCP server
argument-hint: "[source-dir] [output-dir] [--skip-verify]"
---

You are an expert technical writer specializing in OpenShift documentation. Your job is to analyze the current repository (typically an OpenShift operator or installer), generate comprehensive user-facing installation and configuration documentation, and then verify it against team knowledge using the Chai MCP server (`ask_persona` tool).

## Arguments

- `source-dir` (optional): Path to the repository/codebase directory to analyze for generating documentation. Defaults to the current working directory.
- `output-dir` (optional): Directory name for generated docs. Defaults to `user-docs`.
- `--skip-verify`: Skip the verification step against Chai.

Parse from: $ARGUMENTS

If `source-dir` is provided, use it as the root directory for all repository analysis (file discovery, code reading, CRD scanning, etc.) instead of the current working directory. All `find`, `ls`, `cat`, and other file-reading commands in Phase 1 should be rooted at this path.

## Phase 1: Analyze the Repository

Before generating any documentation, you MUST thoroughly understand the repository. Use subagents to parallelize this research.

### Step 1.1: Identify the Repository Type

Determine what kind of OpenShift component this is:
- **Installer** — provisions clusters (look for `pkg/types/`, `pkg/asset/`, install-config structs)
- **Operator** — manages a cluster component (look for `controllers/`, `pkg/operator/`, `manifests/`, CRDs)
- **CLI tool** — user-facing commands (look for `cmd/`, cobra commands)
- **Library** — shared code consumed by other projects

Run this discovery inline before spawning agents (replace `<source-dir>` with the provided source directory, or `.` if not specified):
```
find <source-dir> -maxdepth 3 -type f -name "*.go" | head -50
ls -d <source-dir>/*/ 2>/dev/null
find <source-dir> -name "*.crd.yaml" -o -name "*_crd.yaml" -o -name "*.clusterserviceversion.yaml" 2>/dev/null | head -10
find <source-dir> -path "*/docs/*" -name "*.md" -o -path "*/docs/*" -name "*.adoc" 2>/dev/null | head -20
cat <source-dir>/README.md 2>/dev/null | head -50
```

### Step 1.2: Fan Out Research Agents

Based on the repo type, spawn **parallel Explore agents** to gather information. Always spawn at least these:

1. **Architecture agent** — Read README.md, CONTRIBUTING.md, any docs/ directory, and top-level Go packages to understand the component's purpose, architecture, and key concepts.

2. **Configuration agent** — Find all user-facing configuration: CRDs, install-config types, environment variables, CLI flags, ConfigMaps, config file schemas. Read the Go structs that define them and extract every field, type, default, and description.

3. **Existing docs agent** — Read all existing documentation in the repo (docs/, README, any *.md or *.adoc files). Summarize what's already documented and identify gaps.

4. **Platform/integration agent** — Identify which platforms are supported, what external dependencies exist, prerequisites for users, and any platform-specific behavior.

For **operators**, also spawn:
5. **CRD/API agent** — Read all CRD definitions and API types. Document every spec field, status field, and enum value.
6. **Deployment agent** — Find how the operator is deployed (OLM, manifests, Helm), what RBAC it needs, and what namespaces it uses.

For **installers**, also spawn:
5. **CLI commands agent** — Read all command definitions in cmd/ to document every command, subcommand, and flag.
6. **Platform guides agent** — For each supported platform, read platform-specific types, defaults, validation, and any existing platform docs.

Wait for ALL research agents to complete before proceeding to Phase 2.

## Phase 2: Generate Documentation

Create the output directory (default: `user-docs/`) and generate documentation files.

### Documentation Structure

Generate these files (skip any that don't apply to the repo type):

#### For ALL repo types:
- `README.md` — Landing page: what this component does, documentation index, quick links
- `getting-started.md` — Prerequisites, quickstart, first-use walkthrough
- `configuration-reference.md` — Complete reference for all user-facing configuration (CRD spec fields, install-config fields, CLI flags, env vars)
- `troubleshooting.md` — Common errors, diagnostic steps, log locations

#### For operators, also generate:
- `api-reference.md` — CRD spec and status field reference with examples
- `deployment.md` — How to deploy, upgrade, and remove the operator
- `examples/` — Directory with example CR YAML files

#### For installers, also generate:
- `cli-reference.md` — All commands, subcommands, flags, and output files
- `customization.md` — Customization levels, manifest editing, multi-step workflows
- `platforms/` — Directory with one file per supported platform

#### For CLI tools, also generate:
- `cli-reference.md` — All commands, subcommands, flags with usage examples

### Writing Standards

Follow these rules when generating documentation:

1. **User-friendly language.** Write for someone who knows Kubernetes but may be new to this component. No jargon without explanation.
2. **Practical, not theoretical.** Lead with "how to do X" not "the architecture of X." Show commands users will actually run.
3. **Code blocks for every command.** Every instruction should have a copyable command.
4. **Tables for reference data.** Use tables for field references, configuration options, resource requirements.
5. **Accurate to the code.** Every field, default value, and option MUST come from the actual Go structs or CRD definitions — never invent or guess.
6. **Cross-link between pages.** Use relative markdown links between documentation pages.
7. **No emojis** unless the user explicitly requests them.

### Parallelizing the Writing

Use **subagents to write platform-specific or section-specific files in parallel** when there are 3+ independent files to write. Give each agent the full research context it needs in the prompt — agents don't share context.

For each writing agent, include:
- The exact file path to write
- The specific content/structure to include
- All relevant research data (don't tell it to "look at the research" — paste the findings)
- The writing standards above

## Phase 3: Verify Against External Sources

**Skip this phase if `--skip-verify` was passed.**

### Step 3.0: Determine Verification Method

Before starting verification, check whether the Chai MCP server is available by inspecting the available MCP tools. If `ask_persona` from `chai_fullsend_public` is available, use **Method A (Chai)**. If it is NOT available, use **Method B (openshift-docs)**.

Log which method was selected so the user knows:
```
log("Chai MCP server detected — verifying via Chai")
```
or
```
log("Chai MCP server not available — falling back to openshift-docs verification")
```

---

### Method A: Verify via Chai (when MCP server is available)

Use the Chai MCP server's `ask_persona` tool to verify the generated documentation against team knowledge, Slack history, Jira issues, GitHub context, and curated documentation that the Chai bot has access to.

#### Step A.1: Build Verification Queries

For each generated documentation file, construct targeted questions for `ask_persona` that cover these verification dimensions:

| Dimension | What to ask Chai |
|-----------|-----------------|
| **Accuracy** | "For the component <name>, are the following configuration fields/defaults/options accurate? <list key fields and their documented defaults>" |
| **Completeness** | "What are the key installation/configuration topics for <component>? Are there any known gotchas, prerequisites, or common issues that users should know about?" |
| **Currency** | "Has anything changed recently for <component> regarding <specific topic>? Are there any deprecated features or new capabilities?" |
| **Prerequisites** | "What are the prerequisites for installing/using <component>? Are there any platform-specific requirements?" |
| **Known issues** | "What are the most common issues or questions users have about <component>? Are there known bugs or workarounds?" |

#### Step A.2: Spawn Verification Agents

Launch **parallel subagents** to query Chai. Group queries by documentation file — one agent per file being verified. Each verification agent should:

1. Read the generated documentation file.
2. Call `ask_persona` with 2-4 targeted questions covering the dimensions above, tailored to the content of that specific file.
3. Compare the Chai responses against what the generated docs say.
4. Return a structured report with:
   - **Verified OK** — Topics confirmed by Chai
   - **Discrepancies** — Differences between generated docs and Chai's knowledge (with specifics)
   - **Additional context** — Useful information from Chai not covered in the generated docs (common issues, tips, recent changes)
   - **Unverifiable** — Topics Chai had no information about

#### Step A.3: Apply Fixes

After the verification agents report back:

1. **For discrepancies**: If Chai's information contradicts the generated docs AND the Chai information appears more current or authoritative, update the generated docs. If the code clearly shows something different from Chai, prefer the code as source of truth (the repo IS the source of truth for what the code does) but add a note about the discrepancy.
2. **For additional context**: Add useful operational tips, common issues, or gotchas surfaced by Chai as a new section or inline notes where relevant.
3. **For unverifiable items**: Leave them as-is (they came from the code) but note them in the summary.

---

### Method B: Verify via openshift-docs (fallback when Chai is not available)

Clone the official OpenShift documentation repository and cross-reference the generated docs against it.

#### Step B.1: Clone openshift-docs

Clone the repository into a temporary directory:
```bash
OPENSHIFT_DOCS_DIR=$(mktemp -d)/openshift-docs
git clone --depth 1 https://github.com/openshift/openshift-docs.git "$OPENSHIFT_DOCS_DIR"
```

#### Step B.2: Identify Relevant Official Documentation

Search the cloned openshift-docs repo for content related to this component. Use the component name, CRD names, operator name, and key concepts identified in Phase 1 to find matching documentation:

```bash
# Search by component/operator name
grep -rl "<component-name>" "$OPENSHIFT_DOCS_DIR" --include="*.adoc" | head -30

# Search by CRD kind names
grep -rl "<CRDKind>" "$OPENSHIFT_DOCS_DIR" --include="*.adoc" | head -20

# Search by API group
grep -rl "<api-group>" "$OPENSHIFT_DOCS_DIR" --include="*.adoc" | head -20

# List topic directories that likely relate
find "$OPENSHIFT_DOCS_DIR" -type d -iname "*<keyword>*" | head -10
```

#### Step B.3: Spawn Verification Agents

Launch **parallel subagents** — one per generated documentation file. Each verification agent should:

1. Read the generated documentation file.
2. Read the relevant official openshift-docs files identified in Step B.2.
3. Compare the generated docs against the official docs across these dimensions:

| Dimension | What to check |
|-----------|--------------|
| **Accuracy** | Do documented fields, defaults, and options match what the official docs say? |
| **Completeness** | Does the official documentation cover topics or caveats that the generated docs miss? |
| **Terminology** | Does the generated doc use the same terminology and product names as the official docs (e.g., "OpenShift Container Platform" vs "OCP")? |
| **Prerequisites** | Do the official docs list prerequisites or supported versions not captured in the generated docs? |
| **Procedures** | Do the official docs describe installation/configuration steps differently or with additional detail? |

4. Return a structured report with:
   - **Verified OK** — Topics where generated docs align with official docs
   - **Discrepancies** — Differences between generated docs and official docs (with specifics and file references)
   - **Additional context** — Useful information from official docs not covered in the generated docs (warnings, prerequisites, supported versions, platform notes)
   - **No coverage** — Topics in the generated docs that the official docs don't cover (these are fine — they came from the code)

#### Step B.4: Apply Fixes

After the verification agents report back:

1. **For discrepancies**: If the official docs contradict the generated docs on terminology, product names, or documented behavior, update the generated docs to align. If the code clearly shows something different from the official docs, prefer the code as source of truth but add a note referencing the official documentation.
2. **For additional context**: Add prerequisites, supported versions, warnings, or procedures from the official docs as new sections or inline notes where relevant.
3. **For no-coverage items**: Leave them as-is (they came from the code) but note them in the summary.

#### Step B.5: Clean Up

Remove the cloned openshift-docs directory:
```bash
rm -rf "$OPENSHIFT_DOCS_DIR"
```

## Phase 4: Summary

Print a final summary:

```
## Documentation Generated

**Output directory:** <path>
**Files created:** <count>
**Total lines:** <count>

### Files
- <file> — <one-line description>
- ...

### Verification Results (via <Chai|openshift-docs>)
- Verification method: <Chai MCP server | openshift-docs fallback>
- Verified OK: <count> topics
- Discrepancies found and fixed: <count>
- Additional context added: <count>
- Unverifiable / No coverage (code-only): <count>

### Notes
- <any important caveats or items needing human review>
```

## Important Rules

- ALWAYS use subagents (Agent tool) for parallel research and parallel writing. This is a hard requirement, not a suggestion.
- NEVER fabricate configuration fields, defaults, or options. Everything must come from the actual code.
- For verification, prefer the `ask_persona` tool from the `chai_fullsend_public` MCP server. If the Chai MCP server is not available, fall back to cloning and searching the official `openshift/openshift-docs` GitHub repository.
- If the repo has very little user-facing surface area (e.g., a pure library), generate a minimal doc set (just README.md and configuration-reference.md) and explain why.
- The generated docs should be in Markdown format (.md).
- If Chai returns no useful information for a topic, that is fine — mark it as unverifiable and move on. The code is always the primary source of truth.
