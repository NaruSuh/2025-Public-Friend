#!/bin/bash
set -e

# fetch_ticket.sh - Fetch GitHub issue and create local ticket file
# Usage: ./hack/fetch_ticket.sh <issue-number>
#
# Creates: thoughts/shared/tickets/GH-<number>.md

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TICKETS_DIR="$REPO_ROOT/thoughts/shared/tickets"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <issue-number>"
    echo "Example: $0 123"
    exit 1
fi

ISSUE_NUMBER="$1"
TICKET_FILE="$TICKETS_DIR/GH-$ISSUE_NUMBER.md"

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed${NC}"
    echo "Install with: brew install gh"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not authenticated with GitHub CLI${NC}"
    echo "Run: gh auth login"
    exit 1
fi

# Create tickets directory if it doesn't exist
mkdir -p "$TICKETS_DIR"

# Check if ticket file already exists
if [ -f "$TICKET_FILE" ]; then
    echo -e "${YELLOW}Warning: $TICKET_FILE already exists${NC}"
    read -p "Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

echo "Fetching issue #$ISSUE_NUMBER..."

# Fetch issue data
ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --json title,body,url,labels,state,author,createdAt 2>&1) || {
    echo -e "${RED}Error: Failed to fetch issue #$ISSUE_NUMBER${NC}"
    echo "$ISSUE_JSON"
    exit 1
}

# Extract fields using jq
TITLE=$(echo "$ISSUE_JSON" | jq -r '.title')
BODY=$(echo "$ISSUE_JSON" | jq -r '.body // "No description provided."')
URL=$(echo "$ISSUE_JSON" | jq -r '.url')
LABELS=$(echo "$ISSUE_JSON" | jq -r '.labels | map(.name) | join(", ") | if . == "" then "None" else . end')
STATE=$(echo "$ISSUE_JSON" | jq -r '.state')
AUTHOR=$(echo "$ISSUE_JSON" | jq -r '.author.login')
CREATED=$(echo "$ISSUE_JSON" | jq -r '.createdAt | split("T")[0]')

# Create ticket file
cat > "$TICKET_FILE" << EOF
# GH-$ISSUE_NUMBER: $TITLE

## GitHub Link
$URL

## Metadata
- **Author**: $AUTHOR
- **Created**: $CREATED
- **Labels**: $LABELS
- **Status**: $STATE

## Description

$BODY

## Planning Notes

<!-- Add implementation notes here -->

## Acceptance Criteria

<!-- Define what "done" looks like -->
- [ ]

## Implementation Status

- [ ] Research completed
- [ ] Plan created
- [ ] Implementation done
- [ ] Validation passed
EOF

echo -e "${GREEN}Created: $TICKET_FILE${NC}"

# Sync thoughts directory
echo "Syncing thoughts directory..."
"$SCRIPT_DIR/thoughts_sync.sh" > /dev/null 2>&1 || true

echo -e "${GREEN}Done!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review: $TICKET_FILE"
echo "  2. Plan:   /create_plan thoughts/shared/tickets/GH-$ISSUE_NUMBER.md"
