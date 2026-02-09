# Enterprise Deployment Guide

For platform teams, DevOps engineers, and IT administrators planning organization-wide rollout.

## Overview

Mnemonic is designed for zero-infrastructure deployment. This guide covers enterprise patterns for team coordination, backup, and governance.

---

## Deployment Architectures

### Individual Deployment (Default)

Each developer has their own memory store:

```
Developer Workstation
└── ${MNEMONIC_ROOT}/
    └── {org}/
        ├── decisions/user/
        ├── learnings/user/
        ├── patterns/user/
        └── ...
```

**Pros**: Simple, private, no coordination needed
**Cons**: No team memory sharing

### Team Shared Repository

Centralized memories via git:

```
Git Server (GitHub Enterprise / GitLab)
└── team-memories.git
    ├── decisions/team/
    ├── patterns/team/
    └── context/team/

Developer Workstation
└── ${MNEMONIC_ROOT}/
    ├── shared/              # Clone of team-memories.git
    │   ├── decisions/team/
    │   └── patterns/team/
    └── {org}/               # Personal memories
        └── learnings/user/
```

**Setup:**
```bash
# Each developer
git clone git@github.com:org/team-memories.git ${MNEMONIC_ROOT}/shared

# Sync daily
cd ${MNEMONIC_ROOT}/shared && git pull
```

### Organization Memory Hub

Multi-team architecture:

```
Git Server
├── org-decisions.git       # Company-wide decisions
├── security-policies.git   # Security team memories
├── team-a-memories.git     # Team A
├── team-b-memories.git     # Team B
└── ...

Developer Workstation
└── ${MNEMONIC_ROOT}/
    ├── org/                 # Clone of org-decisions
    ├── security/            # Clone of security-policies
    ├── team/                # Clone of team-X-memories
    └── personal/            # Local only
```

---

## Installation Methods

### Manual Installation

```bash
# Clone mnemonic plugin
git clone https://github.com/zircote/mnemonic.git ~/tools/mnemonic

# Register with Claude Code
claude settings plugins add ~/tools/mnemonic

# Initialize
/mnemonic:setup
```

### Scripted Installation

```bash
#!/bin/bash
# install-mnemonic.sh

MNEMONIC_VERSION="1.0.0"
INSTALL_DIR="$HOME/tools/mnemonic"

# Download
git clone --branch v${MNEMONIC_VERSION} \
  https://github.com/zircote/mnemonic.git "$INSTALL_DIR"

# Register
claude settings plugins add "$INSTALL_DIR"

# Initialize directories
mkdir -p ${MNEMONIC_ROOT}/default/{decisions,learnings,patterns,blockers,context,apis,security,testing,episodic}/{user,project,shared}

# Initialize git
cd ${MNEMONIC_ROOT}
git init
git add .
git commit -m "Initialize mnemonic"

echo "Mnemonic installed successfully"
```

### Configuration Management

**Ansible Example:**
```yaml
# roles/mnemonic/tasks/main.yml
- name: Clone mnemonic
  git:
    repo: https://github.com/zircote/mnemonic.git
    dest: "{{ ansible_env.HOME }}/tools/mnemonic"
    version: "v1.0.0"

- name: Create memory directories
  file:
    path: "{{ ansible_env.HOME }}/.claude/mnemonic/default/{{ item }}/user"
    state: directory
  loop:
    - decisions
    - learnings
    - patterns
    - blockers
    - context

- name: Initialize git repository
  command: git init
  args:
    chdir: "{{ ansible_env.HOME }}/.claude/mnemonic"
    creates: "{{ ansible_env.HOME }}/.claude/mnemonic/.git"
```

---

## Git Server Integration

### GitHub Enterprise

```bash
# Create organization repository
gh repo create org/shared-memories --private

# Clone to shared location
git clone git@github.com:org/shared-memories.git ${MNEMONIC_ROOT}/shared

# Add branch protection
gh api repos/org/shared-memories/branches/main/protection \
  -X PUT \
  -f required_pull_request_reviews.required_approving_review_count=1
```

### GitLab

```bash
# Create project
glab project create shared-memories --group org --private

# Clone
git clone git@gitlab.com:org/shared-memories.git ${MNEMONIC_ROOT}/shared

# Configure merge request approvals
glab mr approval-rule create \
  --name "Memory Review" \
  --approvals-required 1 \
  --project org/shared-memories
```

### Self-Hosted Git

```bash
# Gitea, Gogs, or bare git server
git clone git@git.internal:memories/shared.git ${MNEMONIC_ROOT}/shared
```

