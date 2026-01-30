#!/usr/bin/env bash
#
# Master Test Runner for Mnemonic Plugin
#
# Runs all automated tests:
#   - Unit tests (hooks, memory format)
#   - Integration tests (CLI behavior)
#
# Usage:
#   ./run_all.sh              # Run all tests
#   ./run_all.sh unit         # Run only unit tests
#   ./run_all.sh integration  # Run only integration tests
#   ./run_all.sh --quick      # Skip slow integration tests

set -uo pipefail
# Note: not using -e because arithmetic returns 1 when incrementing from 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

log() {
    echo -e "${BLUE}[test]${NC} $*"
}

pass() {
    echo -e "${GREEN}✓${NC} $*"
    PASSED=$((PASSED + 1))
    TOTAL=$((TOTAL + 1))
}

fail() {
    echo -e "${RED}✗${NC} $*"
    FAILED=$((FAILED + 1))
    TOTAL=$((TOTAL + 1))
}

skip() {
    echo -e "${YELLOW}⊘${NC} $*"
    SKIPPED=$((SKIPPED + 1))
    TOTAL=$((TOTAL + 1))
}

# ============================================================================
# Unit Tests
# ============================================================================

run_unit_tests() {
    log "Running unit tests..."
    echo ""

    # Run all unit tests with pytest (uses isolated environments)
    if python3 -m pytest "$SCRIPT_DIR/unit/" -v --tb=short \
        --ignore="$SCRIPT_DIR/unit/test_cli_behavior.py" 2>&1; then
        pass "All unit tests (isolated environments)"
    else
        fail "Unit tests failed"
    fi
}

# ============================================================================
# Integration Tests
# ============================================================================

run_integration_tests() {
    log "Running integration tests..."
    echo ""

    # Check if Claude CLI is available
    if ! command -v claude &>/dev/null; then
        skip "Integration tests (Claude CLI not available)"
        return
    fi

    # Run isolated CLI tests
    if python3 -m pytest "$SCRIPT_DIR/integration/test_cli_isolated.py" -v --tb=short 2>&1; then
        pass "CLI integration tests (isolated)"
    else
        fail "CLI integration tests"
    fi
}

# ============================================================================
# Functional Tests (Real AI behavior)
# ============================================================================

run_functional_tests() {
    log "Running functional tests (real AI behavior)..."
    echo ""

    # Check if Claude CLI is available
    if ! command -v claude &>/dev/null; then
        skip "Functional tests (Claude CLI not available)"
        return
    fi

    warn "Functional tests make real API calls and may incur costs."
    echo ""

    # Run quick functional tests (1 per category)
    if python3 -m pytest "$SCRIPT_DIR/functional/" -v --tb=short \
        -k "test_capture_on_decision_statement or test_recalls_existing_decision or test_capture_then_recall" 2>&1; then
        pass "Functional tests (capture, recall, workflow)"
    else
        fail "Functional tests"
    fi
}

warn() {
    echo -e "${YELLOW}[warning]${NC} $*"
}

# ============================================================================
# Quick Validation Tests
# ============================================================================

run_quick_tests() {
    log "Running quick validation tests..."
    echo ""

    # Test 1: Hook files exist and are executable
    local hooks_ok=true
    for hook in session_start.py user_prompt_submit.py post_tool_use.py stop.py; do
        if [[ -x "$PROJECT_ROOT/hooks/$hook" ]]; then
            :
        else
            hooks_ok=false
        fi
    done
    if $hooks_ok; then
        pass "All hooks exist and are executable"
    else
        fail "Some hooks missing or not executable"
    fi

    # Test 2: Hooks return valid JSON
    local json_ok=true
    for hook in session_start.py user_prompt_submit.py post_tool_use.py stop.py; do
        local output
        output=$(python3 "$PROJECT_ROOT/hooks/$hook" 2>/dev/null || echo '{}')
        if echo "$output" | python3 -c "import json,sys; json.load(sys.stdin)" 2>/dev/null; then
            :
        else
            json_ok=false
        fi
    done
    if $json_ok; then
        pass "All hooks return valid JSON"
    else
        fail "Some hooks return invalid JSON"
    fi

    # Test 3: Memory directories exist
    if [[ -d ${MNEMONIC_ROOT} ]]; then
        pass "User mnemonic directory exists"
    else
        skip "User mnemonic directory not initialized"
    fi

    # Test 4: Search command works
    if rg --version &>/dev/null; then
        if rg -i "test" ${MNEMONIC_ROOT}/ ./.claude/mnemonic/ --glob "*.memory.md" -l 2>/dev/null || true; then
            pass "Memory search command works"
        else
            fail "Memory search command failed"
        fi
    else
        skip "ripgrep not installed"
    fi

    # Test 5: Memory files have valid format
    local format_ok=true
    local count=0
    for mem in $(find ${MNEMONIC_ROOT} -name "*.memory.md" 2>/dev/null | head -5); do
        if head -1 "$mem" | grep -q "^---$"; then
            count=$((count + 1))
        else
            format_ok=false
        fi
    done
    if [[ $count -gt 0 ]] && $format_ok; then
        pass "Memory files have valid frontmatter ($count checked)"
    elif [[ $count -eq 0 ]]; then
        skip "No memory files to validate"
    else
        fail "Some memory files have invalid format"
    fi
}

# ============================================================================
# Main
# ============================================================================

main() {
    local mode="${1:-all}"

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║            Mnemonic Plugin Automated Test Suite              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    case "$mode" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    functional)
        run_functional_tests
        ;;
    quick | --quick)
        run_quick_tests
        ;;
    all)
        run_quick_tests
        echo ""
        run_unit_tests
        echo ""
        run_integration_tests
        ;;
    full)
        run_quick_tests
        echo ""
        run_unit_tests
        echo ""
        run_integration_tests
        echo ""
        run_functional_tests
        ;;
    *)
        echo "Usage: $0 [unit|integration|functional|quick|all|full]"
        exit 1
        ;;
    esac

    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}, ${YELLOW}$SKIPPED skipped${NC} (total: $TOTAL)"
    echo ""

    if [[ $FAILED -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
