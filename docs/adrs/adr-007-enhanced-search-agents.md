---
title: "Enhanced Search with Agent-Driven Iteration"
description: "Use subcall agents (haiku) for iterative query refinement with synthesis"
type: adr
category: architecture
tags:
  - search
  - agents
  - haiku
  - synthesis
status: accepted
created: 2026-01-24
updated: 2026-01-24
author: zircote
project: mnemonic
technologies:
  - task-tool
  - haiku
  - json
audience:
  - developers
  - architects
related:
  - adr-003-agent-coordination-blackboard.md
---

# ADR-007: Enhanced Search with Agent-Driven Iteration

## Status

Accepted (Implemented)

## Context

### Background and Problem Statement

The basic `/mnemonic:search` command performs single-shot pattern matching. For complex queries spanning multiple topics or namespaces, this approach may miss relevant memories. Users need comprehensive search with synthesis.

### Current State

Basic search implemented:
- Ripgrep-based pattern matching
- Single namespace or all namespaces
- Returns file list with snippets

Missing:
- Query refinement based on initial results
- Cross-namespace synthesis
- Comprehensive answer generation

## Decision Drivers

### Primary Decision Drivers

1. **Context Conservation**: Search must not exhaust main context window
2. **Comprehensive Results**: Find relevant memories across namespaces
3. **Synthesized Output**: Produce coherent answer, not just file list
4. **Cost Efficiency**: Use cheap model for repetitive search work

### Secondary Decision Drivers

1. **Iterative Refinement**: Learn from initial results
2. **Convergence**: Stop when diminishing returns
3. **Traceability**: Track which memories contributed

## Considered Options

### Option 1: Single-Pass Deep Search

**Description**: Expand basic search to search all namespaces and read all matches.

**Technical Characteristics**:
- Single command execution
- Read all matching files
- Synthesize in main context

**Advantages**:
- Simple implementation
- Single pass

**Disadvantages**:
- May exhaust context with many matches
- No refinement based on results
- Fixed search patterns

**Risk Assessment**:
- **Context Risk**: High. Large result sets exhaust context.
- **Quality Risk**: Medium. No refinement.

### Option 2: Agent-Driven Iteration (Selected)

**Description**: Use subcall agents running on haiku for iterative search with synthesis.

**Technical Characteristics**:
- Orchestrating skill in main context
- Haiku subcall agents for search iterations
- JSON findings returned for aggregation
- Final synthesis in main context

**Advantages**:
- Context isolated in subcalls
- Iterative refinement
- Cost-effective (haiku)
- Comprehensive coverage

**Disadvantages**:
- More complex architecture
- Multiple agent invocations

**Risk Assessment**:
- **Complexity Risk**: Medium. Multi-agent coordination.
- **Context Risk**: Low. Isolated subcalls.

### Option 3: External Search Service

**Description**: Implement search as external service with API.

**Technical Characteristics**:
- Separate search process
- API-based queries
- Results returned to Claude

**Advantages**:
- Scalable search
- Persistent index

**Disadvantages**:
- External dependency (violates ADR-001)
- Complex setup

**Risk Assessment**:
- **Dependency Risk**: High. External service needed.

## Decision

We will use agent-driven iteration with haiku subcall agents for enhanced search.

### Architecture

```
Main Context (orchestrator)
    │
    ├── Iteration 1: Task(mnemonic-search-subcall, haiku)
    │       └── Returns JSON findings
    │
    ├── Iteration 2: Task(mnemonic-search-subcall, haiku)
    │       └── Returns JSON findings (refined)
    │
    ├── Iteration 3: Task(mnemonic-search-subcall, haiku)
    │       └── Returns JSON findings (final)
    │
    └── Synthesis: Read top memories, produce answer
```

### Subcall Agent

`mnemonic-search-subcall`:
- Model: haiku (cheap, fast)
- Tools: Grep, Read, Bash
- Input: query, iteration, pattern, namespace filter
- Output: JSON with findings and refinement suggestions

### Convergence

Stop iterating when:
- New iteration finds < 2 new memories
- > 90% overlap with previous
- All suggested namespaces searched
- MAX_ITERATIONS (3) reached

### Output Format

Synthesized markdown with:
- Summary answering query
- Key findings by category
- Analysis connecting findings
- Coverage metrics
- Source memory references

## Consequences

### Positive

1. **Context Safe**: Subcalls run in isolated context
2. **Comprehensive**: Multiple refinement rounds
3. **Cost Effective**: Haiku for search, opus for synthesis
4. **Traceable**: JSON findings track sources

### Negative

1. **Latency**: Multiple agent invocations
2. **Complexity**: Multi-agent coordination

### Neutral

1. **API Calls**: More calls but cheaper model

## Decision Outcome

Agent-driven iteration achieves:
- Context conservation via isolated subcalls
- Comprehensive coverage via iteration
- Cost efficiency via haiku
- Quality synthesis via aggregation

## Implementation Status

**Already Implemented:**
- `skills/mnemonic-search-enhanced/SKILL.md`
- `agents/mnemonic-search-subcall.md`
- `/mnemonic:search-enhanced` command

## Related Decisions

- [ADR-003: Agent Coordination](adr-003-agent-coordination-blackboard.md) - Agent patterns

## Links

- [Iterative Refinement](https://en.wikipedia.org/wiki/Iterative_refinement)

## More Information

- **Date:** 2026-01-24
- **Source:** Enhanced search implementation

## Audit

### 2026-01-24

**Status:** Compliant

**Findings:**

| Finding | Files | Assessment |
|---------|-------|------------|
| Haiku subcall pattern | `agents/mnemonic-search-subcall.md:4` | compliant |
| JSON output format | `agents/mnemonic-search-subcall.md:130-162` | compliant |
| Convergence detection | `skills/mnemonic-search-enhanced/SKILL.md:123-137` | compliant |
| Synthesis output | `skills/mnemonic-search-enhanced/SKILL.md:165-204` | compliant |

**Summary:** Enhanced search implementation follows agent-driven iteration pattern.

**Action Required:** None - already implemented
