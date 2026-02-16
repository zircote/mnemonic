#!/usr/bin/env bash
# qmd-setup.sh — Bootstrap @tobilu/qmd semantic search for mnemonic memories
# Usage: bash tools/qmd-setup.sh
set -euo pipefail

###############################################################################
# Helpers
###############################################################################

info() { printf '\033[1;34m[info]\033[0m  %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m  %s\n' "$*"; }
err() { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; }
die() {
    err "$*"
    exit 1
}

###############################################################################
# Prerequisite checks
###############################################################################

info "Checking prerequisites…"

# Node.js >= 22
if ! command -v node &>/dev/null; then
    die "Node.js is not installed. Install Node.js >= 22 and try again."
fi

NODE_MAJOR=$(node -e 'process.stdout.write(String(process.versions.node.split(".")[0]))')
if ((NODE_MAJOR < 22)); then
    die "Node.js >= 22 required (found v${NODE_MAJOR}). Upgrade and try again."
fi
info "Node.js v$(node --version | tr -d v) ✓"

# qmd CLI
if ! command -v qmd &>/dev/null; then
    die "qmd CLI not found. Install with: npm i -g @tobilu/qmd"
fi
info "qmd $(qmd --version 2>/dev/null || echo '(version unknown)') ✓"

###############################################################################
# Resolve MNEMONIC_ROOT
###############################################################################

CONFIG_FILE="$HOME/.config/mnemonic/config.json"
if [[ -f "$CONFIG_FILE" ]]; then
    RAW_PATH=$(node -e "
const fs = require('fs');
const os = require('os');
const cfg = JSON.parse(fs.readFileSync('$CONFIG_FILE', 'utf8'));
const p = cfg.memory_store_path || '~/.local/share/mnemonic';
console.log(p.replace(/^~/, os.homedir()));
")
    MNEMONIC_ROOT="$RAW_PATH"
else
    MNEMONIC_ROOT="$HOME/.local/share/mnemonic"
fi

if [[ ! -d "$MNEMONIC_ROOT" ]]; then
    die "MNEMONIC_ROOT does not exist: $MNEMONIC_ROOT"
fi
info "MNEMONIC_ROOT=$MNEMONIC_ROOT"

###############################################################################
# Discover memory roots and register collections
###############################################################################

COLLECTIONS_ADDED=0

register_collection() {
    local path="$1" name="$2"
    if [[ ! -d "$path" ]]; then
        warn "Skipping $name — directory not found: $path"
        return
    fi
    info "Registering collection: $name → $path"
    qmd collection add "$path" --name "$name"
    ((COLLECTIONS_ADDED++)) || true
}

# Org directories: {MNEMONIC_ROOT}/{org}/ (skip 'default')
for dir in "$MNEMONIC_ROOT"/*/; do
    [[ -d "$dir" ]] || continue
    org=$(basename "$dir")
    [[ "$org" == "default" ]] && continue
    [[ "$org" == ".blackboard" ]] && continue
    register_collection "$dir" "mnemonic-${org}"
done

# Default directory
if [[ -d "$MNEMONIC_ROOT/default" ]]; then
    register_collection "$MNEMONIC_ROOT/default" "mnemonic-default"
fi

# Project-level memories (resolve from git root if available)
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
if [[ -n "$PROJECT_ROOT" && -d "$PROJECT_ROOT/.claude/mnemonic" ]]; then
    register_collection "$PROJECT_ROOT/.claude/mnemonic" "mnemonic-project"
elif [[ -d ".claude/mnemonic" ]]; then
    warn "Not in a git repo; checking .claude/mnemonic relative to cwd."
    register_collection "$(pwd)/.claude/mnemonic" "mnemonic-project"
fi

if ((COLLECTIONS_ADDED == 0)); then
    die "No memory directories found to register."
fi

info "$COLLECTIONS_ADDED collection(s) registered."

###############################################################################
# Index and embed
###############################################################################

info "Indexing and embedding all configured qmd collections…"
info "Note: if you have other qmd collections, they will also be updated."
info "To limit scope, run: qmd update -c <name> && qmd embed -c <name>"

info "Indexing files (qmd update)…"
qmd update

info "Generating embeddings (qmd embed)…"
info "Note: first run downloads ~2 GB of GGUF models."
qmd embed

###############################################################################
# Validate
###############################################################################

info "Validating with qmd status…"
qmd status

info "Running test search…"
qmd search "mnemonic" -n 3 || warn "Test search returned no results (index may be empty)."

info "Done. qmd is ready for semantic search over mnemonic memories."
info ""
info "Quick start:"
info "  qmd search \"auth\"               # BM25 keyword search"
info "  qmd vsearch \"auth patterns\"     # vector/semantic search"
info "  qmd query \"auth patterns\"       # hybrid (BM25 + vector)"
info "  qmd search \"auth\" -c mnemonic-zircote  # scope to org"
