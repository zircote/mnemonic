# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **[Ontology Discovery]**: Enhanced pattern-based entity discovery (`f642fde`)
  - Improved schema validation for custom ontologies
  - Discovery patterns for automatic entity detection

- **[Integration Skill]**: Python-based memory integration with test suite (`1681803`)
  - Migrate memories between organizations/projects
  - Batch operations with progress tracking
  - Comprehensive test coverage

- **[Memory Protocol]**: Stronger prompt engineering for compliance (`ba39754`)
  - Commitment-based framing (vs command-based)
  - Identity reinforcement for persistent memory
  - Stop hook blocks until captures complete

- **[Social Graphics]**: PNG versions for README badges (`cfa77af`)
  - Cognitive namespace visualizations
  - Ontology structure diagrams

- **[Path Resolution Library]**: Centralized path management in `lib/paths.py`
  - `PathResolver` class with V2 unified path scheme
  - `PathContext` dataclass for context detection (org, project, home, scheme)
  - `PathScheme` enum (LEGACY, V2) for migration support
  - `Scope` enum (USER, PROJECT, ORG) for memory scoping
  - Convenience functions: `get_memory_dir()`, `get_search_paths()`, `get_blackboard_dir()`
  - 26 unit tests in `tests/unit/test_paths.py`

- **[Migration Script]**: `scripts/migrate_to_v2_paths.py`
  - Migrates memories from dual-location (LEGACY) to unified (V2) path structure
  - Automatic backup creation before migration
  - Rollback capability
  - `--dry-run` mode for previewing changes
  - Progress tracking and git commit of changes

### Changed

- **[Unified Path Structure]**: All memories now stored under `~/.claude/mnemonic/`
  - Eliminates "split brain" between user-level and project-level storage
  - New structure: `{org}/{project}/{namespace}/` for project-specific memories
  - Org-wide: `{org}/{namespace}/` for memories shared across projects
  - Fallback: `default/{namespace}/` when org detection fails
  - Single git repository for all memories

- **[Cognitive Namespace Prefix]**: All cognitive triad namespaces now prefixed with `_` (`40752d1`)
  - `_semantic/`, `_episodic/`, `_procedural/` distinguish system namespaces
  - Prevents collision with user-defined namespaces

- **[Documentation]**: Migrated to cognitive namespace structure (`bcfe79f`)
  - All docs updated for unified path structure
  - Social graphics reflect new ontology model

- **[Hooks]**: Updated to use PathResolver
  - `session_start.py`: Uses PathResolver for path resolution with LEGACY fallback
  - `user_prompt_submit.py`: Uses PathResolver for memory search paths
  - Hooks check both V2 and LEGACY paths during migration period

- **[Commands]**: Updated scope options
  - `capture.md`: `--scope project|org` (was `user|project`)
  - `recall.md`: `--scope project|org|all` (was `user|project|all`)

- **[Code Quality]**: Simplified functional test infrastructure
  - Extracted `ClaudeRunner` and `MemoryHelper` classes to module level
  - Extracted `NAMESPACE_MAP` and `MEMORY_WRITE_DELAY` constants
  - Replaced debug prints with `logging.debug()`
  - Simplified verbose GIVEN/WHEN/THEN docstrings to concise single-line format
  - Improved assertion messages with expected vs actual context

- **[Scripts]**: Improved migration and repair scripts
  - `migrate_scope_paths.py`: Returns `(migrations, errors)` tuple for better error handling
  - `fix_malformed_memories.py`: Extracted `_format_yaml_field` helper, replaced conditional chains with dict mapping
  - Removed unused `current_key` variable from YAML parser

- **[Hooks]**: Refined `user_prompt_submit.py`
  - Simplified `detect_triggers()` using `any()` pattern
  - Use specific exception types (`yaml.YAMLError`, `OSError`, `subprocess.SubprocessError`)

### Fixed

- **[Hooks]**: Read tool data from stdin instead of environment variables (`39cf67a`)
  - Fixes hook data passing in Claude Code environment
  - All hooks now properly receive tool context

- **[Plugin]**: Removed duplicate hooks reference from manifest (`b2deea3`)
  - Hooks now loaded exclusively from `hooks/hooks.json`
  - Added `.fastembed_cache/` to gitignore

