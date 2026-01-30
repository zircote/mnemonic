# Quick Start for Memory Bank Users

Already using markdown files for AI memory? You're 5 minutes away from mnemonic.

---

## What You Already Know

If you've been using Memory Bank patterns, you've already discovered:

- Markdown files work for AI memory
- Filesystem storage is reliable
- Your AI assistant can read and write context
- Version control with git is valuable

**Mnemonic validates your approach** and adds standardization.

---

## The 5-Minute Setup

### Step 1: Install the Plugin

```bash
# Clone mnemonic
git clone https://github.com/zircote/mnemonic.git ~/tools/mnemonic

# Register with Claude Code
claude settings plugins add ~/tools/mnemonic
```

### Step 2: Initialize

```bash
# Start Claude Code and run setup
/mnemonic:setup
```

This creates:
```
${MNEMONIC_ROOT}/
├── default/
│   ├── decisions/user/
│   ├── learnings/user/
│   ├── patterns/user/
│   ├── blockers/user/
│   ├── context/user/
│   ├── apis/user/
│   ├── security/user/
│   ├── testing/user/
│   └── episodic/user/
└── .blackboard/
```

### Step 3: Migrate Your Existing Files

```bash
# Quick migration - copy your existing memory files
cp ~/your-memory-bank/*.md ${MNEMONIC_ROOT}/default/context/user/

# Or use the migration tool for proper conversion
./tools/migrate-memory-bank \
  --source ~/your-memory-bank \
  --target ${MNEMONIC_ROOT}/default
```

### Step 4: Start Using It

```bash
# Capture a new decision
/mnemonic:capture decisions "Use PostgreSQL for storage"

# Search your memories
/mnemonic:search "authentication"

# Check status
/mnemonic:status
```

---

## What Changes (And What Doesn't)

### What Stays the Same

| Your Approach | With Mnemonic |
|---------------|---------------|
| Plain markdown files | Still plain markdown |
| Stored on filesystem | Still on filesystem |
| Human-readable | Still human-readable |
| Git-versioned | Still git-versioned |
| Your editor works | Your editor still works |

### What You Gain

| Feature | Before | After |
|---------|--------|-------|
| **Structure** | Ad-hoc | Standardized (MIF Level 3) |
| **Validation** | None | Schema validation tool |
| **Cross-tool** | Manual setup per tool | Works with 9+ tools |
| **Decay model** | Static | Automatic relevance decay |
| **Research backing** | Your intuition | 74% benchmark accuracy |

---

## Format Comparison

### Your Current Format (Typical)

```markdown
# Project Context

We're building an API gateway.

## Decisions
- Use JWT for auth
- PostgreSQL for storage

## Notes
- Fixed the N+1 bug on 2025-01-15
```

### Mnemonic Format (MIF Level 3)

```yaml
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
namespace: decisions/user
created: 2026-01-23T10:30:00Z
title: "Use JWT for Authentication"
tags:
  - authentication
  - security
temporal:
  valid_from: 2026-01-23T10:30:00Z
  recorded_at: 2026-01-23T10:30:00Z
provenance:
  source_type: conversation
  agent: claude-opus-4
  confidence: 0.95
---

# Use JWT for Authentication

We decided to use JWT tokens because:
- Stateless authentication fits our microservices architecture
- Standard library support in all our languages
- Easy integration with API gateway
```

**Key difference**: Structured metadata in YAML frontmatter.

---

## Common Migration Patterns

### Pattern 1: Single Context File → Multiple Memories

**Before**: One large `context.md` with everything

**After**: Separate files by type
```bash
# Create separate memories for each decision
/mnemonic:capture decisions "Use JWT for auth"
/mnemonic:capture decisions "Use PostgreSQL for storage"
/mnemonic:capture patterns "Error handling pattern"
```

### Pattern 2: Project-Specific → Namespaced

**Before**: `~/project-a/memory-bank/`

**After**: `${MNEMONIC_ROOT}/project-a/decisions/user/`

```bash
# Create project-specific namespace
mkdir -p ${MNEMONIC_ROOT}/project-a/{decisions,patterns,learnings}/user
```

### Pattern 3: Unstructured Notes → Typed Memories

**Before**: Generic notes mixed together

**After**: Typed by memory category
- `semantic` - Facts, decisions, specifications
- `episodic` - Events, debugging sessions
- `procedural` - Workflows, patterns

---

## Keep Your Existing Setup

You don't have to choose. Mnemonic can coexist with your current approach:

```
${MNEMONIC_ROOT}/           # Mnemonic memories
~/your-memory-bank/           # Keep your existing setup

# Mnemonic reads both if you configure it
```

Or gradually migrate:
1. Start capturing new memories in mnemonic format
2. Migrate old memories when you touch them
3. Eventually consolidate

---

## Validation

Check your migrated memories:

```bash
# Validate all memories
./tools/mnemonic-validate

# See any format issues
./tools/mnemonic-validate --format json | jq '.errors'
```

---

## Next Steps

- [Full Migration Guide](./migration-from-memory-bank.md) - Detailed walkthrough
- [Comparison](./mnemonic-vs-memory-bank.md) - Side-by-side differences
- [Main Documentation](../../README.md) - Complete reference

---

## Questions?

- **GitHub Issues**: [Report problems](https://github.com/zircote/mnemonic/issues)
- **Discussions**: [Ask questions](https://github.com/zircote/mnemonic/discussions)

[← Back to Community](./README.md)
