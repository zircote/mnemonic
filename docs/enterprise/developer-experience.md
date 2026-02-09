# Developer Experience Guide

For individual developers and senior engineers who value privacy, control, and customization.

## Overview

Mnemonic puts you in control. Your memories stay local, use standard formats, and work with your existing tools. No accounts, no telemetry, no cloud dependencies.

---

## Privacy-First Design

### Zero Telemetry

Mnemonic collects nothing:

- No usage analytics
- No memory content transmission
- No network calls
- No account required
- No API keys needed

### Local Storage Only

```
${MNEMONIC_ROOT}/          # Your memories
${MNEMONIC_ROOT}/          # Project memories (optional)
```

That's it. Plain files on your filesystem.

### You Own Your Data

```bash
# See exactly what's stored
ls -la ${MNEMONIC_ROOT}/

# Read any memory with cat
cat ${MNEMONIC_ROOT}/default/decisions/user/*.memory.md

# Delete anything
rm ${MNEMONIC_ROOT}/default/learnings/user/unwanted.memory.md

# Export everything
tar -czf my-memories.tar.gz ${MNEMONIC_ROOT}/
```

---

## Human-Readable Format

### Standard Markdown

Every memory is a `.memory.md` file you can read and edit:

```yaml
---
id: 550e8400-e29b-41d4-a716-446655440000
type: semantic
namespace: decisions/user
created: 2026-01-23T10:30:00Z
title: "Use PostgreSQL for storage"
tags:
  - database
  - architecture
---

# Use PostgreSQL for Storage

We decided to use PostgreSQL because:
- Strong ACID compliance
- Excellent JSON support
- Mature ecosystem with great tooling
```

### Version Control Built-in

```bash
cd ${MNEMONIC_ROOT}
git log --oneline -10           # See recent changes
git diff HEAD~1                 # What changed?
git checkout HEAD~1 -- file.md  # Restore old version
git blame file.memory.md        # Who changed what?
```

---

## Power User Features

### Advanced Search

```bash
# Full-text search with ripgrep
rg -i "authentication" ${MNEMONIC_ROOT}/

# Search by namespace
rg -i "pattern" ${MNEMONIC_ROOT}/*/decisions/

# Search by memory type
rg "^type: episodic" ${MNEMONIC_ROOT}/ -l

# Search by tag
rg -l "^  - security" ${MNEMONIC_ROOT}/

# Recent memories (last 7 days)
find ${MNEMONIC_ROOT} -name "*.memory.md" -mtime -7

# Combine searches
rg -l "authentication" ${MNEMONIC_ROOT}/*/decisions/ | \
  xargs rg "JWT"
```

### Custom Scripts

Create your own memory tools:

```bash
#!/usr/bin/env bash
# quick-capture.sh - Fast memory capture

NAMESPACE="${1:-learnings}"
TITLE="$2"
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | head -c 50)

cat > ${MNEMONIC_ROOT}/default/${NAMESPACE}/user/${SLUG}.memory.md << EOF
---
id: ${UUID}
type: semantic
namespace: ${NAMESPACE}/user
created: ${DATE}
modified: ${DATE}
title: "${TITLE}"
tags: []
temporal:
  valid_from: ${DATE}
  recorded_at: ${DATE}
provenance:
  source_type: user_explicit
  agent: custom-script
  confidence: 1.0
---

# ${TITLE}

EOF

echo "Created: ${MNEMONIC_ROOT}/default/${NAMESPACE}/user/${SLUG}.memory.md"
```

### Unix Tool Integration

```bash
# Count memories by namespace
find ${MNEMONIC_ROOT} -name "*.memory.md" | \
  sed 's|.*/\([^/]*\)/[^/]*/.*|\1|' | sort | uniq -c

# Find largest memories
find ${MNEMONIC_ROOT} -name "*.memory.md" -exec wc -l {} + | sort -n | tail -10

# Extract all titles
rg "^title:" ${MNEMONIC_ROOT}/ | sed 's/.*title: "//' | sed 's/"$//'

# JSON export with yq
for f in ${MNEMONIC_ROOT}/**/*.memory.md; do
  yq -f extract '.title, .type, .created' "$f"
done
```

---

## Offline Capability

### No Network Required

Mnemonic works completely offline:

- No API calls to make
- No authentication to refresh
- No sync to wait for
- No rate limits

### Travel Mode

