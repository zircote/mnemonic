---
description: Capture a new memory
argument-hint: "<namespace> <title> [--type semantic|episodic|procedural] [--tags tag1,tag2] [--scope user|project] [--citations JSON]"
allowed-tools:
  - Bash
  - Write
  - Read
---

# /mnemonic:capture

Capture a new memory to the mnemonic filesystem.

## Arguments

- `<namespace>` - Required. One of: apis, blockers, context, decisions, learnings, patterns, security, testing, episodic
- `<title>` - Required. Human-readable title for the memory
- `--type` - Memory type: semantic (default), episodic, or procedural
- `--tags` - Comma-separated list of tags
- `--scope` - user (cross-project) or project (default, current codebase)
- `--confidence` - Confidence score 0.0-1.0 (default: 0.95)
- `--citations` - JSON array of citation objects (see mnemonic-format skill for schema)

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
VALID_NS="apis blockers context decisions learnings patterns security testing episodic"
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
if [ "$SCOPE" = "project" ]; then
    MEMORY_DIR="./.claude/mnemonic/${NAMESPACE}/project"
else
    MEMORY_DIR="$HOME/.claude/mnemonic/${ORG}/${NAMESPACE}/user"
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
namespace: {NAMESPACE}/{SCOPE}
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
---

# {TITLE}

{CONTENT}

## Rationale

{RATIONALE}

## Relationships

- relates-to [[other-memory-id]]
```

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
/mnemonic:capture decisions "Use PostgreSQL for data storage" --type semantic --tags database,architecture --scope project
```

### Example with Citations

```
/mnemonic:capture learnings "PostgreSQL JSON Performance" --type semantic --tags database,performance --citations '[{"type":"paper","title":"PostgreSQL vs MySQL Performance","url":"https://arxiv.org/abs/2024.12345","author":"Smith et al.","relevance":0.95}]'
```

## Output

Display:
- Generated UUID
- File path
- Namespace and scope
- Memory type
- Confirmation of git commit
