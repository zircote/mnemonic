---
name: custodian
allowed-tools:
- Bash
- Read
- Write
- Glob
- Grep
- Task
argument-hint: '[audit|relocate|validate-links|decay|summarize|validate-memories|validate-relationships] [--dry-run] [--fix] [--json] [--commit]'
description: Unified memory custodian for audits, validation, and maintenance
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# /mnemonic:custodian

Comprehensive memory system custodian for health checks, validation, and maintenance.

## Usage

```
/mnemonic:custodian [operation] [options]
```

## Operations

### audit (default)

Full health check: links, decay, relationships, orphans, frontmatter completeness.

```
/mnemonic:custodian audit [--fix] [--dry-run] [--json]
```

Runs all checks in a single pass:
1. Validate memory frontmatter (required fields, types, formats)
2. Validate wiki-links and frontmatter relationship targets
3. Validate ontological relationship types
4. Recalculate decay strength values
5. Detect orphaned memories (no incoming references)

### relocate

Move memories when project or org names change. Auto-updates all cross-references.

```
/mnemonic:custodian relocate <old-path> <new-path> [--dry-run] [--commit]
```

Example:
```bash
# Project renamed from old-api to new-api
/mnemonic:custodian relocate ${MNEMONIC_ROOT}/zircote/old-api ${MNEMONIC_ROOT}/zircote/new-api
```

Steps:
1. Build link index across all memory roots
2. Update path references in all memories
3. Move files (using `git mv` when available)
4. Clean up empty directories

### validate-links

Check and optionally repair wiki-links, UUID references, and frontmatter relationships.

```
/mnemonic:custodian validate-links [--fix] [--json]
```

With `--fix`: removes broken `[[wiki-links]]` from body text (replaces with plain text).

### decay

Recalculate exponential decay strength values and update frontmatter in-place.

```
/mnemonic:custodian decay [--dry-run] [--json]
```

Formula: `strength = current_strength * 0.5^(days_since_access / half_life_days)`

Supports models: `exponential`, `linear`, `step`, `none`.

### summarize

Find memories eligible for compression. Reports candidates for the compression-worker agent.

```
/mnemonic:custodian summarize [--dry-run] [--json]
```

Candidates: memories with >100 lines that are >30 days old OR have strength < 0.3.

To compress, invoke the `mnemonic:compression-worker` agent for each candidate.

### validate-memories

Check memory frontmatter completeness against MIF schema.

```
/mnemonic:custodian validate-memories [--json]
```

Checks: required fields (id, type, title, created), UUID format, type enum, date format, confidence range, namespace/path consistency.

### validate-relationships

Verify ontological relationship types and targets.

```
/mnemonic:custodian validate-relationships [--json]
```

Checks: relationship type validity (against MIF built-in + ontology custom types), target existence, strength range.

## Options

- `--dry-run` - Preview changes without modifying files
- `--fix` - Auto-repair issues found (validate-links, audit)
- `--json` - Output report as JSON instead of markdown
- `--commit` - Git commit after changes are applied

## Procedure

```bash
PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $0))}"
python3 "$PLUGIN_DIR/skills/custodian/lib/custodian.py" "$@"
```

If Python execution fails, fall back to manual execution of each subcommand using the skill guidance in `skills/custodian/SKILL.md`.

## Examples

```bash
# Full health check (default)
/mnemonic:custodian

# Preview what audit would find
/mnemonic:custodian audit --dry-run

# Fix broken links and commit
/mnemonic:custodian validate-links --fix --commit

# Update all decay scores
/mnemonic:custodian decay --commit

# Move project memories after rename
/mnemonic:custodian relocate ${MNEMONIC_ROOT}/org/old-name ${MNEMONIC_ROOT}/org/new-name --commit

# JSON output for programmatic use
/mnemonic:custodian audit --json
```

## Output

Displays a structured report with:
- Summary (total findings, errors, warnings, fixes applied)
- Errors grouped by category (links, frontmatter, relationships, decay)
- Warnings (orphans, namespace mismatches)
- Recommendations for follow-up actions
