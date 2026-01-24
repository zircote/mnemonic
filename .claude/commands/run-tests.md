---
name: run-tests
description: Run automated functional tests using the hook-driven test framework. Execute the test suite to validate all project functionality.
argument-hint: "[--category <name>] [--tag <tag>] [--verbose] [--dry-run]"
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Glob, Grep
---

# /run-tests

Execute the automated functional test suite to validate all project components.

## Usage

```
/run-tests [options]
```

### Options

- `--category <name>` - Run only tests in specified category
- `--tag <tag>` - Run only tests with specified tag
- `--verbose` - Show detailed output for each test
- `--dry-run` - Show tests that would run without executing

## Execution Strategy

<strategy>
**Test Orchestration Flow:**

1. Read test definitions from `.claude/tests/tests.yaml`
2. Initialize test state in `.claude/test-state.json`
3. Execute tests sequentially, tracking results
4. Validate each test response against expected patterns
5. Generate summary report

**State Management:**
- State file tracks: current test, results, saved variables
- Each test can save output values for dependent tests
- Tests with `depends_on` wait for dependencies to pass
</strategy>

## Workflow

<workflow>
When invoked:

### Phase 1: Initialization

1. **Load Test Suite**
   - Read `.claude/tests/tests.yaml`
   - Parse test definitions
   - Filter by category/tag if specified

2. **Initialize State**
   Run: `./.claude/tests/runner.sh reset && ./.claude/tests/runner.sh init`

3. **Show Test Plan**
   Display total tests and categories to run

### Phase 2: Test Execution Loop

For each test, execute automatically without waiting for user input:

1. **Get Next Test**
   Run: `./.claude/tests/runner.sh next`

2. **Execute Test Action**
   Parse the action from test output and execute it:
   - If action starts with "Run:" - execute the bash command
   - If action starts with "Check:" - cat/ls the target file
   - Otherwise - execute as described

3. **Validate Response**
   Run: `./.claude/tests/runner.sh validate "$response"`

4. **Record and Continue**
   Display pass/fail result and proceed to next test

### Phase 3: Report Generation

After all tests complete:

Run: `./.claude/tests/runner.sh report --format md`

Display final summary with pass/fail counts.
</workflow>

## Test Format Reference

<format>
```yaml
- id: unique_test_id
  description: Human readable description
  category: category_name
  action: The exact action to execute
  expect:
    - contains: string that must appear
    - not_contains: string that must NOT appear
    - regex: pattern.*to.*match
  tags: [tag1, tag2]
  save_as: variable_name
  depends_on: other_test_id
```
</format>

## Filtering Options

### By Category
```
/run-tests --category commands
/run-tests --category skills
/run-tests --category agents
```

### By Tag
```
/run-tests --tag smoke
/run-tests --tag critical
/run-tests --tag regression
```

### Combined
```
/run-tests --category commands --tag smoke
```
