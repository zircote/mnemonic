---
allowed-tools:
- Task
- Bash
- Read
- Grep
- Glob
- Write
description: Agent-driven iterative memory search with synthesis. Uses subcall agents
  for query refinement and produces comprehensive answers.
name: mnemonic-search-enhanced
user-invocable: true
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# Mnemonic Enhanced Search Skill

Agent-driven iterative memory search with synthesis. Performs multi-round search with query refinement and produces comprehensive, synthesized answers.

## Trigger Phrases

- "deep search memories"
- "comprehensive memory search"
- "thorough search for"
- "analyze memories about"
- "synthesize knowledge about"
- "what do we know about" (followed by complex topic)

## Overview

This skill orchestrates an iterative search workflow:

1. **Initial Search**: Execute first search with user's query
2. **Analyze Results**: Identify gaps and refinement opportunities
3. **Iterative Refinement**: Up to 3 rounds of refined searches
4. **Synthesis**: Aggregate all findings into coherent answer
5. **Citation**: Reference source memories in output

### When to Use

Use enhanced search instead of basic `/mnemonic:search` when:
- Query is complex or multi-faceted
- User wants comprehensive coverage
- Topic spans multiple namespaces
- Need synthesized answer, not just file matches

---

## Workflow

### Step 0: Initialize Workflow (Optional)

For trackable workflows, register in blackboard:

```bash
WORKFLOW_ID="search-$(date +%s)"
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)-$$}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
BB_DIR="$HOME/.claude/mnemonic/.blackboard"
mkdir -p "$BB_DIR"

# Register orchestrator
cat >> "${BB_DIR}/session-notes.md" << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Agent:** search-enhanced
**Status:** active
**Capabilities:** [query-parsing, iteration-orchestration, synthesis]

## Agent Registration

Enhanced search workflow started: $WORKFLOW_ID

### Query
$QUERY

---
EOF

# Initialize shared state
cat >> "${BB_DIR}/shared-context.md" << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Agent:** search-enhanced
**Status:** active

## Shared State: $WORKFLOW_ID

### Current State
\`\`\`json
{
  "phase": "initialization",
  "query": "$QUERY",
  "scope": "$SCOPE",
  "max_iterations": $MAX_ITERATIONS,
  "iteration": 0,
  "total_findings": 0
}
\`\`\`

---
EOF
```

### Step 1: Parse User Query

Extract from user request:
- **Primary topic**: Main subject of search
- **Scope**: user, project, or all (default: all)
- **Max iterations**: 1-3 (default: 3)

```bash
QUERY="user's search query"
SCOPE="${SCOPE:-all}"
MAX_ITERATIONS="${MAX_ITERATIONS:-3}"
```

### Step 2: Generate Initial Search Patterns

Create search patterns from query:

```bash
# Primary pattern: exact query
PATTERN_1="$QUERY"

# Secondary patterns: individual key terms
PATTERN_2=$(echo "$QUERY" | tr ' ' '\n' | head -1)  # First word
PATTERN_3=$(echo "$QUERY" | tr ' ' '\n' | tail -1)  # Last word
```

### Step 3: Execute Iteration Loop

For each iteration (1 to MAX_ITERATIONS):

```
ITERATION 1:
  Pattern: Primary query
  Namespace: all
  → Invoke mnemonic-search-subcall agent
  → Collect JSON findings
  → Analyze: gaps, coverage, suggestions

ITERATION 2 (if needed):
  Pattern: Based on iteration 1 suggestions
  Namespace: Suggested namespace
  → Invoke mnemonic-search-subcall agent
  → Collect additional findings
  → Merge with iteration 1

ITERATION 3 (if needed):
  Pattern: Based on iteration 2 suggestions or related terms
  Namespace: Remaining gaps
  → Invoke mnemonic-search-subcall agent
  → Collect additional findings
  → Merge with previous
```

### Step 4: Invoke Search Subcall Agent

Use Task tool to invoke `mnemonic-search-subcall` agent:

```
Task(
  subagent_type: "mnemonic:mnemonic-search-subcall",
  prompt: "Search mnemonic memories.
    Query: {query}
    Iteration: {iteration}
    Search pattern: {pattern}
    Namespace filter: {namespace}
    Tag filter: {tag}
    Scope: {scope}

    Execute search and return JSON findings.",
  model: "haiku"
)
```

### Step 5: Detect Convergence

Stop iterating early if:
- New iteration finds < 2 new memories
- > 90% overlap with previous iteration
- All suggested namespaces searched
- Reached MAX_ITERATIONS

```python
def should_continue(current_findings, previous_findings, suggestions):
    new_files = set(current_findings) - set(previous_findings)
    if len(new_files) < 2:
        return False  # Diminishing returns
    if not suggestions:
        return False  # No more suggestions
    return True
```

### Step 6: Aggregate Findings

Merge findings from all iterations:
- Deduplicate by file path
- Preserve highest relevance rating per file
- Maintain citation counts
- Sort by relevance (high → low)

### Step 7: Read Top Memories

