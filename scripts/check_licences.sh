#!/usr/bin/env bash
# Check that no copyleft licence exists in the runtime dependency tree.
# Exits non-zero if AGPL, GPL, or SSPL is found.

set -euo pipefail

echo "Checking runtime dependency licences..."

FORBIDDEN=$(uv run pip-licenses \
    --from=mixed \
    --format=csv \
    --with-system \
    | grep -iE "AGPL|GNU General Public|SSPL|Server Side Public" \
    | grep -v "^Name" \
    || true)

if [ -n "$FORBIDDEN" ]; then
    echo "ERROR: Copyleft licence found in runtime dependencies:"
    echo "$FORBIDDEN"
    echo ""
    echo "This violates the constitution. See docs/adr/0002-parser-stack.md."
    exit 1
fi

echo "OK: No copyleft licences in runtime tree."
