#!/usr/bin/env bash
# ==============================================================================
# Universal DevSkill CI Quality Gate Scan (scripts/ci-gate.sh)
# Enforces: R-001 (TODOs), R-002 (Mock data), R-034 (any/type-ignore),
#           R-046 (swallowed errors), R-064 (Secrets), R-142 (console.log)
# Usage:
#   ./scripts/ci-gate.sh            # Scan tracked files in repository
#   ./scripts/ci-gate.sh --staged   # Scan only staged git diff (pre-commit)
# ==============================================================================
set -euo pipefail

MODE="repo"
if [[ "${1:-}" == "--staged" ]]; then
    MODE="staged"
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ci-gate: ERROR — must be executed inside a git work tree (fail-closed per R-232)." >&2
    exit 2
fi

SCAN_FAILED=0
EXCLUDE_PATHS=(
    ':!tests'
    ':!**/tests/**'
    ':!**/__tests__/**'
    ':!**/__mocks__/**'
    ':!*.test.*'
    ':!*.spec.*'
    ':!**/test_*.py'
    ':!*_test.go'
    ':!*.md'
    ':!docs'
    ':!scripts/ci-gate.sh'
)

run_grep() {
    local pattern="$1"
    shift
    if [[ "$MODE" == "staged" ]]; then
        git grep -EIn --cached -e "$pattern" -- "$@"
    else
        git grep -EIn -e "$pattern" -- "$@"
    fi
}

echo "==> Running DevSkill CI Quality Gate Scan (mode: ${MODE})..."

# [1/6] R-001: Forbidden deferred-work markers in production code
echo "[1/6] Scanning for TODO / FIXME / HACK / TBD markers (R-001)..."
if run_grep "(TODO|FIXME|HACK|XXX|TBD):" "${EXCLUDE_PATHS[@]}"; then
    echo "FAIL [R-001]: Found forbidden deferred-work markers in production files." >&2
    SCAN_FAILED=1
else
    echo "PASS [R-001]: No unresolved markers found."
fi

# [2/6] R-002: Mock / placeholder data in production code
echo "[2/6] Scanning for mock data in production paths (R-002)..."
if run_grep "(mockUser|fakeData|test@example\.com|dummyPassword|mockPayload)" "${EXCLUDE_PATHS[@]}"; then
    echo "FAIL [R-002]: Found mock or dummy data in production files." >&2
    SCAN_FAILED=1
else
    echo "PASS [R-002]: No mock data leaks found."
fi

# [3/6] R-142: Raw console.log/debug in production code
echo "[3/6] Scanning for raw console.log/debug statements (R-142)..."
if run_grep "console\.(log|debug)\(" "${EXCLUDE_PATHS[@]}" ':!scripts'; then
    echo "FAIL [R-142]: Found raw console.log/debug statements in production code." >&2
    SCAN_FAILED=1
else
    echo "PASS [R-142]: No unapproved console.log statements found."
fi

# [4/6] R-034: Type bypasses (any / @ts-ignore / # type: ignore)
echo "[4/6] Scanning for forbidden type bypasses (R-034)..."
if run_grep "(:[[:space:]]*any\b|\bas[[:space:]]+any\b|@ts-ignore|@ts-nocheck|# type:[[:space:]]*ignore)" "${EXCLUDE_PATHS[@]}"; then
    echo "FAIL [R-034]: Found forbidden type bypass directives in source code." >&2
    SCAN_FAILED=1
else
    echo "PASS [R-034]: Type system integrity intact."
fi

# [5/6] R-046: Swallowed exceptions (empty catch or bare except: pass)
echo "[5/6] Scanning for swallowed errors (R-046)..."
if run_grep "(catch[[:space:]]*\([^)]*\)[[:space:]]*\{[[:space:]]*\}|except[[:space:]]*:[[:space:]]*pass)" "${EXCLUDE_PATHS[@]}"; then
    echo "FAIL [R-046]: Found empty catch or bare 'except: pass' swallowing errors." >&2
    SCAN_FAILED=1
else
    echo "PASS [R-046]: Error handling integrity verified."
fi

# [6/6] R-064: Hardcoded secret signatures
echo "[6/6] Scanning for hardcoded API keys and private keys (R-064)..."
SECRET_PATTERN="(AKIA[0-9A-Z]{16}|ghp_[0-9a-zA-Z]{36}|github_pat_[0-9a-zA-Z_]{22,}|sk_live_[0-9a-zA-Z]{24}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|EC|OPENSSH|DSA|PGP) PRIVATE KEY-----)"
if run_grep "$SECRET_PATTERN" ':!*.md' ':!scripts/ci-gate.sh'; then
    echo "FAIL [R-064]: Detected potential hardcoded secret or private key." >&2
    SCAN_FAILED=1
else
    echo "PASS [R-064]: Secret scan passed clean."
fi

if [[ "$SCAN_FAILED" -ne 0 ]]; then
    echo "DevSkill CI Gate Scan FAILED. Resolve violations before committing or merging." >&2
    exit 1
fi

echo "All DevSkill CI Gate checks passed."
exit 0
