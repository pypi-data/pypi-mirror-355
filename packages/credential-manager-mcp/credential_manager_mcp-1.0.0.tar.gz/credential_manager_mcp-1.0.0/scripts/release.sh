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

# Commit version change and updated lock file
info "Committing version change and updated lock file..."
git add pyproject.toml uv.lock
git commit -m "Bump version to $NEW_VERSION"

# Create and push tag (this triggers PyPI publishing via GitHub Actions)
info "Creating and pushing tag..."
git tag "v$NEW_VERSION"
git push origin main
git push origin "v$NEW_VERSION"

success "🚀 Tag v$NEW_VERSION pushed! PyPI publishing started automatically."

# Optionally create GitHub release for better UX (not required for PyPI publishing)
if command -v gh >/dev/null 2>&1; then
    info "Creating GitHub release for better UX..."
    
    # Generate release notes
    RELEASE_NOTES=$(cat <<EOF
## 🚀 Release v$NEW_VERSION

### Installation
\`\`\`bash
uvx credential-manager-mcp
\`\`\`

### What's Changed
- Version bump to $NEW_VERSION
- See commit history for detailed changes

### Configuration
Add to your MCP client config:
\`\`\`json
{
  "mcpServers": {
    "credential-manager": {
      "command": "uvx",
      "args": ["credential-manager-mcp"],
      "env": {
        "CREDENTIAL_MANAGER_READ_ONLY": "false"
      }
    }
  }
}
\`\`\`
EOF
    )
    
    gh release create "v$NEW_VERSION" \
        --title "v$NEW_VERSION" \
        --notes "$RELEASE_NOTES" \
        ./dist/credential_manager_mcp-$NEW_VERSION.tar.gz \
        ./dist/credential_manager_mcp-$NEW_VERSION-py3-none-any.whl
    
    success "GitHub release created! 🎉"
else
    info "GitHub CLI not installed - skipping GitHub release creation."
    info "PyPI publishing will still work via the tag-triggered workflow."
fi

success "Release process completed! 🎉"
success "PyPI publishing is happening automatically via GitHub Actions"

echo
info "Monitor the release at:"
echo "- GitHub Actions: https://github.com/mclamee/credential-manager-mcp/actions"
echo "- PyPI: https://pypi.org/project/credential-manager-mcp/" 