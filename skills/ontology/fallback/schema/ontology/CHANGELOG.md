# Ontology Schema Changelog

All notable changes to the ontology schema are documented in this file.

## [v2] - 2026-01-27

### Added
- `content_patterns` array for base ontology namespace suggestion
- `file_patterns` array for file-based namespace suggestion
- `contentPattern` definition for content matching
- `filePattern` definition with namespaces array and context field

### Changed
- Made `suggest_entity` optional in `discoveryPattern` (was required)
- Updated namespace path examples to use underscore prefix (`_semantic/decisions`)

## [v1] - 2026-01-26

### Added
- Initial cognitive triad namespace hierarchy
- Entity type definitions with base types (semantic, episodic, procedural)
- Trait/mixin system
- Relationship definitions
- Discovery pattern support for entity suggestion
