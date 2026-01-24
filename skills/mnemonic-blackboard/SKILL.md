---
name: mnemonic-blackboard
description: Cross-session memory coordination and shared context via blackboard
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Mnemonic Blackboard Skill

Cross-session memory coordination and shared context.

## Trigger Phrases

- "blackboard"
- "shared memory"
- "cross-session"
- "coordination"
- "session handoff"
- "shared context"

## Overview

The blackboard is a shared coordination space for cross-session communication. Unlike structured memories, blackboard entries are append-only logs organized by topic, enabling sessions to share context, hand off work, and coordinate activities.

---

## Blackboard Concept

### Purpose

- **Cross-session coordination**: Share state between separate Claude sessions
- **Work handoff**: Leave notes for future sessions
- **Shared context**: Accumulate background information over time
- **Task tracking**: Log active work items across sessions

### Key Differences from Memories

| Aspect | Memories | Blackboard |
|--------|----------|------------|
| Structure | Full MIF frontmatter | Simple timestamped entries |
| Mutability | Updateable | Append-only |
| Organization | By namespace/type | By topic |
| Persistence | Long-term | Session-relevant |
| Search | Full-text + frontmatter | grep by topic/session |

---

## Directory Structure

### Locations

```
~/.claude/mnemonic/.blackboard/     # Global (cross-project)
./.claude/mnemonic/.blackboard/     # Project-specific
```

### Topic Files

```
.blackboard/
├── active-tasks.md        # Current work items
├── pending-decisions.md   # Decisions awaiting input
├── shared-context.md      # Background for all sessions
├── session-notes.md       # Handoff notes
├── blockers.md            # Known impediments
└── {custom-topic}.md      # Any topic you define
```

---

## Session Identification

### Get Session ID

```bash
# Use Claude's session ID if available
SESSION_ID="${CLAUDE_SESSION_ID:-}"

# Fallback: generate unique ID
if [ -z "$SESSION_ID" ]; then
    SESSION_ID="$(date +%s)-$$"
fi

echo "Session: $SESSION_ID"
```

### Session Metadata

```bash
# Capture session context
SESSION_START=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SESSION_USER=$(whoami)
SESSION_HOST=$(hostname -s)
SESSION_PWD=$(pwd)
```

---

## Write to Blackboard

### Basic Entry

```bash
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TOPIC="active-tasks"

cat >> ~/.claude/mnemonic/.blackboard/${TOPIC}.md << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP

Your content here...

EOF
```

### Structured Entry Template

```markdown
---
**Session:** {session_id}
**Time:** {timestamp}
**Status:** active | completed | blocked | handed-off

## Summary
Brief description of what this entry is about.

## Details
- Point 1
- Point 2

## Next Steps
- [ ] Action item 1
- [ ] Action item 2

---
```

### Write Functions

```bash
# Function to write to blackboard
bb_write() {
    local topic="$1"
    local content="$2"
    local bb_dir="${3:-$HOME/.claude/mnemonic/.blackboard}"

    mkdir -p "$bb_dir"

    local session_id="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat >> "${bb_dir}/${topic}.md" << EOF

---
**Session:** $session_id
**Time:** $timestamp

$content

EOF
}

# Usage
bb_write "active-tasks" "Started working on authentication module"
bb_write "shared-context" "Project uses JWT with RS256 signing"
```

---

## Read from Blackboard

### Read Entire Topic

```bash
# Full topic file
cat ~/.claude/mnemonic/.blackboard/active-tasks.md

# Project blackboard
cat ./.claude/mnemonic/.blackboard/shared-context.md
```

### Read Recent Entries

```bash
# Last 50 lines (most recent entries)
tail -50 ~/.claude/mnemonic/.blackboard/active-tasks.md

# Last 3 entries (entries separated by ---)
tac ~/.claude/mnemonic/.blackboard/active-tasks.md | \
    awk '/^---$/{count++} count<3' | tac
```

