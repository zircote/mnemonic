# Windsurf (Codeium) Integration

Integrate Mnemonic with Windsurf's Cascade AI using Rules and Memories.

## Overview

Windsurf's Cascade has built-in memory capabilities. This integration configures it to use Mnemonic's filesystem-based memory format for portability across tools.

## Setup

### Configure Rules

1. Open Windsurf
2. Navigate to **Settings > Cascade > Rules**
3. Add the following rules:

```
When I ask you to remember something, create a memory file at:
${MNEMONIC_ROOT}/default/{namespace}/user/

Use MIF Level 3 format with YAML frontmatter:
- id: UUID
- type: semantic|episodic|procedural
- namespace: {namespace}/user
- created: ISO8601 timestamp
- title: Descriptive title
- tags: array

Before implementing features, search for relevant memories:
rg -i "<topic>" ${MNEMONIC_ROOT}/ --glob "*.memory.md"

Capture decisions to decisions/, learnings to learnings/, patterns to patterns/.
```

### Memory Namespace Mapping

Map Cascade's built-in memories to Mnemonic namespaces:

| Cascade Memory Type | Mnemonic Namespace |
|--------------------|--------------------|
| Preferences | context/ |
| Decisions | decisions/ |
| Learnings | learnings/ |
| Patterns | patterns/ |

## Usage

### Natural Language

```
"Remember that we're using PostgreSQL for the database"
"What do we know about authentication?"
"Capture this as a pattern: always use dependency injection"
```

### Explicit Commands

```
"Create a mnemonic memory about using REST over GraphQL"
"Search mnemonic for database decisions"
```

## Syncing with Built-in Memories

Windsurf Cascade generates memories automatically. To sync these with Mnemonic:

1. Export Cascade memories periodically
2. Convert to MIF Level 3 format
3. Store in appropriate Mnemonic namespace

## Verification

1. Create a test memory: "Remember that this is a test"
2. Check `${MNEMONIC_ROOT}/default/context/user/` for the file
3. Ask Cascade: "What do you remember about tests?"

## Limitations

- UI-based configuration only
- No direct file system access in some modes
- Automatic memory sync requires manual intervention

---

## Common Workflows

### Daily Development

```
Morning:
1. Open project in Windsurf
2. Ask Cascade: "What context do we have about this project?"
3. Continue where you left off

During Development:
1. Before implementing: "Check memories for [feature] patterns"
2. After decisions: "Remember we decided to use [approach]"
3. After debugging: "Store this fix as a learning"

End of Day:
1. Review Cascade's memory panel
2. Export significant memories to mnemonic format
```

### Feature Implementation

```
1. "What patterns exist for [component type]?"
   → Cascade references patterns/

2. "Any decisions about [feature]?"
   → Searches decisions/

3. Implement following established patterns

4. "Remember this pattern for future reference"
   → Creates memory file
```

### Code Review with Memory

```
1. Review PR changes
2. "What patterns should this code follow?"
3. "Any prior decisions about this area?"
4. Reference memories in review comments
```

---

## Advanced Patterns

### Bidirectional Sync

Sync between Cascade's built-in memories and mnemonic files:

```bash
# Export mnemonic to Cascade-readable format
./tools/mnemonic-export --format windsurf > .windsurf/memories/project.md

# Import Cascade memories to mnemonic
./tools/import-cascade-memories \
  --source ~/.windsurf/memories/ \
  --target ${MNEMONIC_ROOT}/default/
```

### Project-Specific Configuration

Create project-level rules in `.windsurfrules`:

```markdown
# Project Memory Configuration

Memory storage: ${MNEMONIC_ROOT}/this-project/

## Namespaces
- decisions/ - Architectural decisions
- patterns/ - Code patterns and conventions
- apis/ - API documentation
- testing/ - Testing strategies

## Capture Triggers
- "we decided" → decisions/
- "use this pattern" → patterns/
- "learned that" → learnings/
```

### Team Collaboration

Share memories via git:

```bash
# Team patterns repository
git clone git@github.com:team/memories.git ${MNEMONIC_ROOT}/team

# Reference in Windsurf rules
Also check ${MNEMONIC_ROOT}/team/ for shared patterns
```

---

## Migrating from Windsurf Memories

If you're using Windsurf's built-in memory system:

### Step 1: Export Current Memories

Windsurf stores memories in:
- `.windsurf/memories/`
- Cascade's internal storage

Export via:
1. Open Cascade settings
2. Navigate to Memory section
3. Export to markdown

### Step 2: Convert to MIF Format

```bash
# Manual conversion for each memory
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > ${MNEMONIC_ROOT}/default/context/user/${UUID}-migrated.memory.md << EOF
---
id: ${UUID}
type: semantic
namespace: context/user
created: ${DATE}
title: "Migrated from Windsurf"
tags:
  - migrated
  - windsurf
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: migration
  agent: windsurf-cascade
  confidence: 0.9
---

# [Title]

[Your content here]
EOF
```

### Step 3: Update Windsurf Rules

Add mnemonic paths to your rules:

```markdown
Memory sources (in priority order):
1. ${MNEMONIC_ROOT}/default/ (mnemonic format)
2. .windsurf/memories/ (legacy)

For new memories, always use mnemonic format.
```

### Step 4: Validate

```bash
./tools/mnemonic-validate ${MNEMONIC_ROOT}/default/
```

See [Migration Guide](../community/migration-from-memory-bank.md) for complete details.

---

## Troubleshooting

### Rules Not Applied

**Symptom**: Cascade ignores mnemonic instructions

**Solutions**:
1. Check Settings > Cascade > Rules
2. Ensure rules are enabled
3. Restart Windsurf after changes
4. Try explicit memory commands

### Memory Files Not Created

**Symptom**: "Remember X" doesn't create files

**Solutions**:
1. Cascade may store internally first
2. Add explicit instruction: "Create a .memory.md file"
3. Check filesystem access permissions
4. Verify directory exists:
   ```bash
   mkdir -p ${MNEMONIC_ROOT}/default/context/user/
   ```

### Search Not Finding Memories

**Symptom**: "What do we know about X?" returns nothing

**Solutions**:
1. Verify memory path in rules
2. Check file permissions
3. Ensure `.memory.md` extension
4. Try: "Search files in ${MNEMONIC_ROOT}/ for X"

### Sync Issues

**Symptom**: Cascade memories don't match mnemonic files

**Solutions**:
1. Export and convert regularly
2. Use explicit file-based storage
3. Set mnemonic as primary source in rules

### Format Inconsistencies

**Symptom**: Created memories don't match MIF spec

**Solutions**:
1. Include full template in rules
2. Run validation after capture
3. Add format example to rules

---

## Sources

- [Windsurf Cascade Documentation](https://docs.windsurf.com/windsurf/cascade/cascade)
- [Codeium Documentation](https://codeium.com/documentation)
- [Memory Bank Migration](../community/migration-from-memory-bank.md)
- [MIF Level 3 Specification](../../skills/mnemonic-format/SKILL.md)
