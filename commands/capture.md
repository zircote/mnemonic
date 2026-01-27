---
description: Capture a new memory
argument-hint: "<namespace> <title> [--type semantic|episodic|procedural] [--tags tag1,tag2] [--scope project|org] [--citations JSON]"
allowed-tools:
  - Bash
  - Write
  - Read
---

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
# Cognitive triad hierarchical namespaces (prefixed with _ for filesystem disambiguation)
VALID_NS="_semantic _semantic/decisions _semantic/knowledge _semantic/entities"
VALID_NS="$VALID_NS _episodic _episodic/incidents _episodic/sessions _episodic/blockers"
VALID_NS="$VALID_NS _procedural _procedural/runbooks _procedural/patterns _procedural/migrations"

# Check for custom namespaces from ontology
ONTOLOGY_FILE=".claude/mnemonic/ontology.yaml"
if [ -f "$ONTOLOGY_FILE" ]; then
    CUSTOM_NS=$(grep -E "^  [a-z]" "$ONTOLOGY_FILE" | grep -v "#" | sed 's/:.*//;s/ //g' | tr '\n' ' ')
    VALID_NS="$VALID_NS $CUSTOM_NS"
fi

if ! echo "$VALID_NS" | grep -qw "$NAMESPACE"; then
    echo "Error: Invalid namespace '$NAMESPACE'"
    echo "Valid namespaces: $VALID_NS"
    exit 1
fi
```

### Step 3: Generate Identifiers

```bash
# UUID
UUID=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]')
[ -z "$UUID" ] && UUID=$(python3 -c "import uuid; print(uuid.uuid4())")

# Slug from title
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 50)

# Timestamp
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Organization
ORG=$(git remote get-url origin 2>/dev/null | sed -E 's|.*[:/]([^/]+)/[^/]+\.git$|\1|' | sed 's|\.git$||')
[ -z "$ORG" ] && ORG="default"
```

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

```yaml
---
id: {UUID}
type: {TYPE}
namespace: {NAMESPACE}
created: {DATE}
modified: {DATE}
title: "{TITLE}"
tags:
{TAGS_YAML}
temporal:
  valid_from: {DATE}
  recorded_at: {DATE}
provenance:
  source_type: conversation
  agent: claude-opus-4
  confidence: {CONFIDENCE}
{CITATIONS_YAML}
{ONTOLOGY_YAML}
{ENTITY_YAML}
---

# {TITLE}

{CONTENT}

## Rationale

{RATIONALE}

## Relationships

- relates-to [[other-memory-id]]
```

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
4. Claude suggests entity references in content using @[[Name]] syntax

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
