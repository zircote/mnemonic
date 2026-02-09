# ADR-011: Session-Scoped Blackboard

**Status**: Accepted

**Date**: 2026-02-09

**Authors**: Allen R.

**Deciders**: Project maintainers

## Context

The mnemonic plugin's blackboard system uses flat files (`active-tasks.md`, `session-notes.md`, `shared-context.md`) in a single `${MNEMONIC_ROOT}/.blackboard/` directory. All sessions, agents, and projects append to the same files.

### Problems

1. **Unbounded growth**: `session-notes.md` reached 4,676 lines from dozens of unrelated sessions
2. **Cross-project contamination**: Entries from `zircote/nsip` mixed with `zircote/mnemonic`
3. **No session isolation**: Agents read stale context from previous sessions
4. **No structured handoff**: Session end writes to the same file that session start reads from, with no separation between current and historical entries
5. **Performance**: Hooks tail-read multi-thousand-line files to extract the last entry

## Decision

Replace the flat blackboard with a session-scoped directory structure:

```
${MNEMONIC_ROOT}/.blackboard/
    _legacy/                    # Old files (frozen after migration)
    sessions/
        {session_id}/
            active-tasks.md
            session-notes.md
            shared-context.md
            _meta.json          # {session_id, started, ended, project, org, status}
    handoff/
        latest-handoff.md       # Overwritten by each ending session
        handoff-{session_id}.md # Archived per-session handoffs
```

### Key Design Choices

- **Session directories** use `CLAUDE_SESSION_ID` environment variable (or timestamp-pid fallback)
- **`_meta.json`** enables programmatic discovery of active vs ended sessions
- **`handoff/latest-handoff.md`** provides a single-file read for the next session's context (replacing tail-parsing of a 4,676-line file)
- **Migration is idempotent**: checks for `_legacy/` before running, safe to invoke on every session start
- **PathResolver integration**: New methods (`get_session_blackboard_dir`, `get_handoff_dir`, `list_session_blackboards`) follow the existing pattern

## Alternatives Considered

### 1. Date-based directory partitioning
Partition by date (`blackboard/2026-02/09/`) instead of session ID. Rejected because multiple sessions can run on the same day and cross-day sessions would be split.

### 2. Database-backed blackboard
Replace filesystem with SQLite or similar. Rejected as over-engineering for the current use case and breaks the filesystem-first design philosophy (ADR-001).

### 3. Append-only with periodic archival
Keep flat files but archive on a schedule. Rejected because it doesn't solve cross-project contamination or session isolation.

## Consequences

### Positive
- Session reads scoped to own directory (no parsing multi-thousand-line files)
- Cross-project contamination eliminated via `_meta.json` project field
- Clean handoff mechanism via `handoff/latest-handoff.md`
- Session metadata enables programmatic discovery and cleanup
- Backward-compatible: legacy files preserved in `_legacy/`

### Negative
- More directories to manage (one per session)
- Old tooling that hardcodes flat blackboard paths needs updating
- Migration required on first session start after upgrade

### Neutral
- `_meta.json` adds a structured metadata file alongside markdown files (consistent with memory frontmatter pattern)
- Hooks must be updated to use new paths (consolidated into `lib/` modules as part of this work)

## Related

- ADR-001: Filesystem-based storage (design philosophy)
- ADR-003: Agent coordination blackboard (original blackboard design)
- ADR-009: Unified path resolution (PathResolver pattern extended here)