### Read Specific Session

```bash
SESSION_ID="1706012345-12345"

# Find entries from specific session
grep -A20 "Session: $SESSION_ID" ~/.claude/mnemonic/.blackboard/active-tasks.md
```

### Read Today's Entries

```bash
TODAY=$(date +%Y-%m-%d)

# Entries from today
grep -A20 "Time: ${TODAY}T" ~/.claude/mnemonic/.blackboard/active-tasks.md
```

### Search Across Topics

```bash
# Search all blackboard files
rg "pattern" ~/.claude/mnemonic/.blackboard/

# List topics mentioning something
rg -l "authentication" ~/.claude/mnemonic/.blackboard/
```

---

## Topic Conventions

### Standard Topics

| Topic | Purpose | Typical Content |
|-------|---------|-----------------|
| `active-tasks.md` | Current work items | Task descriptions, status |
| `pending-decisions.md` | Decisions needing input | Options, trade-offs |
| `shared-context.md` | Background for sessions | Setup, environment, config |
| `session-notes.md` | Handoff between sessions | Progress, blockers |
| `blockers.md` | Known impediments | Issues, dependencies |
| `debug-log.md` | Investigation notes | Steps tried, findings |
| `todo.md` | Quick task list | Checkbox items |

### Custom Topics

Create any topic file you need:

```bash
# Create new topic
touch ~/.claude/mnemonic/.blackboard/api-integration.md

# Write first entry
bb_write "api-integration" "Started integrating with Stripe API"
```

---

## Coordination Patterns

### Session Handoff

When ending a session, leave notes for the next:

```bash
bb_write "session-notes" "$(cat << 'EOF'
## Handoff Notes

### What I Did
- Implemented user authentication
- Added JWT token generation
- Created login endpoint

### What's Left
- [ ] Add token refresh endpoint
- [ ] Implement logout
- [ ] Add rate limiting

### Important Context
- Using RS256 for signing (see decisions/jwt-signing.memory.md)
- Token expiry is 15 minutes
- Refresh tokens stored in httpOnly cookies

### Watch Out For
- The auth middleware expects Bearer token format
- Tests require TEST_JWT_SECRET env var
EOF
)"
```

### Work Tracking

Track active work across sessions:

```bash
# Starting work
bb_write "active-tasks" "$(cat << 'EOF'
## Starting: Payment Integration

**Priority:** High
**Estimate:** Large

### Goals
- Integrate Stripe checkout
- Handle webhooks
- Update order status

### Files to modify
- src/payments/stripe.ts
- src/api/webhooks.ts
- src/models/order.ts
EOF
)"

# Completing work
bb_write "active-tasks" "$(cat << 'EOF'
## Completed: Payment Integration

**Status:** Done

### Summary
Stripe integration complete. All tests passing.

### Changes
- Added Stripe SDK and config
- Implemented checkout flow
- Webhook handlers for payment events
EOF
)"
```

### Decision Tracking

Track pending decisions:

```bash
bb_write "pending-decisions" "$(cat << 'EOF'
## Decision Needed: Caching Strategy

### Context
API response times are slow for product listings.

### Options
1. **Redis** - Fast, but adds infrastructure
2. **In-memory** - Simple, but not shared across instances
3. **CDN** - Good for static, limited for dynamic

### Recommendation
Option 1 (Redis) - already using Redis for sessions

### Awaiting
Confirmation from team on infrastructure budget
EOF
)"
```

---

## Locking (Optional)

For concurrent access safety:

### Simple Lock

```bash
LOCK_FILE="$HOME/.claude/mnemonic/.blackboard/.lock"

# Acquire lock
acquire_lock() {
    local max_wait=10
    local waited=0

    while [ -f "$LOCK_FILE" ]; do
        sleep 1
        waited=$((waited + 1))
        if [ $waited -ge $max_wait ]; then
            echo "Lock timeout" >&2
            return 1
        fi
    done

    echo $$ > "$LOCK_FILE"
    return 0
}

# Release lock
release_lock() {
    rm -f "$LOCK_FILE"
}

# Usage
if acquire_lock; then
    bb_write "active-tasks" "My entry"
    release_lock
fi
```

