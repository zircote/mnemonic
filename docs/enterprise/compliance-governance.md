# Compliance & Governance Guide

For enterprise architects, compliance officers, and security teams.

## Overview

Mnemonic provides enterprise-grade AI memory with complete audit capabilities, data sovereignty, and governance controls—all without external dependencies.

---

## Audit Trail Architecture

### Git-Based Version Control

Every memory change is tracked with full git history:

```bash
# View memory change history
cd ${MNEMONIC_ROOT}
git log --oneline -20

# See who changed what
git log --pretty=format:"%h %an %ad %s" --date=short

# View specific memory evolution
git log -p path/to/memory.memory.md

# Compare versions
git diff HEAD~5 HEAD -- decisions/user/
```

### What Gets Tracked

| Event | Git Record | Details |
|-------|------------|---------|
| Memory created | New file commit | Author, timestamp, content |
| Memory modified | File change commit | Diff shows exact changes |
| Memory deleted | File removal commit | Preserved in history |
| Batch operations | Grouped commits | gc, compression, etc. |

### Audit Query Examples

```bash
# All changes by a specific user
git log --author="engineer@company.com" --oneline

# Changes in date range
git log --after="2026-01-01" --before="2026-02-01" --oneline

# Changes to decision memories
git log --oneline -- decisions/

# Search for changes mentioning "authentication"
git log -S "authentication" --oneline
```

---

## Data Sovereignty

### Local-Only Storage

All data stays on your infrastructure:

```
${MNEMONIC_ROOT}/           # User-level memories
${MNEMONIC_ROOT}/           # Project-level memories
```

**No external dependencies:**
- No cloud services
- No API calls
- No telemetry
- No account required
- No network access needed

### Data Residency Compliance

| Requirement | How Mnemonic Complies |
|-------------|----------------------|
| **Data stays in jurisdiction** | Filesystem storage only |
| **No cross-border transfers** | No network communication |
| **Right to deletion** | `rm` or git operations |
| **Data portability** | Standard markdown files |
| **Access control** | Filesystem permissions |

### Encryption Options

Mnemonic stores plain-text markdown for human readability. For encryption:

```bash
# Encrypt at rest with filesystem encryption
# macOS: FileVault
# Linux: LUKS, eCryptfs
# Windows: BitLocker

# Or use git-crypt for repository encryption
cd ${MNEMONIC_ROOT}
git-crypt init
echo "*.memory.md filter=git-crypt diff=git-crypt" >> .gitattributes
```

---

## Compliance Framework Alignment

### SOC 2

| Trust Principle | Mnemonic Support |
|-----------------|------------------|
| **Security** | Filesystem permissions, no external access |
| **Availability** | Local storage, no network dependency |
| **Processing Integrity** | Git versioning, validation tool |
| **Confidentiality** | Local-only, encryption-ready |
| **Privacy** | No data collection, no telemetry |

### ISO 27001

| Control Area | Implementation |
|--------------|----------------|
| **A.8 Asset Management** | Memory files are versioned assets |
| **A.9 Access Control** | Filesystem permissions |
| **A.12 Operations Security** | Validation tool, gc commands |
| **A.14 System Acquisition** | Open source, auditable code |
| **A.18 Compliance** | Local storage, audit logs |

### GDPR Considerations

| Right | Implementation |
|-------|----------------|
| **Right to Access** | `cat memory.md` - human readable |
| **Right to Rectification** | Direct file editing |
| **Right to Erasure** | `rm` or `git rm` |
| **Right to Portability** | Standard markdown export |
| **Data Minimization** | gc with TTL policies |

---

## Retention & Lifecycle Policies

### Garbage Collection

```bash
# Clean up expired memories (TTL-based)
/mnemonic:gc --ttl 90d

# Archive low-strength memories
/mnemonic:gc --min-strength 0.3

# Compress large old memories
/mnemonic:gc --compress

# Dry run to preview changes
/mnemonic:gc --dry-run
```

### Policy Configuration

Define retention policies in your organization's CLAUDE.md:

```markdown
## Memory Retention Policy

- **Decisions**: Retain indefinitely (semantic, slow decay)
- **Learnings**: 1 year retention
- **Episodic**: 90 days retention
- **Blockers**: Archive after resolution + 30 days
```

### Bi-Temporal Tracking

Mnemonic implements SQL:2011 temporal patterns:

```yaml
temporal:
  valid_from: 2026-01-15T00:00:00Z    # When this became true
  recorded_at: 2026-01-20T10:30:00Z   # When we recorded it
```

