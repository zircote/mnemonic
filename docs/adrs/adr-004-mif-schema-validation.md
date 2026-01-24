---
title: "MIF Schema as Single Source of Truth for Validation"
description: "Validation tool parses MIF schema from mnemonic-format SKILL.md directly"
type: adr
category: architecture
tags:
  - validation
  - mif
  - schema
  - single-source-of-truth
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
---

# ADR-004: MIF Schema as Single Source of Truth for Validation

## Status

Accepted

## Context

### Background and Problem Statement

The mnemonic system needs a validation tool to ensure memory files conform to the MIF Level 3 specification. The validation rules must be maintained somewhere, and there are multiple approaches to defining and storing these rules.

### Current State

The MIF Level 3 specification is documented in `skills/mnemonic-format/SKILL.md`, which includes:
- Required fields and their types
- Valid enum values for type, source_type, etc.
- Validation rules section with specific checks
- Field reference tables

## Decision Drivers

### Primary Decision Drivers

1. **Single Source of Truth**: One authoritative location for schema rules
2. **Automatic Updates**: Validation should reflect schema changes automatically
3. **Maintainability**: Avoid duplicating schema in multiple places
4. **Discoverability**: Developers should easily find the rules

### Secondary Decision Drivers

1. **Parsability**: Rules must be extractable by validation tool
2. **Documentation**: Schema should be human-readable
3. **Flexibility**: Support adding new validation rules

## Considered Options

### Option 1: Hardcoded Validation Rules

**Description**: Embed validation rules directly in Python validation script.

**Technical Characteristics**:
- Rules defined as Python constants/functions
- No external dependencies
- Manual sync with documentation

**Advantages**:
- Fast validation (no parsing)
- Full flexibility in rule implementation
- Easy to test

**Disadvantages**:
- Rules duplicated from documentation
- Must manually sync when schema changes
- Documentation may drift from implementation

**Risk Assessment**:
- **Drift Risk**: High. Documentation and code may diverge.
- **Maintenance Risk**: High. Two places to update.

### Option 2: Separate Schema File

**Description**: Create a dedicated schema file (JSON Schema, YAML schema).

**Technical Characteristics**:
- `schema/mif-level-3.json` or similar
- Standard schema format
- Documentation generated from schema

**Advantages**:
- Standard format (JSON Schema)
- Tooling support for validation
- Clear separation of schema from docs

**Disadvantages**:
- Another file to maintain
- Documentation still separate
- May not capture all validation logic

**Risk Assessment**:
- **Complexity Risk**: Medium. New file format to maintain.
- **Sync Risk**: Medium. Docs may not match schema.

### Option 3: Parse Schema from SKILL.md (Selected)

**Description**: Validation tool parses rules directly from `mnemonic-format/SKILL.md`.

**Technical Characteristics**:
- SKILL.md is authoritative source
- Validation tool extracts rules from markdown
- Single document for humans and machines

**Advantages**:
- True single source of truth
- Changes automatically reflected in validation
- Documentation is the implementation
- No sync issues

**Disadvantages**:
- Requires parsing markdown
- Schema format constrained by markdown structure
- More complex tool implementation

**Risk Assessment**:
- **Implementation Risk**: Medium. Parsing logic needed.
- **Sync Risk**: None. Same file for docs and validation.

## Decision

We will parse validation rules directly from `skills/mnemonic-format/SKILL.md`.

### Parsing Strategy

The validation tool will extract:

1. **Required Fields**: From "Required Fields" table
2. **Field Types**: From field reference tables
3. **Enum Values**: From type definitions (semantic|episodic|procedural)
4. **Validation Rules**: From "Validation Rules" section
5. **Citation Types**: From Citation Fields table

### Implementation

```python
def parse_mif_schema(skill_path: Path) -> MIFSchema:
    """Parse MIF schema from mnemonic-format SKILL.md."""
    content = skill_path.read_text()

    schema = MIFSchema()

    # Extract required fields from table
    schema.required_fields = extract_required_fields(content)

    # Extract enum values from type definitions
    schema.type_values = extract_enum_values(content, "type")
    schema.source_types = extract_enum_values(content, "source_type")

    # Extract validation rules
    schema.validation_rules = extract_validation_rules(content)

    return schema
```

### SKILL.md Requirements

The SKILL.md must maintain parseable sections:
- Field Reference tables with markdown table format
- Validation Rules section with numbered checks
- Enum values clearly specified

## Consequences

### Positive

1. **Single Source**: One authoritative schema location
2. **Auto-Sync**: Validation always matches documentation
3. **No Drift**: Impossible for docs and validation to diverge
4. **Maintainable**: Update one file for both docs and validation

### Negative

1. **Parsing Complexity**: Tool must parse markdown
2. **Format Constraints**: SKILL.md format somewhat constrained
3. **Implicit Contract**: SKILL.md format becomes a contract

### Neutral

1. **Documentation Quality**: Must maintain parseable format

## Decision Outcome

Using SKILL.md as single source achieves:
- Zero drift between documentation and validation
- Automatic updates when schema changes
- Single maintenance point

Mitigations:
- Clear comments in SKILL.md about parseable sections
- Tests that validate parsing works
- Error messages if parsing fails

## Related Decisions

- [ADR-002: MIF Level 3 Format](adr-002-mif-level-3-format.md) - The format being validated

## Links

- [Single Source of Truth Principle](https://en.wikipedia.org/wiki/Single_source_of_truth)
- [Documentation-Driven Development](https://gist.github.com/zsup/9434452)

## More Information

- **Date:** 2026-01-24
- **Source:** Validation tool design

## Audit

### 2026-01-24

**Status:** Pending implementation

**Findings:** N/A - New ADR

**Action Required:** Implement validation tool with schema parsing
