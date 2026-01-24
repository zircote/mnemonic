# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### Planned

- Memory linking and relationships
- Semantic search with embeddings
- Memory compression for old entries
- Export/import functionality
- Web UI for memory browsing