- **[Security]**: Hardened ontology and integrate skills (`a3dcc4a`)
  - Improved input validation
  - Better error handling for edge cases

- **[Git History]**: Purged `.fastembed_cache/` directories from repository history

### Migration Guide

To migrate existing memories to the unified path structure:

```bash
# Preview changes
python scripts/migrate_to_v2_paths.py --dry-run

# Execute migration (creates backup automatically)
python scripts/migrate_to_v2_paths.py

# Rollback if needed
python scripts/migrate_to_v2_paths.py --rollback ~/.claude/mnemonic_backups/legacy_backup_TIMESTAMP
```

### Planned

- Semantic search with embeddings
- Export/import functionality
- Web UI for memory browsing

## [2.0.0] - 2026-01-26

### Breaking Changes

- **Namespace Hierarchy**: Migrated from 9 flat namespaces to cognitive triad hierarchy
  - Old: `apis`, `blockers`, `context`, `decisions`, `learnings`, `patterns`, `security`, `testing`, `episodic`
  - New: `semantic/`, `episodic/`, `procedural/` with sub-namespaces

### Added

- **MIF Submodule**: Ontologies now sourced from [MIF](https://github.com/zircote/MIF)
  - `mif-base.ontology.yaml` defines cognitive triad hierarchy
  - JSON-LD export for semantic web compatibility
  - `scripts/yaml2jsonld.py` converter

- **Cognitive Triad Namespaces**:
  - `semantic/decisions` - Architectural choices
  - `semantic/knowledge` - APIs, context, learnings, security
  - `semantic/entities` - Technologies, components
  - `episodic/incidents` - Production issues
  - `episodic/sessions` - Debug sessions
  - `episodic/blockers` - Impediments
  - `procedural/runbooks` - Operational procedures
  - `procedural/patterns` - Code conventions, testing
  - `procedural/migrations` - Migration steps

- **Ontology Loader**: Centralized MIF loading (`skills/ontology/lib/ontology_loader.py`)
- **Fallback Support**: Offline installations via `skills/ontology/fallback/`
- **Migration Script**: `scripts/migrate_namespaces.py` for upgrading existing memories

### Changed

- **Hooks**: Updated to use hierarchical namespace paths
- **Commands**: `/mnemonic:capture` supports new namespace format
- **Documentation**: Updated for cognitive triad model

### Migration Guide

1. **Run migration script** (one-time, required):
   ```bash
   python scripts/migrate_namespaces.py --dry-run
   python scripts/migrate_namespaces.py --commit
   ```
2. **Update custom ontologies** to use hierarchical namespaces:
   ```yaml
   namespaces:
     semantic:
       children:
         my-namespace:
           description: "..."
   ```

## [1.3.0] - 2026-01-25

### Changed

- **[CLAUDE.md Protocol]**: Role-based, imperative instructions (Anthropic Prompt Engineering)
  - Added role assignment: "developer with persistent memory"
  - Changed passive "Ask yourself" to structured `<capture_eval>` block
  - Reduced from 63 lines to 30 lines for focused instruction
  - Imperative language throughout ("Search first. Always.")

- **[mnemonic-core Skill]**: Progressive disclosure architecture
  - Reduced SKILL.md from 495 lines to 52 lines (quick reference only)
  - Split detailed workflows into `references/` subdirectory:
    - `capture.md` - Full capture workflow
    - `recall.md` - Search and retrieval patterns
    - `schema.md` - Complete MIF Level 3 schema
    - `examples.md` - Working examples
  - Follows Anthropic Architect principle: "Show only what's needed, when it's needed"

- **[mnemonic-format Skill]**: Simplified schema emphasis
  - Lead with minimal 4-field template (id, title, type, created)
  - All other fields marked as optional
  - Reduces barrier to adoption

- **[Hook Architecture]**: Context hints only, no auto-capture
  - `user_prompt_submit.py`: Removed `create_memory()` function
  - Hooks provide capture signals, Claude uses skills to capture
  - Aligns with skills-first architecture principle
  - `post_tool_use.py`: Updated to reference `/mnemonic:capture` skill

- **[Commands]**: Updated CLAUDE.md templates in init.md and setup.md
  - Match new role-based, imperative style
  - Simplified initial context memory to 4-field format

- **[Test Suite]**: Replaced contrived tests with natural behavior tests
  - Removed 25+ "no error" command tests
  - Added 18 functional tests validating automatic capture/recall without explicit commands
  - Tests verify silent operation, content quality, no duplicates
  - Tests use `--plugin-dir` flag to properly load plugin hooks

### Added

- **[Stop Hook Enforcement]**: Blocks Claude from stopping until captures complete
  - `stop.py` checks for pending captures via temp file
  - Uses `decision: "block"` with reason to force capture before stopping
  - Prevents `stop_hook_active` infinite loops
  - Clears pending state after successful capture

- **[Pending Capture State]**: Session-aware capture tracking
  - `user_prompt_submit.py` writes pending captures to `/tmp/mnemonic-pending-{session_id}.json`
  - Uses `CLAUDE_SESSION_ID` for consistent cross-hook communication
  - Stop hook reads and enforces pending captures

### Fixed

- **[Pattern Triggers]**: Fixed pattern namespace detection
  - Added `\bshould always\b` and `\balways use\b` patterns
  - Original `\balways\b.*\bwhen\b` missed common phrases like "We should always use X"

- **[Skill Description]**: Updated mnemonic-core for auto-loading
  - Added explicit trigger phrases to description field
  - Enables Claude to auto-load skill when relevant phrases detected

- **[Templates]**: Heredoc variable expansion in mnemonic-core/SKILL.md
  - Changed `'MEMORY_EOF'` to `MEMORY_EOF` (unquoted)
  - Changed `{UUID}` placeholders to `${UUID}` bash variables

### Removed

- **[Cognitive Bridge]**: Entire cognitive bridge feature removed
  - Removed bridge commands: `/mnemonic:bridge-scan`, `/mnemonic:bridge-status`, `/mnemonic:bridge-sync`
  - Removed bridge skills: `bridge-core`, `bridge-triggers`, `bridge-synthesis`, `bridge-integration`
  - Removed bridge agents: `capability-mapper`, `pattern-synthesizer`
  - Removed `check_registry()` from `session_start.py` hook
  - Removed bridge documentation and architecture diagrams
  - Skills-first approach replaces bridge's hook-centric pattern

## [1.2.0] - 2026-01-24

### Added

- **[Cognitive Bridge]**: Plugin integration and intelligent context injection
  - `PreToolUse` hook for file pattern detection (auth, api, db, test, config, deploy, security)
  - Relevant memory file paths provided when editing related files
  - Bridge registry for plugin capability mapping
  - Pattern synthesis for cross-memory knowledge consolidation

- **[Bridge Skills]**: Four new skills for cognitive bridge
  - `bridge-core`: Interpreting session context and memory availability
  - `bridge-triggers`: File pattern to namespace mappings
  - `bridge-synthesis`: Pattern consolidation and meta-pattern creation
  - `bridge-integration`: Plugin integration for memory capture

- **[Bridge Agents]**: Two new agents for automated operations
  - `capability-mapper`: Discovers plugins and builds bridge registry
  - `pattern-synthesizer`: Analyzes memories for patterns and creates meta-patterns

- **[Bridge Commands]**: Three new commands
  - `/mnemonic:bridge-scan`: Discover plugins and build bridge registry
  - `/mnemonic:bridge-status`: Show registry, memory health, blackboard status
  - `/mnemonic:bridge-sync`: Process blackboard and synthesize patterns

### Changed

- **[Hooks]**: All hooks now use `hookSpecificOutput.additionalContext` for Claude-readable context
  - SessionStart: Provides memory counts, health score, registry status, suggestions
  - PreToolUse: Provides relevant memory file paths for file edits
  - UserPromptSubmit: Provides capture/recall trigger context
  - PostToolUse: Provides capture opportunity context
  - Stop: Provides session summary context

- **[Architecture]**: Hooks inform, Claude decides
  - Hooks provide context, not instructions
  - Claude autonomously decides when to read memories or use agents
  - Agents invoked via commands, not hook triggers

### Technical

- Hooks execute in <100ms with timeouts (3-5s)
- Fast pattern matching with regex and ripgrep
- Memory health scoring based on confidence decay and duplicates

## [1.1.1] - 2026-01-24

### Added

- **[Query Command]**: New `/mnemonic:query` command for confidence-rated memory retrieval
  - `tools/mnemonic-query` Python CLI with structured output
  - Confidence scoring based on age, strength, and access patterns
  - JSON output format for programmatic use
  - Test fixtures for confidence scoring validation
- **[Test Framework]**: Extended test definitions in `.claude/tests/tests.yaml`
  - Additional test cases for query command
  - Improved test coverage
- **[Research Reports]**: Comprehensive market research report
  - Full report in Markdown and HTML formats
  - Executive summary
  - Mermaid visualizations for competitive positioning, SWOT, risk matrix

### Changed

- **[Search Skill]**: Enhanced `mnemonic-search` with confidence-aware patterns
- **[README]**: Updated feature documentation
- **[Makefile]**: Added query-related targets

### Fixed

- **[Reports]**: Corrected inaccurate feature status in research report
  - Marked decay/archival as implemented (gc command)
  - Marked citation validation as implemented (mnemonic-validate)
  - Fixed Mermaid SWOT quadrant syntax (`<-->` → `-->`)
- **[Plugin]**: Removed duplicate hooks reference from manifest

## [1.1.0] - 2026-01-24

### Added

- **[Citations]**: Optional citations array in MIF format for external references
  - Supports types: paper, documentation, blog, github, stackoverflow, article
  - Fields: title, url, author, date, accessed, relevance, note
  - Validation rules for citation fields
  - Search patterns for finding memories by citation
- **[Enhanced Search]**: Agent-driven iterative search with synthesis
  - `/mnemonic:search-enhanced` command for comprehensive memory analysis
  - `mnemonic-search-enhanced` skill for orchestrating multi-round search
  - `mnemonic-search-subcall` agent (Haiku) for targeted search operations
  - Iterative query refinement (up to 3 rounds)
  - Synthesized answers instead of raw file matches
- **[GitHub Integration]**: GitHub Copilot agent configuration
- **[Plugin Config]**: ADR and sigint plugin configurations
- **[Validation Tool]**: MIF Level 3 schema validation for memory files
  - `tools/mnemonic-validate` Python CLI for validating memories
  - Validates required fields, types, UUID format, ISO 8601 timestamps
  - Validates code_refs (file paths, line numbers, types)
  - Validates citations (types, URLs, relevance scores)
  - Validates memory links (`[[uuid]]` resolution)
  - JSON and Markdown output formats
  - `--capture` flag to save validation runs as episodic memories
  - `--changed` flag for git-modified files only
  - Makefile targets: `validate-memories`, `validate-memories-ci`
- **[Memory Compression]**: Auto-summarization for verbose memories
  - `compression-worker` agent (Haiku) for generating concise summaries
  - New gc flags: `--compress`, `--compress-only`, `--compress-threshold`
  - Compression criteria: (Age > 30d AND lines > 100) OR (strength < 0.3 AND lines > 100)
  - Adds `summary` and `compressed_at` fields to MIF frontmatter
- **[Multi-Agent Coordination]**: Blackboard-based agent coordination
  - `mnemonic-agent-coordination` skill with agent patterns
  - Agent registration in `session-notes.md`
  - Task handoffs with context in `active-tasks.md`
  - Shared workflow state in `shared-context.md`
  - Progress reporting for subcall agents
  - Extended blackboard entry format with Agent, Status, Capabilities fields
- **[ADRs]**: Five new architectural decision records
  - ADR-003: Agent Coordination via Blackboard Extension
  - ADR-004: MIF Schema as Single Source of Truth for Validation
  - ADR-005: Memory Compression via GC Extension
  - ADR-006: Validation Results as Episodic Memories
  - ADR-007: Enhanced Search with Agent-Driven Iteration
- **[Test Framework]**: Hook-driven test framework for plugin validation
  - `.claude/tests/tests.yaml` - Test definitions with expectations
  - `.claude/tests/runner.sh` - Test execution and validation
  - `.claude/hooks/test-wrapper.sh` - User prompt interception for test mode
  - 25 functional tests covering commands, skills, agents, integration, and error handling

### Changed

- **[Hooks]**: Format Python files with ruff
- **[ADRs]**: Rename ADRs to 3-digit numbering scheme
- **[GC Command]**: Extended with compression capabilities
- **[Agents]**: memory-curator and search-subcall now use blackboard coordination
- **[Skills]**: mnemonic-search-enhanced uses blackboard for workflow state

### Fixed

- **[Stop Hook]**: Skip verbose output during test mode to prevent test interruption
  - Removed XML-style `<mnemonic-session-end>` tags that could cause parsing issues
  - Added `is_test_mode()` detection based on test-state.json
- **[Test Expectations]**: Updated `agent_search_subcall_basic` test to use specific failure patterns

### Documentation

- **[Reports]**: Add AI memory filesystem research
- **[validation.md]**: Validation tool usage and CI integration
- **[agent-coordination.md]**: Multi-agent coordination patterns and examples
- **[Enterprise Package]**: Comprehensive documentation for enterprise adoption
  - `docs/enterprise/README.md` - Overview and audience-specific navigation
  - `docs/enterprise/compliance-governance.md` - Audit trails, data sovereignty, SOC2/ISO/GDPR
  - `docs/enterprise/productivity-roi.md` - Team benefits, cost analysis, multi-tool flexibility
  - `docs/enterprise/developer-experience.md` - Privacy-first design, power user features
  - `docs/enterprise/research-validation.md` - Letta benchmark (74%), academic foundations
  - `docs/enterprise/deployment-guide.md` - Installation, backup, team sharing patterns
- **[Community Package]**: Resources for Memory Bank users and community
  - `docs/community/README.md` - Community hub and navigation
  - `docs/community/quickstart-memory-bank.md` - 5-minute setup for Memory Bank users
  - `docs/community/migration-from-memory-bank.md` - Complete migration walkthrough
  - `docs/community/mnemonic-vs-memory-bank.md` - Side-by-side feature comparison
  - `docs/community/adoption-stories.md` - Community experiences template
  - `docs/community/CONTRIBUTING-COMMUNITY.md` - How to contribute stories
- **[Integration Guides]**: Enhanced Cursor, Windsurf, GitHub Copilot guides
  - Common workflows and daily development patterns
  - Advanced configuration patterns
  - Memory Bank migration sections
  - Troubleshooting guides

## [1.0.0] - 2026-01-24

### Added

- Initial release of Mnemonic memory system
- **Commands**:
  - `/mnemonic:setup` - Configure mnemonic with proactive behavior
  - `/mnemonic:init` - Initialize directory structure
  - `/mnemonic:capture` - Capture a new memory
  - `/mnemonic:recall` - Search and recall memories
  - `/mnemonic:search` - Full-text search
  - `/mnemonic:status` - Show system status
  - `/mnemonic:gc` - Garbage collect expired memories
- **Skills**:
  - `mnemonic-core` - Complete memory operations
  - `mnemonic-setup` - CLAUDE.md configuration
  - `mnemonic-search` - Advanced search patterns
  - `mnemonic-format` - MIF Level 3 templates
  - `mnemonic-organization` - Namespace management
  - `mnemonic-blackboard` - Cross-session coordination
- **Agents**:
  - `memory-curator` - Autonomous maintenance and curation
- **Hooks**:
  - `SessionStart` - Load relevant memories on session start
  - `UserPromptSubmit` - Detect recall/capture opportunities
  - `PostToolUse` - Capture learnings from tool results
  - `Stop` - Commit changes and summarize session
- MIF Level 3 compliant memory format
- Bi-temporal tracking (valid time vs recorded time)
- Exponential decay model for memory relevance
- Git versioning for all memories
- Cross-session coordination via blackboard
- User-level and project-level memory scopes
- Nine standard namespaces (apis, blockers, context, decisions, learnings, patterns, security, testing, episodic)

### Technical Details

- Pure filesystem-based storage (no external databases)
- Self-contained skills (no library dependencies)
- Standard Unix tools (git, ripgrep, find)
- Python 3.8+ for hook scripts
