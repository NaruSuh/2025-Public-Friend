#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/run_silent.sh"

print_main_header "Setting up repository"

# CI environment detection
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
    IS_CI=true
else
    IS_CI=false
fi

# Install CI tools if needed
if [ "$IS_CI" = true ]; then
    print_header "CI" "Installing CI tools"

    # Claude Code CLI
    if ! command_exists claude; then
        run_silent "Installing Claude Code CLI" "npm install -g @anthropic-ai/claude-code"
    fi

    # golangci-lint for Go projects
    if ! command_exists golangci-lint; then
        run_silent "Installing golangci-lint" "go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest"
    fi
fi

# Project-specific setup
print_header "Setup" "Setting up project"

# Add your project-specific setup here
# Example for Go:
# run_silent "Installing Go dependencies" "go mod download"

# Example for TypeScript:
# run_silent "Installing npm dependencies" "npm install"

print_main_header "Setup complete"
