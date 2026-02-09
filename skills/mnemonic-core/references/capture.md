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

## Step 3.5: Discover Related Memories

After determining the namespace and title, search for related memories to establish connections.

**Why relationships matter:**
- Link related decisions together
- Track knowledge evolution (supersedes, derived_from)
- Enable graph-based memory navigation
- Prevent duplicates by surfacing similar memories

**Search for related memories:**

```bash
# Search using title keywords and namespace
rg -i "{title_keywords}" ${MNEMONIC_ROOT} --glob "*.memory.md" -l | head -5
```

**Review candidates and determine relationship types:**

For each candidate memory, evaluate:

| Relationship Type | When to Use | Example |
|------------------|-------------|---------|
| `supersedes` | This memory replaces/updates an older one | New decision overrides previous approach |
| `derived_from` | This memory builds on another | Implementation pattern based on architecture decision |
| `relates_to` | Thematically connected | Two related but independent decisions |

**Decision criteria:**
- Same namespace + similar title keywords (>50% overlap) → `supersedes`
- Different namespace + shared concepts (>30% overlap) → `derived_from`
- Thematic connection without direct evolution → `relates_to`

**Include discovered relationships in frontmatter:**

If you find related memories, add them to the `relationships:` field in Step 4.

## Step 4: Create Memory File

**CRITICAL: Always generate REAL values. Never write placeholders like "PLACEHOLDER_UUID" or "PLACEHOLDER_DATE".**

**File naming:** `{slug}.memory.md`

**Optional fields:**
- `tags: [tag1, tag2]` - categorization tags
- `namespace: _semantic/decisions` - explicit namespace path
- `relationships:` - links to other memories (see Step 3.5)
  ```yaml
  relationships:
    - type: supersedes
      target: a5e46807-uuid-here
      label: "Replaces old approach"
    - type: relates_to
      target: b6f57918-uuid-here
      label: "Related decision"
  ```

```bash
# Resolve MNEMONIC_ROOT from config
if [ -f "$HOME/.config/mnemonic/config.json" ]; then
    RAW_PATH=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json')).get('memory_store_path', '~/.claude/mnemonic'))")
    MNEMONIC_ROOT="${RAW_PATH/#\~/$HOME}"
else
    MNEMONIC_ROOT="$HOME/.claude/mnemonic"
fi
# Generate real values - NEVER use placeholder text
UUID=$(uuidgen 2>/dev/null | tr '[:upper:]' '[:lower:]')
[ -z "$UUID" ] && UUID=$(python3 -c "import uuid; print(uuid.uuid4())")
NAMESPACE="decisions"
SCOPE="project"
TYPE="semantic"
TITLE="Use PostgreSQL for data storage"
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-' | head -c 50)
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Determine path
if [ "$SCOPE" = "project" ]; then
    MEMORY_DIR="${MNEMONIC_ROOT}/${NAMESPACE}/project"
else
    ORG="${ORG:-default}"
    MEMORY_DIR="$MNEMONIC_ROOT/${ORG}/${NAMESPACE}/user"
fi

mkdir -p "$MEMORY_DIR"

# Create memory file (minimal format)
cat > "${MEMORY_DIR}/${SLUG}.memory.md" << MEMORY_EOF
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
cd ${MNEMONIC_ROOT}
git add -A
git commit -m "Capture: ${TITLE}"
cd -
```