---

## Backup Strategies

### Local Backup

```bash
# Cron job for daily backup
# Add to crontab: crontab -e
0 2 * * * tar -czf ~/backups/mnemonic-$(date +\%Y\%m\%d).tar.gz ${MNEMONIC_ROOT}/

# Keep last 30 backups
find ~/backups -name "mnemonic-*.tar.gz" -mtime +30 -delete
```

### Git Remote Backup

```bash
# Add backup remote
cd ${MNEMONIC_ROOT}
git remote add backup git@backup-server:mnemonic.git

# Push to backup (cron job)
0 3 * * * cd ${MNEMONIC_ROOT} && git push backup main

# Or push to multiple remotes
git remote set-url --add --push origin git@github.com:user/mnemonic.git
git remote set-url --add --push origin git@backup:mnemonic.git
```

### Cloud Sync (Optional)

```bash
# Dropbox/iCloud/OneDrive
ln -s ${MNEMONIC_ROOT} ~/Dropbox/mnemonic-backup

# Or rsync to cloud storage
rsync -avz ${MNEMONIC_ROOT}/ s3://bucket/mnemonic/
```

---

## Disaster Recovery

### Full Restore

```bash
# From tar backup
tar -xzf ~/backups/mnemonic-20260124.tar.gz -C ~/

# From git remote
git clone git@backup-server:mnemonic.git ${MNEMONIC_ROOT}
```

### Point-in-Time Recovery

```bash
cd ${MNEMONIC_ROOT}

# Find commit from desired date
git log --before="2026-01-20" --oneline | head -1

# Restore to that point
git checkout abc123 -- .

# Or create branch from that point
git checkout -b recovery-20260120 abc123
```

### Corruption Recovery

```bash
# If git is corrupted
rm -rf ${MNEMONIC_ROOT}/.git
git init
git add .
git commit -m "Recover from corruption"

# Re-add remote
git remote add origin git@github.com:user/mnemonic.git
```

---

## Team Memory Sharing

### Namespace Strategy

```
${MNEMONIC_ROOT}/
├── org/                    # Organization-wide (read-only for most)
│   ├── decisions/shared/   # Company architectural decisions
│   ├── patterns/shared/    # Standard code patterns
│   └── security/shared/    # Security policies
├── team/                   # Team-specific (read-write for team)
│   ├── decisions/team/     # Team decisions
│   ├── patterns/team/      # Team patterns
│   └── context/team/       # Project context
└── personal/               # Individual (private)
    ├── learnings/user/     # Personal learnings
    └── episodic/user/      # Personal experiences
```

### Contribution Workflow

```bash
# Developer wants to share a pattern
cd ${MNEMONIC_ROOT}/team

# Create memory
cat > patterns/team/uuid-new-pattern.memory.md << 'EOF'
---
id: uuid-here
type: procedural
namespace: patterns/team
...
EOF

# Submit for review
git add patterns/team/uuid-new-pattern.memory.md
git commit -m "Add API pagination pattern"
git push origin feature/pagination-pattern

# Create PR for review
gh pr create --title "Add pagination pattern" --body "..."
```

### Access Control

**CODEOWNERS file:**
```
# .github/CODEOWNERS
decisions/shared/*.memory.md  @org/architects
security/shared/*.memory.md   @org/security-team
patterns/shared/*.memory.md   @org/tech-leads
```

**Branch protection:**
- Require PR reviews for shared memories
- Require specific team approval for security namespace
- Allow direct push for personal namespace

---

## Migration Strategies

### From Memory Bank

```bash
# Use migration tool
./tools/migrate-memory-bank \
  --source ~/old-memory-bank \
  --target ${MNEMONIC_ROOT}/default \
  --namespace learnings
```

### From Other Systems

```bash
# Generic markdown migration
for f in ~/old-memories/*.md; do
  UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
  DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  TITLE=$(head -1 "$f" | sed 's/^# //')

  cat > ${MNEMONIC_ROOT}/default/context/user/${UUID}-migrated.memory.md << EOF
---
id: ${UUID}
type: semantic
namespace: context/user
created: ${DATE}
title: "${TITLE}"
tags: [migrated]
---

$(cat "$f")
EOF
done
```

### Validation After Migration

```bash
# Validate all migrated memories
./tools/mnemonic-validate ${MNEMONIC_ROOT}/

# Check for errors
./tools/mnemonic-validate --format json | jq '.summary'
```

---

## Monitoring

### Memory System Health