For top 5-10 memories (by relevance):
- Read full content
- Extract key points
- Note citations if present

```bash
for f in $TOP_MEMORIES; do
    echo "=== Reading: $f ==="
    cat "$f"
done
```

### Step 8: Synthesize Response

Produce structured markdown output:

```markdown
## Summary

[2-3 sentence executive summary answering the query]

## Key Findings

### [Category/Namespace 1]

- **[Memory Title]** (namespace, type)
  - Key point from memory
  - Evidence: "quote"
  - Citations: [if any]

### [Category/Namespace 2]

- **[Memory Title]** (namespace, type)
  - Key point from memory

## Analysis

[Synthesis connecting findings, identifying patterns, explaining relationships]

## Coverage

- **Iterations**: {count}
- **Memories examined**: {total}
- **Relevant memories**: {relevant}
- **Namespaces searched**: {list}

## Source Memories

- [[uuid-1]] - Title 1
- [[uuid-2]] - Title 2
- ...

## Gaps & Next Steps

[Areas not fully covered, suggested follow-up searches]
```

---

## Examples

### Example 1: Simple Topic Search

**User**: "What do we know about authentication?"

**Workflow**:
1. Iteration 1: Pattern "authentication" → 5 memories found
2. Suggestions: Try "OAuth", search apis namespace
3. Iteration 2: Pattern "OAuth" → 2 more memories
4. Iteration 3: Search apis namespace → 1 more memory
5. Synthesize 8 total memories

**Output**:
```markdown
## Summary

We have 8 memories about authentication covering JWT tokens, OAuth flow,
and middleware patterns. Key decision: Use JWT with RS256 signing.

## Key Findings

### Decisions
- **Use JWT for API Authentication** (decisions/project, semantic)
  - RS256 algorithm for signing
  - 15-minute access token expiry
  - Evidence: "Stateless authentication reduces server load"

### Patterns
- **Authentication Middleware Pattern** (patterns/project, procedural)
  - Always verify signature before trusting claims
  - Store refresh tokens in httpOnly cookies

...

## Source Memories

- [[abc123]] - Use JWT for API Authentication
- [[def456]] - Authentication Middleware Pattern
```

### Example 2: Complex Multi-Faceted Query

**User**: "Synthesize everything about our database decisions and performance learnings"

**Workflow**:
1. Iteration 1: Pattern "database" in decisions → 3 memories
2. Iteration 2: Pattern "performance" in learnings → 4 memories
3. Iteration 3: Pattern "PostgreSQL OR MySQL" in all → 2 more
4. Synthesize 9 total memories with cross-references

---

## Best Practices

### Query Refinement Strategy

1. **Start broad**: Use user's exact query first
2. **Narrow by namespace**: Focus on most relevant category
3. **Expand by related terms**: Use terms found in initial results
4. **Check suggestions**: Follow subcall agent's refinement suggestions

### Performance Optimization

- Limit to 10 files per iteration (use head -10)
- Read frontmatter + snippet only during search
- Full read only for top 5-10 final memories
- Use haiku model for subcalls (cost-effective)

### Context Conservation

- Subcall agents run in isolated context
- Only JSON findings returned to main context
- Full memory content read only during synthesis
- Total context usage: ~3-5k tokens typical

---

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| MAX_ITERATIONS | 3 | Maximum search rounds |
| FILES_PER_ITERATION | 10 | Max files to process per round |
| TOP_MEMORIES | 10 | Full memories to read for synthesis |
| MODEL | haiku | Model for subcall agents |

---

## Error Handling

| Condition | Action |
|-----------|--------|
| No results in iteration 1 | Try broader pattern, check spelling |
| Subcall agent timeout | Skip iteration, continue with current findings |
| Malformed JSON from subcall | Log error, skip that iteration |
| Max iterations reached | Proceed to synthesis with available findings |

---

### Step 9: Complete Workflow (Optional)

For trackable workflows, update blackboard on completion:

```bash
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Update shared state
cat >> "${BB_DIR}/shared-context.md" << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Agent:** search-enhanced
**Status:** idle

## Shared State: $WORKFLOW_ID

### Final State
\`\`\`json
{
  "phase": "complete",
  "iterations": $ITERATIONS_RUN,
  "total_findings": $TOTAL_FINDINGS,
  "memories_synthesized": $MEMORIES_READ
}
\`\`\`

---
EOF

# Update agent status
cat >> "${BB_DIR}/session-notes.md" << EOF

---
**Session:** $SESSION_ID
**Time:** $TIMESTAMP
**Agent:** search-enhanced
**Status:** idle

## Workflow Complete

### Summary
- Workflow: $WORKFLOW_ID
- Iterations: $ITERATIONS_RUN
- Findings: $TOTAL_FINDINGS
- Memories synthesized: $MEMORIES_READ

---
EOF
```

---

## Related

- `/mnemonic:search` - Basic single-shot search (faster, simpler)
- `mnemonic-search-subcall` agent - Executes individual search rounds
- `mnemonic-search` skill - Advanced search patterns reference
- `mnemonic-agent-coordination` skill - Agent coordination patterns
