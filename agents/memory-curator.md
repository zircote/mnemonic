---
name: memory-curator
description: Autonomous memory maintenance and curation agent for conflict detection, deduplication, and decay management
trigger: Proactively when memory conflicts detected or maintenance needed
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---

# Memory Curator Agent

Autonomous agent for memory maintenance, conflict detection, deduplication, and decay management.

## Purpose

The memory-curator agent performs background maintenance on the mnemonic memory system:

1. **Conflict Detection**: Find memories that may contradict each other
2. **Deduplication**: Identify and merge duplicate memories
3. **Decay Management**: Update relevance scores based on access patterns
4. **Relationship Integrity**: Ensure memory links are valid
5. **Cleanup**: Archive or remove orphaned/expired content

<!-- BEGIN MNEMONIC PROTOCOL -->

## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.

<!-- END MNEMONIC PROTOCOL -->

## Trigger Conditions

Invoke this agent when:
- Memory count exceeds threshold (e.g., 100+ in a namespace)
- Potential conflicts detected during capture
- Scheduled maintenance (weekly/monthly)
- User requests memory cleanup

## Tasks

### 1. Conflict Detection

Find memories with similar titles or contradictory content:

```bash
# Find memories with similar titles in same namespace
for ns in _semantic/decisions _semantic/knowledge _procedural/patterns; do
    echo "=== Checking $ns for conflicts ==="

    # Get all titles
    titles=$(rg "^title:" ${MNEMONIC_ROOT} --path "*/$ns/" --glob "*.memory.md" -o 2>/dev/null | \
             sed 's/.*title: "//' | sed 's/"$//' | sort)

    # Find near-duplicates (simplified)
    echo "$titles" | uniq -d
done
```

**Resolution strategies:**
- **Merge**: Combine information from both memories
- **Invalidate**: Mark older memory as superseded
- **Skip**: Keep both if they represent different valid states

### 2. Deduplication

Identify memories that are effectively duplicates:

```bash
# Find files with very similar content
for f1 in ${MNEMONIC_ROOT}/**/*.memory.md; do
    for f2 in ${MNEMONIC_ROOT}/**/*.memory.md; do
        [ "$f1" = "$f2" ] && continue

        # Compare content similarity (excluding frontmatter)
        similarity=$(diff <(sed '1,/^---$/d' "$f1" | sed '/^---$/,$d') \
                         <(sed '1,/^---$/d' "$f2" | sed '/^---$/,$d') | \
                    wc -l)

        if [ "$similarity" -lt 10 ]; then
            echo "Potential duplicate: $f1 <-> $f2"
        fi
    done
done
```

**Merge procedure:**
1. Identify the more complete/recent memory
2. Combine unique information from both
3. Update relationships to point to merged memory
4. Archive the duplicate

### 3. Decay Management

Update relevance scores based on time and access:

```python
import os
import re
from datetime import datetime, timezone
from pathlib import Path

def update_decay_scores(mnemonic_path: Path):
    """Update strength scores based on decay model."""
    now = datetime.now(timezone.utc)

    for memory_file in mnemonic_path.rglob("*.memory.md"):
        content = memory_file.read_text()

        # Extract decay parameters
        half_life_match = re.search(r'half_life: P(\d+)D', content)
        last_access_match = re.search(r'last_accessed: (\S+)', content)
        strength_match = re.search(r'strength: ([\d.]+)', content)

        if not all([half_life_match, last_access_match, strength_match]):
            continue

        half_life_days = int(half_life_match.group(1))
        last_accessed = datetime.fromisoformat(last_access_match.group(1).replace('Z', '+00:00'))
        current_strength = float(strength_match.group(1))

        # Calculate new strength: strength * 0.5^(days_since_access / half_life)
        days_since = (now - last_accessed).days
        decay_factor = 0.5 ** (days_since / half_life_days)
        new_strength = current_strength * decay_factor

        # Update if significantly different
        if abs(new_strength - current_strength) > 0.01:
            new_content = re.sub(
                r'strength: [\d.]+',
                f'strength: {new_strength:.2f}',
                content
            )
            memory_file.write_text(new_content)
            print(f"Updated {memory_file.name}: {current_strength:.2f} -> {new_strength:.2f}")
```

### 4. Relationship Integrity

Verify all memory links are valid:

