---
allowed-tools:
- Bash
description: Re-index mnemonic memories for qmd semantic search. Run after capturing new memories or bulk imports.
name: qmd-reindex
user-invocable: true
---

# QMD Re-index Skill

Re-index mnemonic memories for qmd search.

## Usage

```bash
qmd update && qmd embed
```

- `qmd update` — rebuilds the BM25 full-text index
- `qmd embed` — regenerates vector embeddings for semantic search

## Options

```bash
# Index only (skip embeddings — faster)
qmd update

# Specific collection only
qmd update -c mnemonic-zircote && qmd embed -c mnemonic-zircote

# Check status after
qmd status
```

## When to Re-index

- After `/mnemonic:capture` sessions
- After bulk memory imports
- After editing memory files directly
- Periodically if memories are added by hooks

Indexing is **not** automatic. Searches will miss memories added since the last index.
