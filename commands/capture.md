---
allowed-tools:
- Bash
- Write
- Read
- Glob
- Grep
argument-hint: <namespace> <title> [--type semantic|episodic|procedural] [--tags tag1,tag2]
  [--scope project|org] [--citations JSON]
description: Capture a new memory
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# /mnemonic:capture

Capture a new memory to the mnemonic filesystem.

## Arguments

- `<namespace>` - Required. Hierarchical namespace path using cognitive triad (prefixed with _ for filesystem disambiguation):
  - **Semantic** (facts/knowledge): `_semantic/decisions`, `_semantic/knowledge`, `_semantic/entities`
  - **Episodic** (events/experiences): `_episodic/incidents`, `_episodic/sessions`, `_episodic/blockers`
  - **Procedural** (processes/steps): `_procedural/runbooks`, `_procedural/patterns`, `_procedural/migrations`
- `<title>` - Required. Human-readable title for the memory
- `--type` - Memory type: semantic (default), episodic, or procedural
- `--tags` - Comma-separated list of tags
- `--scope` - project (default, current project) or org (shared across all projects in organization)
- `--confidence` - Confidence score 0.0-1.0 (default: 0.95)
- `--citations` - JSON array of citation objects (see mnemonic-format skill for schema)
- `--entity-type` - Entity type from ontology (e.g., technology, component, runbook)
- `--entity-id` - Custom entity ID (auto-generated if not provided)

## Procedure

### Step 1: Parse Arguments

```bash
NAMESPACE="${1:-decisions}"
TITLE="${2:-Untitled Memory}"
TYPE="${TYPE:-semantic}"
SCOPE="${SCOPE:-project}"
CONFIDENCE="${CONFIDENCE:-0.95}"
TAGS="${TAGS:-}"
```

### Step 2: Validate Namespace

```bash
# Use ontology registry to validate namespace (includes base + user + project ontologies)
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $0))}"
if python3 "$PLUGIN_DIR/skills/ontology/lib/ontology_registry.py" --validate "$NAMESPACE" >/dev/null 2>&1; then
    echo "Namespace '$NAMESPACE' validated"
else
    echo "Error: Invalid namespace '$NAMESPACE'"
    echo "Valid namespaces:"
    python3 "$PLUGIN_DIR/skills/ontology/lib/ontology_registry.py" --namespaces
    exit 1
fi
```

### Step 3: Generate Identifiers

**CRITICAL: You MUST execute these commands to generate real values. NEVER write placeholder text like "PLACEHOLDER_UUID" or "PLACEHOLDER_DATE" into memory files.**

```bash
# UUID - MUST be a real UUID, not a placeholder
UUID=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]')
[ -z "$UUID" ] && UUID=$(python3 -c "import uuid; print(uuid.uuid4())")

# Slug from title
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 50)

# Timestamp - MUST be a real ISO 8601 timestamp, not a placeholder
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Organization
ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"
```

**Validation:** Before proceeding, verify UUID looks like `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` and DATE looks like `2026-01-28T12:00:00Z`. If either is empty or a placeholder, re-run the generation commands.

### Step 4: Determine Path

```bash
# Get project name from git remote or directory
PROJECT=$(git remote get-url origin 2>/dev/null | sed -E 's|.*/([^/]+)\.git$|\1|' | sed 's|\.git$||')
[ -z "$PROJECT" ] && PROJECT=$(basename "$(pwd)")

# All memories are stored under ~/.claude/mnemonic/
# Path structure: {org}/{project}/{namespace}/ for project scope
#                 {org}/{namespace}/ for org scope (when --scope org)
if [ "$SCOPE" = "org" ]; then
    # Org-wide memory (shared across projects in org)
    MEMORY_DIR="$HOME/.claude/mnemonic/${ORG}/${NAMESPACE}"
else
    # Project-specific memory (default)
    MEMORY_DIR="$HOME/.claude/mnemonic/${ORG}/${PROJECT}/${NAMESPACE}"
fi

mkdir -p "$MEMORY_DIR"
MEMORY_FILE="${MEMORY_DIR}/${UUID}-${SLUG}.memory.md"
```

### Step 5: Format Tags

