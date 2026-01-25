#!/usr/bin/env bash
#
# Functional Test Runner for Mnemonic Plugin
#
# Runs tests that verify actual AI behavior:
# - Memory capture (does Claude create files?)
# - Memory recall (does Claude use existing memories?)
# - Full workflows (capture → recall cycles)
#
# Requirements:
# - Claude CLI installed and authenticated
# - Makes real API calls (costs money)
# - Uses isolated test directories (no pollution of real memories)
#
# Usage:
#   ./run_functional.sh              # Run all functional tests
#   ./run_functional.sh capture      # Run only capture tests
#   ./run_functional.sh recall       # Run only recall tests
#   ./run_functional.sh workflow     # Run only workflow tests
#   ./run_functional.sh --quick      # Run minimal set (1 test per category)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[functional]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[warning]${NC} $*"
}

error() {
    echo -e "${RED}[error]${NC} $*"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check Claude CLI
    if ! command -v claude &>/dev/null; then
        error "Claude CLI not installed"
        echo "Install with: npm install -g @anthropic-ai/claude-cli"
        exit 1
    fi

    # Check authentication (try a simple command)
    if ! claude --version &>/dev/null; then
        error "Claude CLI not working"
        exit 1
    fi

    log "Prerequisites OK"
}

# Run tests
run_tests() {
    local mode="${1:-all}"

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║           Mnemonic Functional Test Suite                     ║"
    echo "║                                                              ║"
    echo "║   Tests REAL AI behavior - makes API calls                   ║"
    echo "║   Uses ISOLATED directories - safe for real memories         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    warn "These tests make real Claude API calls and may incur costs."
    echo ""

    local pytest_args="-v --tb=short"

    case "$mode" in
    capture)
        log "Running capture tests..."
        python3 -m pytest "$SCRIPT_DIR/test_capture.py" $pytest_args
        ;;
    recall)
        log "Running recall tests..."
        python3 -m pytest "$SCRIPT_DIR/test_recall.py" $pytest_args
        ;;
    workflow)
        log "Running workflow tests..."
        python3 -m pytest "$SCRIPT_DIR/test_workflow.py" $pytest_args
        ;;
    quick | --quick)
        log "Running quick functional tests (1 per category)..."
        python3 -m pytest "$SCRIPT_DIR/" $pytest_args \
            -k "test_capture_on_decision_statement or test_recalls_existing_decision or test_capture_then_recall"
        ;;
    all)
        log "Running all functional tests..."
        python3 -m pytest "$SCRIPT_DIR/" $pytest_args
        ;;
    *)
        echo "Usage: $0 [capture|recall|workflow|quick|all]"
        exit 1
        ;;
    esac
}

# Main
main() {
    check_prerequisites

    # Confirm before running (since it costs money)
    if [[ "${SKIP_CONFIRM:-}" != "1" ]]; then
        echo ""
        read -p "Run functional tests? These make API calls. [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 0
        fi
    fi

    run_tests "${1:-all}"
}

main "$@"