```bash
#!/bin/bash
# health-check.sh

MEMORY_DIR="$MNEMONIC_ROOT"

# Count by namespace
echo "=== Memory Counts ==="
find "$MEMORY_DIR" -name "*.memory.md" | \
  sed 's|.*/\([^/]*\)/[^/]*/.*|\1|' | sort | uniq -c

# Total size
echo -e "\n=== Total Size ==="
du -sh "$MEMORY_DIR"

# Recent activity
echo -e "\n=== Last 5 Changes ==="
cd "$MEMORY_DIR" && git log --oneline -5

# Validation status
echo -e "\n=== Validation ==="
./tools/mnemonic-validate --format json 2>/dev/null | \
  jq -r '"Valid: \(.summary.valid), Errors: \(.summary.errors)"'
```

### Alerting

```bash
# Add to monitoring system
# Alert if validation errors > 0
./tools/mnemonic-validate --format json | jq -e '.summary.errors == 0'
```

---

## Security Hardening

### Filesystem Permissions

```bash
# Restrict access
chmod 700 ${MNEMONIC_ROOT}
chmod 600 ${MNEMONIC_ROOT}/**/*.memory.md

# Shared directories (read-only for team members)
chmod 750 ${MNEMONIC_ROOT}/shared
chmod 640 ${MNEMONIC_ROOT}/shared/**/*.memory.md
```

### Git Signing

```bash
cd ${MNEMONIC_ROOT}

# Configure signing
git config commit.gpgsign true
git config user.signingkey YOUR_GPG_KEY

# Verify signatures
git log --show-signature -5
```

### Sensitive Data

```bash
# Add to .gitignore
echo "security/private/*" >> ${MNEMONIC_ROOT}/.gitignore

# Or use git-crypt for encryption
git-crypt init
echo "security/**/*.memory.md filter=git-crypt" >> .gitattributes
```

---

## Performance Tuning

### Large Memory Sets

```bash
# Use indexed search for 10k+ memories
# Consider organizing by date
mkdir -p ${MNEMONIC_ROOT}/archive/2025
mv ${MNEMONIC_ROOT}/default/episodic/user/2025-* ${MNEMONIC_ROOT}/archive/2025/

# Limit search scope
rg "pattern" ${MNEMONIC_ROOT}/default/  # Not archive
```

### Git Performance

```bash
cd ${MNEMONIC_ROOT}

# Pack repository
git gc --aggressive

# Shallow clone for shared repos
git clone --depth 100 git@github.com:org/shared.git shared

# Sparse checkout for large repos
git sparse-checkout init
git sparse-checkout set decisions patterns
```

---

## Rollout Checklist

### Pre-Rollout

- [ ] Choose deployment architecture (individual/team/org)
- [ ] Set up git server repository (if team/org)
- [ ] Create namespace structure
- [ ] Define access controls (CODEOWNERS)
- [ ] Prepare installation scripts
- [ ] Set up backup automation
- [ ] Create monitoring/alerting

### Pilot (Week 1)

- [ ] Install on 3-5 pilot users
- [ ] Capture initial memories
- [ ] Validate format compliance
- [ ] Gather feedback
- [ ] Refine namespace structure

### Team Rollout (Week 2-3)

- [ ] Roll out to full team
- [ ] Set up shared repository
- [ ] Establish contribution workflow
- [ ] Configure CI validation
- [ ] Train team on workflows

### Organization Rollout (Month 2+)

- [ ] Expand to additional teams
- [ ] Create org-wide decision repository
- [ ] Establish governance policies
- [ ] Set up cross-team sharing
- [ ] Document best practices

---

## Troubleshooting

### Common Issues

**Git conflicts on shared memories:**
```bash
cd ${MNEMONIC_ROOT}/shared
git fetch origin
git rebase origin/main
# Resolve conflicts, then:
git rebase --continue
```

**Disk space issues:**
```bash
# Compress old memories
/mnemonic:gc --compress

# Archive old episodic memories
mv ${MNEMONIC_ROOT}/default/episodic/user/old-* ~/archive/
```

**Slow search:**
```bash
# Check ripgrep is installed
which rg || brew install ripgrep

# Use namespace filtering
rg "pattern" ${MNEMONIC_ROOT}/default/decisions/  # Faster
```

---

## Related Documentation

- [Compliance & Governance](./compliance-governance.md) - Security controls
- [Productivity & ROI](./productivity-roi.md) - Team benefits
- [Validation Tool](../validation.md) - Schema validation
- [Integrations](../integrations/README.md) - Tool setup

[← Back to Enterprise Overview](./README.md)
