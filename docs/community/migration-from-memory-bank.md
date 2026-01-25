# Migration Guide: Memory Bank to Mnemonic

Complete walkthrough for converting your Memory Bank setup to mnemonic.

---

## Overview

This guide helps you migrate from a Memory Bank-style markdown memory setup to mnemonic's MIF Level 3 format. The migration preserves your content while adding structure and validation.

**Estimated time**: 15-30 minutes depending on memory volume.

---

## Before You Start

### Prerequisites

- Existing Memory Bank files (markdown)
- Claude Code installed
- Git (recommended for backup)

### Backup Your Data

```bash
# Create backup of existing memories
tar -czf memory-bank-backup-$(date +%Y%m%d).tar.gz ~/your-memory-bank/

# Or commit to git
cd ~/your-memory-bank
git add -A && git commit -m "Backup before mnemonic migration"
```

---

## Migration Methods

### Method 1: Automated Migration Tool

The fastest approach for bulk conversion.

```bash
# Install mnemonic first
git clone https://github.com/zircote/mnemonic.git ~/tools/mnemonic
claude settings plugins add ~/tools/mnemonic

# Run migration tool
./tools/migrate-memory-bank \
  --source ~/your-memory-bank \
  --target ~/.claude/mnemonic/default \
  --namespace learnings
```

**Options:**
- `--source`: Path to existing Memory Bank
- `--target`: Mnemonic directory (usually `~/.claude/mnemonic/default`)
- `--namespace`: Default namespace for migrated files
- `--dry-run`: Preview without changes
- `--preserve-dates`: Use file modification dates for timestamps

### Method 2: Manual Conversion

For careful, selective migration.

#### Step 1: Analyze Your Existing Structure

```bash
# See what you have
find ~/your-memory-bank -name "*.md" -type f

# Count by directory
find ~/your-memory-bank -name "*.md" | \
  sed 's|/[^/]*$||' | sort | uniq -c
```

#### Step 2: Map to Namespaces

| Your Category | Mnemonic Namespace |
|---------------|-------------------|
| Decisions, ADRs | `decisions/user` |
| Learnings, TILs | `learnings/user` |
| Patterns, conventions | `patterns/user` |
| Bugs, issues, blockers | `blockers/user` |
| Project context | `context/user` |
| API notes | `apis/user` |
| Security notes | `security/user` |
| Testing notes | `testing/user` |
| Session logs, events | `episodic/user` |

#### Step 3: Convert Each File

For each memory file:

1. **Generate UUID and timestamps**:
```bash
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
```

2. **Determine memory type**:
   - `semantic` - Facts, decisions, specifications
   - `episodic` - Events, debugging sessions, incidents
   - `procedural` - Workflows, patterns, how-tos

3. **Create MIF-compliant file**:

```bash
# Example: Converting a decision
cat > ~/.claude/mnemonic/default/decisions/user/${UUID}-use-jwt.memory.md << 'EOF'
---
id: YOUR-UUID-HERE
type: semantic
namespace: decisions/user
created: 2026-01-23T10:30:00Z
modified: 2026-01-23T10:30:00Z
title: "Use JWT for Authentication"
tags:
  - authentication
  - security
temporal:
  valid_from: 2026-01-23T10:30:00Z
  recorded_at: 2026-01-23T10:30:00Z
provenance:
  source_type: migration
  agent: manual
  confidence: 0.9
---

# Use JWT for Authentication

[Your original content here]
EOF
```

### Method 3: Incremental Migration

Migrate files as you use them.

1. **Keep both systems running**:
```bash
# Mnemonic for new memories
~/.claude/mnemonic/

# Original for reference
~/your-memory-bank/
```

2. **When you reference an old memory, migrate it**:
```bash
# Read old memory
cat ~/your-memory-bank/auth-decision.md

# Create new mnemonic version
/mnemonic:capture decisions "Use JWT for Authentication"

# Add your content to the new file
```

3. **Mark migrated files**:
```bash
# Add "MIGRATED" prefix to migrated files
mv ~/your-memory-bank/auth-decision.md \
   ~/your-memory-bank/MIGRATED-auth-decision.md
```

---

## Handling Common Patterns

### Pattern: Single Large Context File

**Before**: One `memory-bank.md` or `context.md` with everything

