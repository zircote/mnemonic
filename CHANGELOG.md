# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- Memory linking and relationships
- Semantic search with embeddings
- Export/import functionality
- Web UI for memory browsing

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
