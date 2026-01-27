---
name: mnemonic-core
description: >
  Capture decisions, learnings, patterns, and blockers to persistent memory.
  Use AUTOMATICALLY when user says: "I've decided", "let's use", "we're going with",
  "I learned", "turns out", "TIL", "discovered", "I'm stuck", "blocked by",
  "always use", "never do", "convention is".
  Also use for recall when user asks: "what did we decide", "how do we handle",
  "remind me", "what patterns", "search memories".
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Mnemonic Core

Memory system operations. See `references/` for full documentation.

## Trigger Phrases

### Capture Triggers (silently capture when user says):

**Decisions** (namespace: _semantic/decisions):
- "I've decided", "let's use", "we're going with"
- "we'll use", "I'm choosing", "going forward with"
- "the decision is", "we chose", "decided on"

**Learnings** (namespace: _semantic/knowledge):
- "I learned", "turns out", "discovered that"
- "TIL", "gotcha", "found out", "realized"
- "the root cause was", "it was because"

**Patterns** (namespace: _procedural/patterns):
- "always use", "never do", "when X do Y"
- "the pattern is", "we should always", "convention is"
- "standard approach", "best practice here"

**Blockers** (namespace: _episodic/sessions/blockers):
- "I'm stuck on", "blocked by", "can't figure out"
- "hitting a wall", "the problem is", "struggling with"

**Context** (namespace: _semantic/knowledge):
- "important to know", "keep in mind", "context is"
- "background", "constraint", "requirement"

### Recall Triggers (search memories when user asks):

- "what did we decide about", "how do we handle"
- "what's our approach to", "check for decisions"
- "any learnings about", "patterns for"
- "remind me", "what do we know about"
- "search memories", "recall", "find memories"

### Silent Capture Protocol

When trigger phrases are detected:
1. Capture to appropriate namespace WITHOUT announcing
2. Do NOT say "I'm capturing this" or similar
3. Continue natural conversation flow
4. Memory creation is invisible to user

## Capture

```bash
/mnemonic:capture {namespace} "{title}"
```

Namespaces: `_semantic/decisions` | `_semantic/knowledge` | `_procedural/patterns` | `_episodic/blockers` | `_semantic/knowledge` | `_semantic/knowledge` | `_semantic/knowledge` | `_procedural/patterns` | `episodic`

## Recall

```bash
rg -i "{keywords}" ~/.claude/mnemonic/ --glob "*.memory.md" -l
```

## Minimal Memory Format

```yaml
---
id: {uuid}
title: "Title"
type: semantic|episodic|procedural
created: {iso-date}
---

# Title

Content here.
```

## References

- `references/capture.md` - Full capture workflow
- `references/recall.md` - Search and retrieval patterns
- `references/schema.md` - Complete MIF Level 3 schema
- `references/examples.md` - Working examples
