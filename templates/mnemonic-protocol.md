<!-- BEGIN MNEMONIC PROTOCOL -->
## Memory Operations

You have PERSISTENT MEMORY across sessions.

BEFORE starting any task:
```bash
if [ -d ~/.claude/mnemonic ]; then
    rg -i "{relevant_keywords}" ~/.claude/mnemonic/ --glob "*.memory.md" -l | head -5
fi
```
If results exist, READ the most relevant and apply that context.

AFTER completing work, if you discovered:
- A decision → report for capture to _semantic/decisions
- A pattern → report for capture to _procedural/patterns
- A learning → report for capture to _semantic/knowledge
<!-- END MNEMONIC PROTOCOL -->
