---
name: test-report
description: Generate test execution report in various formats
arguments:
  - name: format
    description: Output format (markdown, html, json)
    required: false
  - name: output
    description: Output file path (defaults to stdout)
    required: false
---

# Generate Test Report

Create a comprehensive report of test execution results.

## Report Generation

<step name="check-state">
Verify test state exists:

```bash
if [[ ! -f ".claude/test-state.json" ]]; then
  echo "No test results found. Run /run-tests first."
  exit 1
fi
```
</step>

<step name="generate-report">
Call the runner to generate the report:

```bash
"./.claude/tests/runner.sh" report {{#if format}}--format {{format}}{{/if}}
```
</step>

<step name="output-report">
If output path specified, write to file:

```bash
"./.claude/tests/runner.sh" report --format {{format}} > {{output}}
```

Otherwise, display in conversation.
</step>

## Report Formats

### Markdown (default)

```markdown
# Test Execution Report

**Generated:** 2026-01-24T15:30:00Z

## Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Passed | 18 | 90.0% |
| ❌ Failed | 1 | 5.0% |
| ⏭️ Skipped | 1 | 5.0% |
| **Total** | **20** | **100%** |

## Failed Tests

### cmd_search_empty
**Category:** commands
**Description:** Search with no results returns empty message

**Expected:**
- contains: "no results"

**Actual Response:**
> Found 0 matches for query

**Failure:** Missing 'no results'

## Passed Tests

<details>
<summary>18 tests passed (click to expand)</summary>

- ✅ smoke_basic
- ✅ cmd_capture_basic
- ✅ cmd_recall_basic
...
</details>
```

### JSON

```json
{
  "generated_at": "2026-01-24T15:30:00Z",
  "summary": {
    "total": 20,
    "passed": 18,
    "failed": 1,
    "skipped": 1,
    "pass_rate": 0.90
  },
  "results": [...],
  "metadata": {
    "filters": {
      "category": null,
      "tag": null
    },
    "test_file": ".claude/tests/tests.yaml",
    "runner_version": "1.0.0"
  }
}
```

### HTML

Generates styled HTML with:
- Color-coded status badges
- Collapsible sections
- Syntax highlighting for responses
- Print-friendly styling

## CI Integration

For CI/CD pipelines, use JSON format and check exit code:

```bash
./.claude/tests/runner.sh report --format json > test-results.json

# Check for failures
failures=$(jq '.summary.failed' test-results.json)
if [[ "$failures" -gt 0 ]]; then
  echo "Tests failed: $failures"
  exit 1
fi
```

## Historical Reports

Reports are saved to `.claude/tests/reports/` by default:

```
.claude/tests/reports/
├── 2026-01-24T15-30-00.md
├── 2026-01-24T15-30-00.json
└── latest.md -> 2026-01-24T15-30-00.md
```