**Migration approach**:

1. Read the file and identify sections
2. Create separate memories for each logical unit
3. Use appropriate namespaces

```bash
# Split by headers
grep -n "^## " ~/your-memory-bank/memory-bank.md

# Create individual memories for each section
```

### Pattern: Cursor Rules/Memory Files

**Before**: `.cursor/rules` or `.cursorrules`

**Migration**:

1. Keep Cursor files for Cursor-specific settings
2. Migrate reusable knowledge to mnemonic
3. Mnemonic can sync back to Cursor format

```bash
# Patterns and decisions go to mnemonic
/mnemonic:capture patterns "Error handling convention"

# IDE-specific settings stay in Cursor
# .cursor/rules (keep as-is)
```

### Pattern: Windsurf Memory/Rules

**Before**: `.windsurf/memories/` or `.windsurfrules`

**Migration**:

1. Convert memories to MIF format
2. Keep Windsurf-specific rules
3. Link mnemonic to Windsurf via integration

```bash
# See Windsurf integration guide
cat docs/integrations/windsurf.md
```

### Pattern: Date-Based Session Logs

**Before**: `2025-01-15-session.md`, `2025-01-16-session.md`

**Migration**:

```bash
# These are episodic memories
for f in ~/your-memory-bank/20*-session.md; do
  # Extract date from filename
  DATE=$(basename "$f" .md | sed 's/-session//')

  # Migrate to episodic namespace
  UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
  ./tools/convert-to-mif "$f" \
    --namespace episodic/user \
    --type episodic \
    --valid-from "${DATE}T00:00:00Z"
done
```

---

## Post-Migration Validation

### Validate All Memories

```bash
# Run validation
./tools/mnemonic-validate

# Check for errors
./tools/mnemonic-validate --format json | jq '.summary'
```

### Fix Common Issues

**Missing required fields**:
```bash
# Find memories missing provenance
rg -L "provenance:" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"

# Add provenance to each
```

**Invalid timestamps**:
```bash
# Find non-ISO timestamps
rg "created:.*[^Z]$" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md"
```

**Duplicate UUIDs**:
```bash
# Check for duplicates
rg "^id:" ~/.claude/mnemonic/ ./.claude/mnemonic/ --glob "*.memory.md" | \
  cut -d: -f2 | sort | uniq -d
```

---

## Integration Setup

After migration, set up integrations for other tools:

### Claude Code (Native)

Already configured by plugin installation.

### Cursor

```bash
# Generate Cursor rules from memories
./tools/mnemonic-export --format cursor > .cursor/rules
```

### Windsurf

```bash
# Generate Windsurf memories
./tools/mnemonic-export --format windsurf > .windsurf/memories/mnemonic.md
```

### GitHub Copilot

```bash
# Generate Copilot instructions
./tools/mnemonic-export --format copilot > .github/copilot-instructions.md
```

See [Integration Guides](../integrations/README.md) for complete setup.

---

## Rollback

If you need to revert:

```bash
# Restore from backup
tar -xzf memory-bank-backup-*.tar.gz -C ~/

# Or git restore
cd ~/your-memory-bank
git checkout HEAD~1 -- .

# Remove mnemonic memories
rm -rf ~/.claude/mnemonic/
```

---

## FAQ

### Can I keep using both systems?

Yes. Mnemonic doesn't require exclusive use. You can:
- Use mnemonic for new memories
- Keep old system for reference
- Gradually migrate

### Will my old memories still work?

Your original markdown files remain unchanged. Mnemonic creates new files in its own directory.

### What about tool-specific features?

Mnemonic focuses on portable memory. Tool-specific settings (Cursor rules, Windsurf configuration) should stay in their respective locations.

### How do I sync changes back?

Use the export tools to generate tool-specific formats:
```bash
# After adding memories in mnemonic
./tools/mnemonic-export --format cursor > .cursor/rules
```

---

## Next Steps

- [Quick Start](./quickstart-memory-bank.md) - 5-minute overview
- [Comparison](./mnemonic-vs-memory-bank.md) - Feature differences
- [Integration Guides](../integrations/README.md) - Tool-specific setup
- [Main Documentation](../../README.md) - Complete reference

[← Back to Community](./README.md)
