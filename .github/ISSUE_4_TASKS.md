# Issue #4: QMD Semantic Search - Task Breakdown

## Sub-Tasks

### Setup & Infrastructure
- [ ] #4.1: Add qmd availability detection to `lib/search.py`
- [ ] #4.2: Implement auto-routing heuristic (ripgrep vs qmd)
- [ ] #4.3: Add qmd BM25 search function
- [ ] #4.4: Add qmd semantic search function  
- [ ] #4.5: Add qmd hybrid search function

### Commands
- [ ] #4.6: Create `/mnemonic:qmd-setup` command
- [ ] #4.7: Create `/mnemonic:reindex` command

### Integration
- [ ] #4.8: Update `/mnemonic:search` command with semantic support
- [ ] #4.9: Update post-capture hook for incremental indexing
- [ ] #4.10: Update session hooks (start/stop) for index management

### Skills & Documentation
- [ ] #4.11: Update `mnemonic-search` skill with semantic examples
- [ ] #4.12: Update `mnemonic-search-enhanced` skill
- [ ] #4.13: Update README with qmd setup instructions
- [ ] #4.14: Create semantic search documentation

### Testing
- [ ] #4.15: Add unit tests for qmd integration
- [ ] #4.16: Add integration tests
- [ ] #4.17: Manual end-to-end testing

## Dependencies
- Node.js ≥ 22 or Bun ≥ 1.0.0
- @tobilu/qmd npm package
- ~2GB disk space for models

## Success Criteria
- Semantic search works end-to-end
- Auto-routing chooses correct backend
- Graceful fallback without qmd
- All tests pass