This supports:
- **Corrections**: Update valid_from without losing when you learned it
- **Audit**: Distinguish between truth time and knowledge time
- **Compliance**: Full temporal audit trail

---

## Data Quality Assurance

### Schema Validation

```bash
# Validate all memories against MIF Level 3 schema
./tools/mnemonic-validate

# CI-friendly JSON output
./tools/mnemonic-validate --format json

# Validate only changed files
./tools/mnemonic-validate --changed
```

### Validation Checks

| Check | Purpose |
|-------|---------|
| **Required fields** | Ensure complete metadata |
| **UUID format** | Unique identification |
| **ISO 8601 timestamps** | Standard date format |
| **Type enumeration** | semantic/episodic/procedural |
| **Provenance** | Track data origin |

### Automated Validation

Add to CI/CD pipeline:

```yaml
# .github/workflows/validate-memories.yml
name: Validate Memories
on:
  push:
    paths: ['**/*.memory.md']
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate memories
        run: ./tools/mnemonic-validate --format json
```

---

## Security Model

### Access Control

```bash
# Restrict access to memory directory
chmod 700 ${MNEMONIC_ROOT}

# Read-only for shared memories
chmod 444 ${MNEMONIC_ROOT}/shared/*.memory.md
```

### Threat Model

| Threat | Mitigation |
|--------|------------|
| **Unauthorized access** | Filesystem permissions |
| **Data exfiltration** | No network access |
| **Tampering** | Git signatures (`git commit -S`) |
| **Data loss** | Git remote backup |
| **Injection attacks** | Markdown sanitization |

### Git Signing

For tamper-evident audit trails:

```bash
cd ${MNEMONIC_ROOT}
git config commit.gpgsign true
git config user.signingkey YOUR_KEY_ID
```

---

## Enterprise Deployment Patterns

### Centralized Memory Repository

```
Git Server (GitHub Enterprise / GitLab)
         │
         ├── org/mnemonic-decisions (shared decisions)
         ├── org/mnemonic-patterns (shared patterns)
         └── user/* (individual memories)
```

### Team Memory Sharing

```bash
# Clone shared memory repository
git clone git@github.com:org/shared-memories.git ${MNEMONIC_ROOT}/shared

# Pull latest shared memories
cd ${MNEMONIC_ROOT}/shared && git pull

# Contribute to shared memories
git add new-pattern.memory.md
git commit -m "Add authentication pattern"
git push
```

### Backup Strategy

```bash
# Automated backup
0 2 * * * tar -czf ~/backups/mnemonic-$(date +%Y%m%d).tar.gz ${MNEMONIC_ROOT}/

# Git remote backup
cd ${MNEMONIC_ROOT}
git remote add backup git@backup-server:mnemonic.git
git push backup main
```

---

## Governance Controls

### Memory Classification

Use namespaces for access control:

| Namespace | Classification | Access |
|-----------|---------------|--------|
| `security/` | Confidential | Security team only |
| `decisions/` | Internal | Engineering team |
| `patterns/` | Public | All developers |
| `personal/` | Private | Individual only |

### Review Workflows

Require PR review for shared memories:

```yaml
# .github/CODEOWNERS
decisions/*.memory.md @engineering-leads
security/*.memory.md @security-team
patterns/*.memory.md @architects
```

### Provenance Tracking

Every memory includes origin information:

```yaml
provenance:
  source_type: conversation    # How it was captured
  agent: claude-opus-4         # Which model
  confidence: 0.95             # Confidence score
```

---

## Monitoring & Alerting

### Memory System Health

```bash
# Count memories by namespace
find ${MNEMONIC_ROOT} -name "*.memory.md" | \
  sed 's|.*/\([^/]*\)/[^/]*/[^/]*$|\1|' | sort | uniq -c

# Check for validation errors
./tools/mnemonic-validate --format json | jq '.summary.errors'

# Monitor memory growth
du -sh ${MNEMONIC_ROOT}/
```

### Audit Log Export

```bash
# Export audit log for compliance review
cd ${MNEMONIC_ROOT}
git log --pretty=format:'%H,%an,%ae,%ad,%s' --date=iso > audit-log.csv
```

---

## Related Documentation

- [Research Validation](./research-validation.md) - Academic foundations
- [Deployment Guide](./deployment-guide.md) - Enterprise rollout
- [Validation Tool](../validation.md) - Schema validation details
- [ADR-001](../adrs/adr-001-filesystem-based-storage.md) - Storage architecture decision

[← Back to Enterprise Overview](./README.md)
