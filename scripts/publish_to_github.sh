#!/usr/bin/env bash
set -euo pipefail
REPO_NAME="${1:-jyotish-lab}"
VISIBILITY="${2:-private}"

command -v gh >/dev/null 2>&1 || { echo "GitHub CLI (gh) is required."; exit 1; }
command -v git >/dev/null 2>&1 || { echo "git is required."; exit 1; }

git init
git add .
git commit -m "Initial Jyotish Lab release"
gh auth status >/dev/null
gh repo create "$REPO_NAME" --"$VISIBILITY" --source . --remote origin --push

echo "Published as $REPO_NAME ($VISIBILITY)."
