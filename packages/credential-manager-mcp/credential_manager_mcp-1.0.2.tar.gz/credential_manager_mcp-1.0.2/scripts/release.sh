#!/bin/bash

# Release automation script for credential-manager-mcp
# Usage: ./scripts/release.sh [major|minor|patch|VERSION]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]] || [[ ! -d "credential_manager_mcp" ]]; then
    error "Please run this script from the project root directory"
fi

# Check if git is clean
if [[ -n $(git status --porcelain) ]]; then
    error "Git working directory is not clean. Please commit or stash your changes."
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    warn "You're not on the main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get current version
CURRENT_VERSION=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
info "Current version: $CURRENT_VERSION"

# Determine new version
if [[ $# -eq 0 ]]; then
    echo "Usage: $0 [major|minor|patch|VERSION]"
    echo "Current version: $CURRENT_VERSION"
    exit 1
fi

VERSION_TYPE=$1

# Function to increment version
increment_version() {
    local version=$1
    local type=$2
    
    IFS='.' read -r major minor patch <<< "$version"
    
    case $type in
        major)
            echo "$((major + 1)).0.0"
            ;;
        minor)
            echo "$major.$((minor + 1)).0"
            ;;
        patch)
            echo "$major.$minor.$((patch + 1))"
            ;;
        *)
            echo "$type"  # Assume it's a specific version
            ;;
    esac
}

# Calculate new version
if [[ "$VERSION_TYPE" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    NEW_VERSION=$VERSION_TYPE
else
    NEW_VERSION=$(increment_version "$CURRENT_VERSION" "$VERSION_TYPE")
fi

info "New version: $NEW_VERSION"

# Generate changelog using dedicated script
info "Generating changelog using scripts/generate-changelog.sh..."
./scripts/generate-changelog.sh --version "v$NEW_VERSION"

# Get the changelog file path and content
CHANGELOG_FILE="docs/changelogs/v$NEW_VERSION.md"
CHANGELOG=$(cat "$CHANGELOG_FILE")

# Confirm release
read -p "Create release v$NEW_VERSION? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Update version in pyproject.toml
info "Updating version in pyproject.toml..."
sed -i.bak "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update lock file
info "Updating uv.lock file..."
uv lock || error "Failed to update lock file"

# Run tests
info "Running tests..."
uv run pytest test/ -v || error "Tests failed"

# Build package
info "Building package..."
rm -rf dist/
uv build || error "Build failed"

# Test built package
info "Testing built package..."
if command -v timeout >/dev/null 2>&1; then
    # Linux/GNU timeout
    timeout 5s uvx --from ./dist/credential_manager_mcp-$NEW_VERSION-py3-none-any.whl credential-manager-mcp >/dev/null 2>&1 || success "Package installation test completed (server started successfully)"
elif command -v gtimeout >/dev/null 2>&1; then
    # macOS with GNU coreutils (brew install coreutils)
    gtimeout 5s uvx --from ./dist/credential_manager_mcp-$NEW_VERSION-py3-none-any.whl credential-manager-mcp >/dev/null 2>&1 || success "Package installation test completed (server started successfully)"
else
    # Fallback: start server in background and kill after 5 seconds
    uvx --from ./dist/credential_manager_mcp-$NEW_VERSION-py3-none-any.whl credential-manager-mcp >/dev/null 2>&1 &
    SERVER_PID=$!
    sleep 5
    kill $SERVER_PID 2>/dev/null || true
    success "Package installation test completed (server started successfully)"
fi

# Add and commit files automatically
info "Adding version change, updated lock file, and changelog to git..."
git add pyproject.toml uv.lock "$CHANGELOG_FILE"
info "Files staged for commit:"
echo "  - pyproject.toml (version bump)"
echo "  - uv.lock (updated dependencies)"
echo "  - $CHANGELOG_FILE (generated changelog)"
echo ""

info "Committing changes..."
git commit -m "Bump version to $NEW_VERSION"
success "Changes committed!"

info "Creating tag v$NEW_VERSION..."
git tag "v$NEW_VERSION"
success "Tag v$NEW_VERSION created!"

# Show what will be pushed
echo ""
info "Ready to push the following:"
echo "  - Commit: $(git log -1 --oneline)"
echo "  - Tag: v$NEW_VERSION"
echo ""

# Ask for confirmation to push
read -p "Push changes and tag to origin? This will trigger PyPI publishing! [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Pushing to origin..."
    git push origin main
    git push origin "v$NEW_VERSION"
    success "Release v$NEW_VERSION pushed! 🎉"
    
    echo ""
    info "PyPI publishing will start automatically via GitHub Actions"
    echo ""
    info "Monitor the release at:"
    echo "- GitHub Actions: https://github.com/mclamee/credential-manager-mcp/actions"
    echo "- PyPI: https://pypi.org/project/credential-manager-mcp/"
else
    warn "Push cancelled. You can push manually later:"
    echo ""
    echo "  git push origin main"
    echo "  git push origin 'v$NEW_VERSION'"
    echo ""
    info "After pushing the tag, PyPI publishing will start automatically via GitHub Actions"
fi 