```bash
# Convert comma-separated to YAML list
if [ -n "$TAGS" ]; then
    TAGS_YAML=$(echo "$TAGS" | tr ',' '\n' | sed 's/^/  - /' | sed 's/^ *- */  - /')
else
    TAGS_YAML="  - untagged"
fi
```

### Step 5b: Format Citations (Optional)

If `--citations` is provided as a JSON array, convert to YAML:

```bash
# CITATIONS is optional JSON array: '[{"type":"paper","title":"...","url":"..."}]'
if [ -n "$CITATIONS" ]; then
    # Parse JSON and format as YAML (Claude will handle this conversion)
    CITATIONS_YAML="citations:"
    # Each citation becomes:
    #   - type: paper
    #     title: "..."
    #     url: https://...
    #     accessed: 2026-01-24T10:00:00Z
else
    CITATIONS_YAML=""
fi
```

**Citation fields:**
- `type` (required): paper, documentation, blog, github, stackoverflow, article
- `title` (required): Human-readable title
- `url` (required): Full URL
- `author` (optional): Author name
- `date` (optional): Publication date
- `accessed` (optional): When accessed
- `relevance` (optional): 0.0-1.0
- `note` (optional): Brief description

### Step 6: Prompt for Content

Ask the user to provide the memory content. This should include:
- Main description
- Rationale or context
- Any code references
- Related memories

### Step 7: Create Memory File

**CRITICAL: Replace ALL variables below with the REAL values generated in Steps 1-5. Every `{VARIABLE}` must be substituted. No placeholders may appear in the final file.**

Use the Write tool to create the file at `$MEMORY_FILE` with this structure (all variables substituted with real values):

```yaml
---
id: <real UUID from Step 3>
type: <real TYPE from Step 1>
namespace: <real NAMESPACE from Step 1>
created: <real DATE from Step 3>
modified: <real DATE from Step 3>
title: "<real TITLE from Step 1>"
tags:
<real TAGS_YAML from Step 5>
temporal:
  valid_from: <real DATE from Step 3>
  recorded_at: <real DATE from Step 3>
provenance:
  source_type: conversation
  agent: claude-opus-4
  confidence: <real CONFIDENCE from Step 1>
---

# <real TITLE>

<real CONTENT from Step 6>

## Rationale

<real RATIONALE from Step 6>
```

**Validation:** After writing, read the first 5 lines of the file and verify the `id:` field contains a real UUID (not "PLACEHOLDER" or "{UUID}").

### Step 7b: Add Ontology Fields (if --entity-type provided)

If `--entity-type` is specified, add ontology metadata:

```yaml
# ONTOLOGY_YAML (if entity-type provided):
ontology:
  entity_type: {ENTITY_TYPE}
  entity_id: {ENTITY_ID}

# ENTITY_YAML (entity-specific fields based on schema):
entity:
  name: "{extracted from title}"
  # Additional fields based on entity type schema
```

When capturing with an entity type:
1. Look up entity type schema from loaded ontology
2. Prompt user for required fields
3. Include entity block in frontmatter
4. Claude suggests entity references in content using `@[[Name]]` syntax

### Step 8: Commit to Git

```bash
cd ~/.claude/mnemonic
git add -A
git commit -m "Capture: ${TITLE}"
cd -
```

### Step 9: Report

```bash
echo "Memory captured:"
echo "  ID: $UUID"
echo "  File: $MEMORY_FILE"
echo "  Namespace: $NAMESPACE/$SCOPE"
echo "  Type: $TYPE"
```

## Example Usage

```
/mnemonic:capture _semantic/decisions "Use PostgreSQL for data storage" --tags database,architecture
/mnemonic:capture _procedural/patterns "Repository pattern for data access" --tags database,patterns
/mnemonic:capture _episodic/incidents "Database connection timeout issue" --type episodic
```

### Example with Citations

```
/mnemonic:capture _semantic/knowledge "PostgreSQL JSON Performance" --tags database,performance --citations '[{"type":"paper","title":"PostgreSQL vs MySQL Performance","url":"https://arxiv.org/abs/2024.12345","author":"Smith et al.","relevance":0.95}]'
```

## Output

Display:
- Generated UUID
- File path
- Namespace and scope
- Memory type
- Confirmation of git commit
