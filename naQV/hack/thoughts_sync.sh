#!/bin/bash
set -e

# thoughts_sync.sh - Sync thoughts directory with git and create searchable index
# Usage: ./hack/thoughts_sync.sh [commit-message]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
THOUGHTS_DIR="$REPO_ROOT/thoughts"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if thoughts directory exists
if [ ! -d "$THOUGHTS_DIR" ]; then
    echo -e "${YELLOW}Warning: thoughts/ directory not found${NC}"
    exit 0
fi

# Function to create searchable directory with hard links
create_searchable() {
    local searchable_dir="$THOUGHTS_DIR/searchable"

    # Remove old searchable directory
    if [ -d "$searchable_dir" ]; then
        chmod -R 755 "$searchable_dir" 2>/dev/null || true
        rm -rf "$searchable_dir"
    fi

    mkdir -p "$searchable_dir"

    local count=0

    # Find all files (following symlinks) and create hard links
    while IFS= read -r -d '' file; do
        # Skip hidden files and CLAUDE.md
        local basename=$(basename "$file")
        if [[ "$basename" == .* ]] || [[ "$basename" == "CLAUDE.md" ]]; then
            continue
        fi

        # Get relative path from thoughts directory
        local rel_path="${file#$THOUGHTS_DIR/}"

        # Skip if already in searchable
        if [[ "$rel_path" == searchable/* ]]; then
            continue
        fi

        # Create target directory
        local target_dir="$searchable_dir/$(dirname "$rel_path")"
        mkdir -p "$target_dir"

        # Resolve symlinks and create hard link
        local real_file=$(realpath "$file" 2>/dev/null) || continue
        if [ -f "$real_file" ]; then
            ln "$real_file" "$searchable_dir/$rel_path" 2>/dev/null && ((count++)) || true
        fi
    done < <(find -L "$THOUGHTS_DIR" -type f -print0 2>/dev/null)

    echo -e "${GREEN}Created $count hard links in searchable directory${NC}"
}

# Function to sync with git
sync_git() {
    local commit_msg="${1:-Sync thoughts - $(date -Iseconds)}"

    cd "$THOUGHTS_DIR"

    # Check if it's a git repo
    if [ ! -d ".git" ]; then
        echo -e "${YELLOW}thoughts/ is not a git repository, skipping git sync${NC}"
        return 0
    fi

    # Stage all changes
    git add -A

    # Check if there are changes to commit
    if git diff-index --quiet HEAD 2>/dev/null; then
        echo "No changes to commit"
    else
        git commit -m "$commit_msg"
        echo -e "${GREEN}Changes committed${NC}"
    fi

    # Pull with rebase
    if git remote get-url origin &>/dev/null; then
        echo "Pulling changes..."
        if ! git pull --rebase 2>&1; then
            echo -e "${YELLOW}Warning: Pull failed. You may need to resolve conflicts manually.${NC}"
        fi

        # Push
        echo "Pushing changes..."
        if ! git push 2>&1; then
            echo -e "${YELLOW}Warning: Push failed. You may need to push manually.${NC}"
        else
            echo -e "${GREEN}Changes pushed${NC}"
        fi
    else
        echo "No remote configured, skipping push"
    fi
}

# Main
echo "Syncing thoughts directory..."
create_searchable
sync_git "$1"
echo -e "${GREEN}Thoughts sync complete${NC}"
