<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->


# Capture Workflow

Complete workflow for capturing memories to mnemonic.

## Step 1: Generate UUID

```bash
# macOS/Linux with uuidgen
UUID=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]')

# Fallback to Python
[ -z "$UUID" ] && UUID=$(python3 -c "import uuid; print(uuid.uuid4())")
```

## Step 2: Determine Namespace and Scope

| Content Type | Namespace | Example |
|--------------|-----------|---------|
| API documentation | apis | REST endpoint specs |
| Problems/issues | blockers | Bug that blocked progress |
| Background info | context | Project setup, environment |
| Architectural choices | decisions | "We chose PostgreSQL because..." |
| Insights/discoveries | learnings | "TIL that X works better than Y" |
| Code conventions | patterns | "Always use factory pattern for..." |
| Security policies | security | "Never store secrets in..." |
| Test strategies | testing | "Edge case: empty input..." |
| Events/experiences | episodic | Debug session, incident |

**Scope Selection:**
- `user/` - Personal knowledge, cross-project
- `project/` - Specific to current codebase

## Step 3: Classify Cognitive Type

| Type | When to Use | Indicators |
|------|-------------|------------|
| `semantic` | Facts, concepts, specifications | "X is Y", definitions, docs |
| `episodic` | Events, experiences, incidents | "When we...", timestamps |
| `procedural` | Processes, workflows, how-tos | "To do X, first...", steps |

## Step 4: Create Memory File

**File naming:** `{uuid}-{slug}.memory.md`

```bash
# Variables
UUID="550e8400-e29b-41d4-a716-446655440000"
NAMESPACE="decisions"
SCOPE="project"
TYPE="semantic"
TITLE="Use PostgreSQL for data storage"
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 50)
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Determine path
if [ "$SCOPE" = "project" ]; then
    MEMORY_DIR="~/.claude/mnemonic/${NAMESPACE}/project"
else
    ORG="${ORG:-default}"
    MEMORY_DIR="$HOME/.claude/mnemonic/${ORG}/${NAMESPACE}/user"
fi

mkdir -p "$MEMORY_DIR"

# Create memory file (minimal format)
cat > "${MEMORY_DIR}/${UUID}-${SLUG}.memory.md" << MEMORY_EOF
---
id: ${UUID}
title: "${TITLE}"
type: ${TYPE}
created: ${DATE}
---

# ${TITLE}

## Summary

[One sentence summary]

## Details

[Full content here]
MEMORY_EOF
```

## Step 5: Git Commit

```bash
cd ~/.claude/mnemonic
git add -A
git commit -m "Capture: ${TITLE}"
cd -
```
