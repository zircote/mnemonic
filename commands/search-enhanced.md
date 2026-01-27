---
description: Agent-driven iterative search with synthesis
argument-hint: "<query> [--scope user|project|all] [--max-iterations 1-3]"
allowed-tools:
  - Task
  - Bash
  - Read
  - Grep
  - Glob
---

# /mnemonic:search-enhanced

Agent-driven iterative search across mnemonic memories with synthesis. Uses subcall agents for query refinement and produces comprehensive, synthesized answers.

## Arguments

- `<query>` - Required. Search query or question
- `--scope` - Search scope: user, project, or all (default: all)
- `--max-iterations` - Maximum search iterations 1-3 (default: 3)

## When to Use

Use `/mnemonic:search-enhanced` instead of `/mnemonic:search` when:
- Query is complex or multi-faceted
- You want comprehensive coverage across namespaces
- You need a synthesized answer, not just file matches
- Topic may span multiple memory types

For simple, fast searches use `/mnemonic:search` instead.

## Procedure

### Step 1: Parse Arguments

```bash
QUERY="${1:?Error: Query required}"
SCOPE="${SCOPE:-all}"
MAX_ITERATIONS="${MAX_ITERATIONS:-3}"
```

### Step 2: Initialize

```bash
echo "=== Enhanced Memory Search ==="
echo "Query: $QUERY"
echo "Scope: $SCOPE"
echo "Max iterations: $MAX_ITERATIONS"
echo ""
```

### Step 3: Invoke mnemonic-search-enhanced Skill

The skill handles the full workflow:
1. Execute iterative search with subcall agents
2. Refine queries based on findings
3. Aggregate and deduplicate results
4. Synthesize comprehensive answer

### Step 4: Display Results

The skill produces structured markdown output:
- Summary answering the query
- Key findings by category
- Analysis connecting findings
- Source memory references
- Gaps and suggested follow-ups

## Example Usage

### Basic Enhanced Search

```
/mnemonic:search-enhanced "authentication security patterns"
```

### Project-Scoped Search

```
/mnemonic:search-enhanced "database performance" --scope project
```

### Quick Enhanced Search (1 iteration)

```
/mnemonic:search-enhanced "API endpoints" --max-iterations 1
```

### Comprehensive Search

```
/mnemonic:search-enhanced "everything about our testing strategy" --max-iterations 3
```

## Output Format

```markdown
## Summary

[2-3 sentence executive summary answering the query]

## Key Findings

### [Category]
- **[Memory Title]** (namespace, type)
  - Key insight
  - Evidence: "quote"

## Analysis

[Synthesis connecting findings]

## Coverage

- Iterations: 3
- Memories examined: 45
- Relevant memories: 12
- Namespaces searched: _semantic/decisions, _semantic/knowledge, _procedural/patterns

## Source Memories

- [[uuid-1]] - Memory Title 1
- [[uuid-2]] - Memory Title 2

## Gaps & Next Steps

[Suggested follow-up searches]
```

## Performance

| Metric | Typical Value |
|--------|---------------|
| Iterations | 2-3 |
| Runtime | 15-30 seconds |
| Memories examined | 20-50 |
| Context usage | 3-5k tokens |

Enhanced search is slower than basic `/mnemonic:search` but provides:
- Comprehensive coverage across namespaces
- Synthesized answers (not just matches)
- Automatic query refinement
- Citation of source memories

## Comparison

| Feature | `/mnemonic:search` | `/mnemonic:search-enhanced` |
|---------|-------------------|----------------------------|
| Speed | Fast (~2s) | Slower (~20s) |
| Output | File matches | Synthesized answer |
| Refinement | None | Iterative |
| Coverage | Single pattern | Multi-pattern |
| Use case | Quick lookup | Comprehensive analysis |

## Related

- `/mnemonic:search` - Basic single-shot search
- `/mnemonic:recall` - Structured recall with filters
- `mnemonic-search` skill - Advanced search patterns
- `mnemonic-search-enhanced` skill - Full orchestration details
