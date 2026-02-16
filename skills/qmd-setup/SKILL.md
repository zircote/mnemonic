---
allowed-tools:
- Bash
- Read
- Write
description: >
  Set up @tobilu/qmd semantic search for mnemonic memories. Registers collections,
  builds indexes, and generates embeddings. Run this once per machine.
name: qmd-setup
user-invocable: true
---

# QMD Setup Skill

Bootstrap `@tobilu/qmd` for semantic search over mnemonic memories.

## Prerequisites

- **Node.js >= 22** — `node --version`
- **qmd CLI** — `npm i -g @tobilu/qmd`

## Automated Setup

Run the setup script:

```bash
bash tools/qmd-setup.sh
```

The script will:
1. Check prerequisites (Node.js >= 22, qmd installed)
2. Resolve `MNEMONIC_ROOT` from `~/.config/mnemonic/config.json`
3. Discover memory roots dynamically:
   - `{MNEMONIC_ROOT}/{org}/` → collection `mnemonic-{org}`
   - `{MNEMONIC_ROOT}/default/` → collection `mnemonic-default`
   - `.claude/mnemonic/` → collection `mnemonic-project`
4. Run `qmd update` (index) + `qmd embed` (embeddings)
5. Validate with `qmd status` and a test search

> **Note:** First `qmd embed` downloads ~2 GB of GGUF models.

## Manual Setup

If you prefer to set up manually:

`MNEMONIC_ROOT` is resolved from `~/.config/mnemonic/config.json` (defaults to
`~/.local/share/mnemonic`). Adjust the paths below to match your config:

```bash
# 1. Register collections (replace paths with your MNEMONIC_ROOT)
qmd collection add "${MNEMONIC_ROOT:-$HOME/.local/share/mnemonic}/zircote/" --name mnemonic-zircote
qmd collection add "${MNEMONIC_ROOT:-$HOME/.local/share/mnemonic}/default/" --name mnemonic-default
qmd collection add "$(git rev-parse --show-toplevel)/.claude/mnemonic/" --name mnemonic-project  # if exists

# 2. Build index
qmd update

# 3. Generate embeddings (downloads models on first run)
qmd embed

# 4. Validate
qmd status
qmd search "test" -n 3
```

## After Setup

Use search commands:

| Command | Type | Requires |
|---------|------|----------|
| `qmd search "query"` | BM25 keyword | `qmd update` |
| `qmd vsearch "query"` | Semantic vector | `qmd embed` |
| `qmd query "query"` | Hybrid (BM25 + vector) | Both |

Scope to a specific collection:

```bash
qmd search "auth" -c mnemonic-zircote    # org memories only
qmd search "auth" -c mnemonic-project    # this repo only
qmd search "auth"                        # all collections
```

## Re-indexing

After adding new memories, re-index with `/mnemonic:qmd-reindex` or:

```bash
qmd update && qmd embed
```

Indexing is **not** automatic — run after captures or bulk imports.
