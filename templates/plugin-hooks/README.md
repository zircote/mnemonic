# Plugin Hooks Templates

Templates for integrating mnemonic memory operations into other Claude Code plugins.

## Files

### `mnemonic-suggest.py`

A template Python hook that detects file creation events and suggests mnemonic memory capture.

**To use:**

1. Copy to target plugin's `hooks/` directory
2. Customize the `PLUGIN_PATTERNS` dict for your plugin's file patterns
3. Update `PLUGIN_NAME` constant
4. Create or update `hooks.json` to include this hook

### `hooks.json.template`

Example hooks.json configuration that triggers the mnemonic-suggest hook on Write tool use.

**To use:**

1. Copy as `hooks.json` to target plugin's `hooks/` directory
2. Merge with existing hooks.json if one exists

## How It Works

1. Claude uses the Write tool to create a file
2. PostToolUse hook runs `mnemonic-suggest.py`
3. Hook checks if file path matches any plugin patterns
4. If match found, injects `additionalContext` suggesting memory capture
5. Claude sees suggestion and captures memory with full conversation context

## Customization

The `PLUGIN_PATTERNS` dict maps regex patterns to capture configurations:

```python
PLUGIN_PATTERNS = {
    r"/adr/.*\.md$": {
        "event": "ADR created",
        "namespace": "decisions",
        "capture_hint": "Capture decision rationale...",
        "tags": ["architecture", "adr"],
    },
}
```

**Fields:**
- `event`: Human-readable description of what happened
- `namespace`: Target mnemonic namespace (decisions, learnings, patterns, etc.)
- `capture_hint`: Guidance for Claude on what to capture
- `tags`: Suggested tags for the memory

## Integration with `/mnemonic:plugin-integration`

The plugin-integration skill can automatically set up these templates for a target plugin.

```bash
/mnemonic:plugin-integration ~/.claude/plugins/cache/your-org/your-plugin/
```

This will:
1. Analyze the plugin structure
2. Copy and customize these templates
3. Add workflow sections to command/skill markdown files
