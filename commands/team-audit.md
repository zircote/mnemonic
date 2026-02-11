---
name: team-audit
description: Comprehensive health audit with parallel agent remediation across all memory phases
allowed-tools:
- Bash
- Read
- Write
- Edit
- Glob
- Grep
- Task
argument-hint: '[--dry-run] [--phase 1|2|3|4|5|all]'
---
<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory

Search first: `/mnemonic:search {relevant_keywords}`
Capture after: `/mnemonic:capture {namespace} "{title}"`

Run `/mnemonic:list --namespaces` to see available namespaces from loaded ontologies.
<!-- END MNEMONIC PROTOCOL -->

# /mnemonic:team-audit

Comprehensive health audit of the mnemonic memory system with parallel agent remediation.

## Arguments

- `--dry-run` — Report issues without modifying files
- `--phase <N|all>` — Run a specific phase (1-5) or all phases (default: all)

## Setup

```bash
# Resolve MNEMONIC_ROOT from config
if [ -f "$HOME/.config/mnemonic/config.json" ]; then
    RAW_PATH=$(python3 -c "import json; print(json.load(open('$HOME/.config/mnemonic/config.json')).get('memory_store_path', '~/.claude/mnemonic'))")
    MNEMONIC_ROOT="${RAW_PATH/#\~/$HOME}"
else
    MNEMONIC_ROOT="$HOME/.claude/mnemonic"
fi
```

## Phases

Orchestrate a team of agents to execute phases in parallel where possible.

### Phase 1: Duplicate Detection & Archival

Scan all active memories (exclude `.archive/`) for duplicates across three vectors:

1. **Same-topic duplicates within a namespace** — memories with similar titles/content about the same decision, pattern, or knowledge item. Use `lib.search.find_duplicates()` or Python fuzzy matching on titles. Read candidates to confirm.
2. **Cross-namespace duplicates** — identical memories in both `default/` and project-specific paths, or in both org-level and project-level paths. Keep project-specific, archive generic.
3. **Shared UUID duplicates** — memories with identical `id:` fields across different paths. Keep one, archive the other.

For each confirmed duplicate cluster: keep the most complete/recent, archive the rest to `.archive/YYYY-MM/custodian-dedup/`.

### Phase 2: Frontmatter Validation & Repair

Validate all active memories against the MIF schema:

- **Required fields**: `id` (valid UUID4), `type` (semantic|procedural|episodic), `title`, `created` (ISO 8601)
- **Placeholder detection**: Replace `PLACEHOLDER_UUID`, `MEMORY_ID_PLACEHOLDER`, `DATE_PLACEHOLDER`, `${UUID}`, `${DATE}` with real generated values
- **Type-path consistency**: `type:` must match directory path (`_semantic/` → semantic, `_procedural/` → procedural, `_episodic/` → episodic)
- **Namespace-path consistency**: `namespace:` must match cognitive triad path. Strip `/user`, `/project` suffixes.
- **Frontmatter delimiters**: Exactly 2 `---` per file. Replace extra `---` in body with `***`.
- **Broken merge templates**: Remove lines containing `> Merged from memory ${UUID}` or unresolved template variables.

### Phase 3: Decay & Strength Management

- **Add decay fields** to memories missing them: `strength: 1.0`, `half_life:` (per defaults), `last_accessed:` (file mtime), `decay_model: exponential`
- **Recalculate stale strengths**: `strength = 0.5^(days_since_access / half_life_days)`
- **Normalize schema**: Flatten nested `decay:` blocks to top-level fields

**Half-life defaults:**

| Namespace | Half-life |
|-----------|-----------|
| `_semantic/decisions` | P180D |
| `_semantic/knowledge` | P90D |
| `_procedural/patterns` | P180D |
| `_procedural/runbooks` | P180D |
| `_episodic/blockers` | P30D |
| `_episodic/sessions` | P30D |
| `_episodic/incidents` | P60D |

### Phase 4: Link Validation

- Find all `[[wiki-links]]` in memory bodies. Check if targets exist. Replace broken links with plain text.
- Validate frontmatter `relationships:` entries against the canonical MIF relationship registry (all supported types including inverse forms, both snake_case and PascalCase). Remove references to non-existent memories or invalid relationship types.

### Phase 5: Prevention — Capture Workflow Audit

Audit the mnemonic plugin source for correctness:

1. **Capture template** (`skills/mnemonic-core/SKILL.md`): Verify minimal format includes `namespace`, `confidence`, `strength`, `half_life`, `last_accessed`, `decay_model`, `provenance`.
2. **Dedup check** (`skills/mnemonic-core/SKILL.md`, `references/capture.md`, `commands/capture.md`): Verify mandatory search-before-capture step exists.
3. **Namespace routing**: Verify memories route to `${ORG}/${PROJECT}/${NAMESPACE}`, not `default/` or bare org paths.

## Deliverables

After all phases, report:

| Metric | Value |
|--------|-------|
| Active memories before/after | |
| Duplicates archived (by type) | |
| Frontmatter issues fixed (by category) | |
| Decay coverage % | |
| Broken links repaired | |
| Prevention measures verified | |
