---
applyTo: "**/*.memory.md"
---

# Memory File Guidelines (MIF Level 3)

## Required Frontmatter Fields

```yaml
---
id: <uuid>                    # Unique identifier (uuidgen format)
type: semantic|episodic|procedural
namespace: {category}/user    # e.g., decisions/user, learnings/user
created: <ISO8601>            # Creation timestamp
modified: <ISO8601>           # Last modification timestamp
title: "Title"                # Human-readable title
tags: [tag1, tag2]            # Categorization tags
---
```

## Optional Temporal Fields

```yaml
temporal:
  valid_from: <ISO8601>       # When content became valid
  valid_until: <ISO8601>      # When content expires (optional)
  recorded_at: <ISO8601>      # When it was recorded
  decay:
    model: exponential        # Decay model type
    half_life: P7D            # ISO 8601 duration
    strength: 0.85            # Current strength 0.0-1.0
```

## Optional Provenance Fields

```yaml
provenance:
  source_type: user_explicit|inferred|conversation
  agent: model-identifier     # e.g., claude-opus-4
  confidence: 0.9             # Confidence score 0.0-1.0
```

## Memory Types

- **semantic**: Facts, decisions, specifications - things that ARE true
- **episodic**: Events, debug sessions, incidents - things that HAPPENED
- **procedural**: Workflows, patterns, how-tos - things you DO

## Content Structure

After frontmatter, use standard Markdown:
- H1 heading matching the title
- Clear sections for context, details, implications
- Code blocks with language specification
- Links to related memories or external resources
