#!/bin/bash
set -e

# Simple git worktree creation script
# Usage: ./hack/create_worktree.sh <branch-name>

if [ -z "$1" ]; then
    echo "Usage: $0 <branch-name>"
    exit 1
fi

BRANCH_NAME="$1"
WORKTREE_DIR="../$(basename $(pwd))-$BRANCH_NAME"

echo "Creating worktree at $WORKTREE_DIR for branch $BRANCH_NAME"

git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" 2>/dev/null || \
git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"

echo "Worktree created at $WORKTREE_DIR"
echo "cd $WORKTREE_DIR to start working"
