---
allowed-tools:
- Read
- Glob
- Grep
- Bash
- Write
description: Protocol for recalling memories at appropriate detail levels
name: mnemonic-progressive-disclosure
user-invocable: true
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# Mnemonic Progressive Disclosure Skill

Protocol for recalling memories at the appropriate detail level.

## Trigger Phrases

- "progressive disclosure"
- "disclosure levels"
- "memory recall levels"
- "how to recall"
- "expand memory"
- "more detail"

## Overview

Progressive disclosure enables efficient memory recall by surfacing only the detail level needed. Start with Level 1 (Quick Answer), expand to Level 2 (Context) or Level 3 (Full Detail) only when required.

---

## Disclosure Levels

### Level 1: Quick Answer (Default)

**What to read:** The `## Quick Answer` section only (or `summary` frontmatter field)

**Content:** 1-3 sentences answering the core question

**Sufficient for:**
- "What is X?"
- "Which X do we use?"
- "What did we decide about X?"
- Simple recall questions

**Example response:**
> PostgreSQL was chosen for primary storage due to ACID compliance and native JSON support.

### Level 2: Context (On Request)

**What to read:** `## Quick Answer` + `## Context` sections

**Content:**
- Decision date/timeframe
- Alternatives considered
- Key decision drivers
- Trade-offs made

**Sufficient for:**
- "Why did we choose X?"
- "What alternatives did we consider?"
- "Tell me more about X"
- Understanding rationale

**Triggers:**
- User asks "why?"
- User asks for reasoning/rationale
- User says "tell me more" or "explain"

**Example response:**
> PostgreSQL was chosen for primary storage due to ACID compliance and native JSON support.
>
> **Context:**
> - Decision made: 2026-01-15
> - Alternatives considered: MySQL, MongoDB, SQLite
> - Key drivers: Need for JSON queries, team familiarity, existing infrastructure
> - Trade-off: Accepted more complex hosting for better query capabilities

### Level 3: Comprehensive (Deep Dive)

**What to read:** Full memory content

**Content:**
- Complete alternatives analysis
- Implementation notes
- Related decisions/patterns
- Code references
- Citations

**Sufficient for:**
- Implementation work
- Debugging issues related to decision
- Writing documentation
- Making related decisions
- "Give me all the details"

**Triggers:**
- User is implementing something
- User is debugging
- User asks for "all details" or "full context"
- User needs to make a related decision

**Example response:**
> [Full memory content including alternatives analysis, implementation notes, code refs, etc.]

---

## Recall Protocol

### Step 1: Search for Memories

```bash
# Search by topic
rg -i "{topic}" ~/.claude/mnemonic/ --glob "*.memory.md" -l

# Search in specific namespace
rg -i "{topic}" ~/.claude/mnemonic --path "*/_semantic/decisions/" --glob "*.memory.md" -l
```

### Step 2: Determine Required Level

| User Intent | Start With |
|-------------|------------|
| Quick question | Level 1 |
| Understanding reasoning | Level 2 |
| Implementation work | Level 3 |
| Debugging | Level 3 |
| Related decision-making | Level 2, then 3 |

### Step 3: Read Appropriate Section

```bash
# For Level 1: Read just title and Quick Answer
head -30 {memory_file}  # Usually enough for frontmatter + Quick Answer

# For Level 2: Read through Context section
head -60 {memory_file}

# For Level 3: Read full file
cat {memory_file}
```

### Step 4: Respond and Offer Expansion

After Level 1 or 2 response, offer to expand:
- "Would you like more context on why this was chosen?"
- "I can provide the full implementation details if needed."

---

## Examples

### Example 1: Simple Question

**User:** "What database are we using?"

**Action:** Search, find postgres-decision.memory.md, read Quick Answer

**Response:**
> PostgreSQL for primary storage, chosen for ACID compliance and JSON support.

### Example 2: Reasoning Question

**User:** "Why PostgreSQL instead of MongoDB?"

**Action:** Search, find memory, read through Context section

**Response:**
> We chose PostgreSQL over MongoDB because:
> - Team already familiar with SQL
> - Needed ACID transactions for payments
> - JSON support sufficient for our flexible schema needs
> - MongoDB would require new infrastructure and training

### Example 3: Implementation Work

**User:** "I'm implementing the new caching layer"

**Action:** Search for caching memories, read full content

**Response:**
> [Full memory with implementation notes, configuration details, code references]

---

## Memory Structure Reference

Comprehensive memories should have this structure:

```markdown
# {Title}

## Quick Answer
{1-3 sentences - Level 1 content}

## Context
{Decision factors, alternatives, trade-offs - Level 2 content}

## Full Detail
{Implementation notes, code refs, citations - Level 3 content}
```

Memories with `detail_level: minimal` may only have Quick Answer.
Memories with `detail_level: standard` should have Quick Answer + Context.
Memories with `detail_level: comprehensive` should have all three sections.

---

## When to Expand Automatically

Expand to higher detail level automatically when:

1. **User is implementing** - They need Level 3 for code refs and implementation notes
2. **User mentions debugging** - They need Level 3 for full context
3. **User is making a related decision** - They need Level 2-3 to understand prior reasoning
4. **Memory is marked as superseded** - Include note about newer decision

---

## Best Practices

1. **Default to Level 1** - Most questions only need the Quick Answer
2. **Offer expansion** - Let user know more detail is available
3. **Cite the memory** - Reference the memory file for traceability
4. **Check for updates** - Note if memory has low confidence or is old
5. **Search multiple namespaces** - _semantic/decisions, _procedural/patterns, and _semantic/knowledge may all be relevant
