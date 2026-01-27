# Memory Examples

Complete examples of memory capture and recall.

## Example: Capture a Decision

```bash
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "~/.claude/mnemonic/semantic/decisions/${UUID}-use-jwt-auth.memory.md" << EOF
---
id: ${UUID}
title: "Use JWT for API authentication"
type: semantic
created: ${DATE}
tags:
  - authentication
  - security
  - api
---

# Use JWT for API Authentication

We decided to use JSON Web Tokens (JWT) for API authentication.

## Rationale

- Stateless authentication reduces server load
- Standard format with wide library support
- Can include claims for authorization
- Works well with microservices architecture

## Implementation Notes

- Use RS256 algorithm for token signing
- Token expiry: 15 minutes for access, 7 days for refresh
- Store refresh tokens in httpOnly cookies
EOF
```

## Example: Capture a Learning

```bash
UUID=$(uuidgen | tr '[:upper:]' '[:lower:]')
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$HOME/.claude/mnemonic/default/learnings/user/${UUID}-async-wiring-fix.memory.md" << EOF
---
id: ${UUID}
title: "Async actor wiring must happen after config load"
type: semantic
created: ${DATE}
tags:
  - async
  - actors
  - initialization
---

# Async Actor Wiring Fix

## The Problem

Optional async actors weren't receiving messages because they were wired before the configuration was loaded.

## The Solution

Always wire optional actors AFTER the config load phase completes. The initialization order is:
1. Load config
2. Start core actors
3. Wire optional actors

## Code Reference

See \`src/actors/watcher.rs:142\` for the correct pattern.
EOF
```

## Example: Recall Decisions About Auth

```bash
# Search for auth-related decisions
rg -i "auth"decisions/ --glob "*.memory.md" -l

# Get full content of matching files
for f in $(rg -i "auth"decisions/ --glob "*.memory.md" -l); do
    echo "=== $f ==="
    cat "$f"
    echo ""
done
```

## Example: Update Existing Memory

```bash
# Find memory to update
MEMORY_FILE=$(rg -l "Use JWT for API" --glob "*.memory.md" | head -1)

# Update modified date
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
sed -i '' "s/^modified: .*/modified: ${DATE}/" "$MEMORY_FILE"

# Commit
cd ~/.claude/mnemonic && git add -A && git commit -m "Update: JWT auth decision" && cd -
```

## Example: Status Check

```bash
echo "=== Mnemonic Status ==="

# Count by namespace
for ns in apis blockers context decisions learnings patterns security testing episodic; do
    count=$(find ~/.claude/mnemonic/*/$ns -name "*.memory.md" 2>/dev/null | wc -l)
    echo "$ns: $count memories"
done

# Recent captures
echo ""
echo "=== Recent (last 7 days) ==="
find ~/.claude/mnemonic -name "*.memory.md" -mtime -7 -exec basename {} \; 2>/dev/null | head -10
```
