#!/bin/bash
# Quick release script for aluna-cli
# Usage: ./release.sh [major|minor|patch]

set -e  # Exit on error

VERSION_BUMP=${1:-patch}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$SCRIPT_DIR"

echo "🚀 Starting aluna-cli release process..."

# Run the Python build and release script
uv run python build_and_release.py "$VERSION_BUMP"