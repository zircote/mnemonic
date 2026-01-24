---
title: "Validation Results as Episodic Memories"
description: "Optionally capture validation runs as MIF-compliant episodic memories"
type: adr
category: architecture
tags:
  - validation
  - episodic
  - memory
  - maintenance
status: accepted
created: 2026-01-24
updated: 2026-01-24
author: zircote
project: mnemonic
technologies:
  - python
  - yaml
  - markdown
audience:
  - developers
  - architects
related:
  - adr-002-mif-level-3-format.md
  - adr-004-mif-schema-validation.md
---

# ADR-006: Validation Results as Episodic Memories

## Status

Accepted

## Context

### Background and Problem Statement

The mnemonic validation tool produces reports about memory file compliance. These reports are valuable for tracking maintenance history and identifying recurring issues over time. Without capturing them, validation history is lost.

### Current State

No validation tool exists yet. When implemented (per ADR-004), it will output reports but not store them.

## Decision Drivers

### Primary Decision Drivers

1. **History Tracking**: Record validation runs over time
2. **Searchability**: Find past validation issues via mnemonic search
3. **Consistency**: Use same storage as other memories
4. **Optionality**: Not all runs need capture

### Secondary Decision Drivers

1. **MIF Compliance**: Captured validations should follow MIF format
2. **Appropriate Type**: Validation runs are events (episodic)
3. **Minimal Overhead**: Capture should be quick

## Considered Options

### Option 1: Standalone Report Files

**Description**: Write validation reports to a reports/ directory as markdown files.

**Technical Characteristics**:
- `reports/validation/YYYY-MM-DD.md`
- Standard markdown, no frontmatter
- Separate from mnemonic system

**Advantages**:
- Simple file output
- Easy to read directly
- No MIF overhead

**Disadvantages**:
- Not searchable via mnemonic
- No metadata
- Separate from memory ecosystem

**Risk Assessment**:
- **Discovery Risk**: High. Reports may be forgotten.
- **Search Risk**: High. Not integrated with search.

### Option 2: Capture as Episodic Memories (Selected)

**Description**: Optionally capture validation runs as MIF-compliant episodic memories.

**Technical Characteristics**:
- `--capture` flag on validation tool
- Creates memory in `blockers/project` (if errors) or `episodic/project`
- Full MIF frontmatter
- Searchable via mnemonic

**Advantages**:
- Searchable via mnemonic search
- Full metadata (temporal, provenance)
- Integrated with memory ecosystem
- Optional via flag

**Disadvantages**:
- More complex than simple file
- Requires MIF formatting

**Risk Assessment**:
- **Complexity Risk**: Low. Standard memory creation.
- **Integration Risk**: Low. Uses existing patterns.

### Option 3: Always Capture

**Description**: Automatically capture every validation run.

**Technical Characteristics**:
- No flag needed
- Every run creates memory
- May create many memories

**Advantages**:
- Complete history
- No user action needed

**Disadvantages**:
- May create excessive memories
- No control over capture

**Risk Assessment**:
- **Volume Risk**: High. Many memories over time.
- **Relevance Risk**: Medium. Not all runs valuable.

## Decision

We will optionally capture validation runs as MIF-compliant episodic memories using the `--capture` flag.

### Memory Format

```yaml
---
id: {uuid}
type: episodic
namespace: blockers/project  # or episodic/project if no errors
created: {timestamp}
title: "Validation Run: {date}"
tags:
  - validation
  - maintenance
temporal:
  valid_from: {timestamp}
  recorded_at: {timestamp}
provenance:
  source_type: inferred
  agent: mnemonic-validate
  confidence: 1.0
---

# Validation Run: {date}

## Summary

- **Memories validated:** 145
- **Errors:** 3
- **Warnings:** 5

## Issues Found

### Errors

1. **Missing required field** in `abc123-example.memory.md`
   - Field: `type`
   - Line: 3

### Warnings

1. **Invalid tag format** in `def456-other.memory.md`
   - Tag: `CamelCase` should be `camel-case`

## Passed Checks

- Schema validation: 142/145
- Code refs validation: 100%
- Citations validation: 100%
```

### Namespace Selection

- **Errors found**: `blockers/project` - Captures as blocker for action
- **No errors**: `episodic/project` - Captures as routine maintenance event

### CLI Usage

```bash
# Validate and capture results
mnemonic-validate --capture

# Validate without capture
mnemonic-validate

# Capture with specific format
mnemonic-validate --capture --format markdown
```

## Consequences

### Positive

1. **Searchable History**: Find past issues via mnemonic search
2. **Trend Analysis**: Track validation quality over time
3. **Actionable Blockers**: Errors captured in blockers namespace
4. **Optional**: Only capture when desired

### Negative

1. **Memory Volume**: May accumulate validation memories
2. **GC Consideration**: Should have TTL for cleanup

### Neutral

1. **MIF Compliance**: Follows standard format

## Decision Outcome

Optional episodic capture achieves:
- Searchable validation history
- Integration with mnemonic ecosystem
- User control via flag
- Appropriate namespace based on results

## Related Decisions

- [ADR-002: MIF Level 3 Format](adr-002-mif-level-3-format.md) - Format for captured memories
- [ADR-004: MIF Schema Validation](adr-004-mif-schema-validation.md) - Validation tool design

## Links

- [Episodic Memory](https://en.wikipedia.org/wiki/Episodic_memory) - Memory of events

## More Information

- **Date:** 2026-01-24
- **Source:** Validation tool design

## Audit

### 2026-01-24

**Status:** Pending implementation

**Findings:** N/A - New ADR

**Action Required:** Implement --capture flag in validation tool