```bash
# On a plane? In a tunnel? Disconnected environment?
# Mnemonic works exactly the same.

/mnemonic:capture decisions "Use event sourcing for audit log"
/mnemonic:recall authentication
/mnemonic:search "database"

# All local, all instant
```

---

## Customization Options

### Namespace Organization

```bash
# Default namespaces
decisions/  patterns/  learnings/  blockers/  context/
apis/       security/  testing/    episodic/

# Add your own
mkdir -p ${MNEMONIC_ROOT}/default/research/user
mkdir -p ${MNEMONIC_ROOT}/default/bookmarks/user
```

### Memory Types

| Type | Use For | Decay Rate |
|------|---------|------------|
| **semantic** | Facts, decisions, specs | Slow (30 days) |
| **episodic** | Events, debugging sessions | Fast (7 days) |
| **procedural** | Workflows, how-tos | Medium (14 days) |

### Decay Model

Memories naturally fade based on age and access patterns:

```yaml
temporal:
  decay:
    model: exponential
    half_life: P7D      # Halves every 7 days
    strength: 0.85      # Current strength (0.0-1.0)
```

Override for important memories:

```yaml
temporal:
  decay:
    model: none         # Never decay
```

---

## Git Workflows

### Personal Memory Repository

```bash
# Initialize git (if not already)
cd ${MNEMONIC_ROOT}
git init

# Daily backup
git add .
git commit -m "Daily backup $(date +%Y-%m-%d)"

# Remote backup
git remote add origin git@github.com:yourname/memories.git
git push -u origin main
```

### Branch for Experiments

```bash
cd ${MNEMONIC_ROOT}
git checkout -b experiment/new-architecture

# Try new patterns, make decisions
# If it works, merge back
git checkout main
git merge experiment/new-architecture

# If not, discard
git branch -D experiment/new-architecture
```

### Time Travel

```bash
# What did I know last month?
git checkout HEAD~30 -- .

# Restore specific memory
git checkout HEAD~5 -- decisions/user/important.memory.md

# Compare memory evolution
git diff HEAD~10 -- patterns/user/auth.memory.md
```

---

## Performance Tips

### Fast Search

```bash
# Use ripgrep (10x faster than grep)
brew install ripgrep  # macOS
apt install ripgrep   # Ubuntu

# Limit search scope
rg "pattern" ${MNEMONIC_ROOT}/*/decisions/  # Not all namespaces

# Use file lists for large sets
rg -l "keyword" ${MNEMONIC_ROOT}/ | head -20  # Preview first
```

### Manage Memory Growth

```bash
# Check size
du -sh ${MNEMONIC_ROOT}/

# Archive old memories
/mnemonic:gc --compress --compress-threshold 100

# Remove expired TTL memories
/mnemonic:gc --ttl 90d

# Preview before cleanup
/mnemonic:gc --dry-run
```

---

## Validation & Quality

### Schema Validation

```bash
# Validate all memories
./tools/mnemonic-validate

# Check specific namespace
./tools/mnemonic-validate ${MNEMONIC_ROOT}/default/decisions/

# Capture validation as memory
./tools/mnemonic-validate --capture
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
./tools/mnemonic-validate --changed --fast-fail
```

---

## Comparison with Alternatives

### vs. Cloud-Based Memory

| Feature | Cloud Memory | Mnemonic |
|---------|-------------|----------|
| Privacy | Data on servers | 100% local |
| Offline | No | Yes |
| Telemetry | Usually yes | None |
| Lock-in | Vendor format | Open MIF |
| Cost | Subscription | Free |

### vs. Plain Markdown Files

| Feature | Plain Markdown | Mnemonic |
|---------|---------------|----------|
| Structure | Ad-hoc | Standardized |
| Validation | None | Schema validation |
| Integration | Manual | Claude Code plugin |
| Search | Basic grep | Intelligent recall |
| Metadata | None | Rich frontmatter |

---

## Quick Reference

```bash
# Capture
/mnemonic:capture decisions "Title here"

# Search
rg -i "topic" ${MNEMONIC_ROOT}/

# Recall (automatic, but manual option)
/mnemonic:recall --namespace decisions

# Status
/mnemonic:status

# Validate
./tools/mnemonic-validate

# Cleanup
/mnemonic:gc --compress
```

---

## Related Documentation

- [Productivity & ROI](./productivity-roi.md) - Team benefits
- [Compliance & Governance](./compliance-governance.md) - Enterprise controls
- [Research Validation](./research-validation.md) - Why it works
- [Main Documentation](../../README.md) - Full reference

[← Back to Enterprise Overview](./README.md)