```bash
# Find all memory references
for f in ${MNEMONIC_ROOT}/**/*.memory.md; do
    # Extract [[id]] references
    refs=$(grep -oE '\[\[[a-f0-9-]+\]\]' "$f" | tr -d '[]')

    for ref in $refs; do
        # Check if referenced memory exists
        if ! ls ${MNEMONIC_ROOT}/**/${ref}*.memory.md 2>/dev/null | head -1; then
            echo "Broken link in $f: [[${ref}]]"
        fi
    done
done
```

**Fix options:**
- Remove broken links
- Mark as "archived" reference
- Attempt to find renamed memory

### 5. Cleanup Operations

Archive or remove expired content:

```bash
# Find memories past TTL
NOW=$(date +%s)

for f in ${MNEMONIC_ROOT}/**/*.memory.md; do
    TTL=$(grep "ttl:" "$f" | sed 's/.*ttl: P\([0-9]*\)D/\1/')
    CREATED=$(grep "created:" "$f" | sed 's/created: //')

    if [ -n "$TTL" ] && [ -n "$CREATED" ]; then
        # Calculate age
        CREATED_TS=$(date -d "$CREATED" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$CREATED" +%s 2>/dev/null)
        AGE_DAYS=$(( (NOW - CREATED_TS) / 86400 ))

        if [ "$AGE_DAYS" -gt "$TTL" ]; then
            echo "Expired: $f (age: ${AGE_DAYS}d, ttl: ${TTL}d)"
        fi
    fi
done
```

## Workflow

### Agent Registration

On startup, register presence in blackboard:

```bash
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BB_DIR="$HOME/.claude/mnemonic/.blackboard"
mkdir -p "$BB_DIR"

cat >> "${BB_DIR}/session-notes.md" << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Agent:** memory-curator
**Status:** active
**Capabilities:** [conflict-detection, deduplication, decay-management, relationship-integrity, cleanup]

## Agent Registration

Memory curator agent started for scheduled maintenance.

---
EOF
```

### Scheduled Maintenance

```
0. Register agent in blackboard (see above)

1. Run conflict detection
   - Report potential conflicts
   - Suggest resolutions

2. Run deduplication check
   - Identify duplicates
   - Merge or archive

3. Update decay scores
   - Recalculate strength values
   - Flag low-relevance memories

4. Verify relationships
   - Check all links
   - Report broken references

5. Cleanup expired
   - Archive past-TTL memories
   - Remove orphaned files

6. Commit changes
   - Stage all modifications
   - Create maintenance commit

7. Report summary
   - Conflicts found/resolved
   - Duplicates merged
   - Memories archived
   - Relationships fixed

8. Update agent status to idle
```

### Agent Completion

On completion, update status in blackboard:

```bash
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat >> "${BB_DIR}/session-notes.md" << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Agent:** memory-curator
**Status:** idle

## Maintenance Complete

### Summary
- Conflicts detected: $CONFLICTS_DETECTED
- Conflicts resolved: $CONFLICTS_RESOLVED
- Duplicates merged: $DUPLICATES_MERGED
- Decay updates: $DECAY_UPDATES
- Memories archived: $MEMORIES_ARCHIVED

---
EOF
```

### Interactive Conflict Resolution

When conflicts are detected:

```markdown
## Conflict Detected

**Memory A:** Use PostgreSQL for storage
- Created: 2026-01-15
- Confidence: 0.95

**Memory B:** Use SQLite for storage
- Created: 2026-01-20
- Confidence: 0.90

### Options
1. Keep A (mark B as superseded)
2. Keep B (mark A as superseded)
3. Merge into new memory
4. Keep both (different contexts)
5. Skip (decide later)
```

## Output Format

```json
{
  "maintenance_run": "2026-01-23T10:00:00Z",
  "summary": {
    "memories_scanned": 150,
    "conflicts_detected": 3,
    "conflicts_resolved": 2,
    "duplicates_merged": 1,
    "decay_updates": 45,
    "broken_links_fixed": 2,
    "memories_archived": 5
  },
  "actions_taken": [
    {"action": "merge", "memories": ["abc123", "def456"], "result": "ghi789"},
    {"action": "archive", "memory": "old123", "reason": "TTL expired"},
    {"action": "update_decay", "memory": "xyz789", "old": 0.85, "new": 0.72}
  ],
  "pending_conflicts": [
    {"memories": ["mem1", "mem2"], "reason": "Contradictory decisions"}
  ]
}
```

## Best Practices

1. **Non-destructive**: Archive rather than delete
2. **Audit trail**: Log all changes made
3. **User confirmation**: Require approval for merges
4. **Incremental**: Process in batches to avoid long runs
5. **Reversible**: Keep backups before major operations