### Lock with Expiry

```bash
LOCK_FILE="$HOME/.claude/mnemonic/.blackboard/.lock"
LOCK_TIMEOUT=60  # seconds

check_stale_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local lock_age=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || echo 0) ))
        if [ $lock_age -gt $LOCK_TIMEOUT ]; then
            rm -f "$LOCK_FILE"
            echo "Removed stale lock"
        fi
    fi
}
```

---

## Cleanup

### Archive Old Entries

```bash
# Archive entries older than 30 days
ARCHIVE_DIR="$HOME/.claude/mnemonic/.blackboard/.archive"
mkdir -p "$ARCHIVE_DIR"

for topic in ~/.claude/mnemonic/.blackboard/*.md; do
    topic_name=$(basename "$topic" .md)

    # Extract entries older than 30 days
    # (This is a simplified approach - real implementation needs date parsing)
    cp "$topic" "$ARCHIVE_DIR/${topic_name}-$(date +%Y%m%d).md"
done
```

### Clear Completed Tasks

```bash
# Remove completed entries from active-tasks
# Keep only entries without "Status: Done"
grep -v -A10 "Status: Done" ~/.claude/mnemonic/.blackboard/active-tasks.md > \
    ~/.claude/mnemonic/.blackboard/active-tasks.md.tmp
mv ~/.claude/mnemonic/.blackboard/active-tasks.md.tmp \
   ~/.claude/mnemonic/.blackboard/active-tasks.md
```

### Reset Topic

```bash
# Clear a topic (keep file, remove content)
echo "# $(basename $TOPIC .md)" > ~/.claude/mnemonic/.blackboard/$TOPIC.md
```

---

## Examples

### Example: Start of Session

```bash
#!/bin/bash
# session_start.sh - Initialize blackboard for new session

SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
PROJECT=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || basename "$PWD")

# Read recent context
echo "=== Recent Activity ==="
tail -30 ~/.claude/mnemonic/.blackboard/session-notes.md 2>/dev/null

echo ""
echo "=== Active Tasks ==="
tail -20 ~/.claude/mnemonic/.blackboard/active-tasks.md 2>/dev/null

echo ""
echo "=== Pending Decisions ==="
tail -20 ~/.claude/mnemonic/.blackboard/pending-decisions.md 2>/dev/null

# Log session start
cat >> ~/.claude/mnemonic/.blackboard/session-notes.md << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Project:** $PROJECT
**Status:** started

Session initialized.

EOF
```

### Example: End of Session

```bash
#!/bin/bash
# session_end.sh - Capture session summary

SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

read -r -d '' SUMMARY << 'EOF'
## Session Summary

### Completed
- Item 1
- Item 2

### In Progress
- Item 3

### Blocked
- None

### Notes for Next Session
- Continue with Item 3
EOF

cat >> ~/.claude/mnemonic/.blackboard/session-notes.md << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Status:** ended

$SUMMARY

EOF

# Commit changes
cd ~/.claude/mnemonic && git add -A && git commit -m "Session $SESSION_ID ended"
```

### Example: Quick Task Add

```bash
# Add task to todo
echo "- [ ] $(date +%H:%M) - $*" >> ~/.claude/mnemonic/.blackboard/todo.md
```

---

## Best Practices

1. **Keep entries concise** - Blackboard is for coordination, not documentation
2. **Use consistent formatting** - Makes parsing and searching easier
3. **Include session ID** - Enables tracking and handoff
4. **Clean up regularly** - Archive old entries, remove completed tasks
5. **Use topics wisely** - Don't create too many; consolidate when possible
6. **Project vs Global** - Use project blackboard for project-specific coordination
