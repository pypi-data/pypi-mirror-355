#!/bin/bash

# Changelog generation script for credential-manager-mcp
# Usage: ./scripts/generate-changelog.sh --version v1.0.0 [--from-tag v0.9.0] [--commit] [--help]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
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

show_help() {
    cat << EOF
Changelog Generation Script for credential-manager-mcp

Usage: $0 --version VERSION [OPTIONS]

Required:
  --version VERSION    The version to generate changelog for (e.g., v1.0.0)

Options:
  --from-tag TAG      Generate changelog from this tag (auto-detected if not provided)
  --commit            Commit the generated changelog file
  --help              Show this help message

Examples:
  $0 --version v1.0.0
  $0 --version v1.0.0 --from-tag v0.9.0
  $0 --version v1.0.0 --commit
EOF
}

# Parse arguments
VERSION=""
FROM_TAG=""
SHOULD_COMMIT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --from-tag)
            FROM_TAG="$2"
            shift 2
            ;;
        --commit)
            SHOULD_COMMIT=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1. Use --help for usage information."
            ;;
    esac
done

# Validate required arguments
if [[ -z "$VERSION" ]]; then
    error "Version is required. Use --version to specify it."
fi

# Ensure version starts with 'v'
if [[ ! "$VERSION" =~ ^v ]]; then
    VERSION="v$VERSION"
fi

# Auto-detect from-tag if not provided
if [[ -z "$FROM_TAG" ]]; then
    # Get the latest tag (which should be the previous version)
    FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -n "$FROM_TAG" ]]; then
        info "Auto-detected previous tag: $FROM_TAG"
    else
        FROM_TAG=""
        info "No previous tag found, generating initial release changelog"
    fi
fi

# Generate changelog function
generate_changelog() {
    local version=$1
    local from_tag=$2
    
    if [[ -n "$from_tag" ]]; then
        echo "## 🚀 Release $version"
        echo ""
        echo "### What's Changed"
        
        # Get commits since last tag, format them nicely
        git log --oneline --pretty=format:"- %s (%h)" "$from_tag"..HEAD | head -20
        
        echo ""
        echo "### Installation"
        echo "\`\`\`bash"
        echo "uvx credential-manager-mcp"
        echo "\`\`\`"
        echo ""
        echo "### Configuration"
        echo "Add to your MCP client config:"
        echo "\`\`\`json"
        echo "{"
        echo "  \"mcpServers\": {"
        echo "    \"credential-manager\": {"
        echo "      \"command\": \"uvx\","
        echo "      \"args\": [\"credential-manager-mcp\"],"
        echo "      \"env\": {"
        echo "        \"CREDENTIAL_MANAGER_READ_ONLY\": \"false\""
        echo "      }"
        echo "    }"
        echo "  }"
        echo "}"
        echo "\`\`\`"
        
        echo ""
        echo "**Full Changelog**: https://github.com/mclamee/credential-manager-mcp/compare/$from_tag...$version"
    else
        echo "## 🚀 Initial Release $version"
        echo ""
        echo "### What's New"
        echo "- Initial release of Credential Manager MCP Server"
        echo "- Secure API credential management with read-only mode by default"
        echo "- Multi-instance support with file locking"
        echo "- Simple JSON storage in ~/.credential-manager-mcp/"
        echo ""
        echo "### Installation"
        echo "\`\`\`bash"
        echo "uvx credential-manager-mcp"
        echo "\`\`\`"
        echo ""
        echo "### Configuration"
        echo "Add to your MCP client config:"
        echo "\`\`\`json"
        echo "{"
        echo "  \"mcpServers\": {"
        echo "    \"credential-manager\": {"
        echo "      \"command\": \"uvx\","
        echo "      \"args\": [\"credential-manager-mcp\"],"
        echo "      \"env\": {"
        echo "        \"CREDENTIAL_MANAGER_READ_ONLY\": \"false\""
        echo "      }"
        echo "    }"
        echo "  }"
        echo "}"
        echo "\`\`\`"
    fi
}

# Create changelog directory
mkdir -p docs/changelogs

# Generate and save changelog
CHANGELOG_FILE="docs/changelogs/${VERSION}.md"
info "Generating changelog for $VERSION..." >&2
if [[ -n "$FROM_TAG" ]]; then
    info "Generating changelog from $FROM_TAG to HEAD..." >&2
else
    info "Generating initial release changelog..." >&2
fi

generate_changelog "$VERSION" "$FROM_TAG" > "$CHANGELOG_FILE"

success "Changelog saved to $CHANGELOG_FILE" >&2

# Show preview
echo "" >&2
info "Changelog preview:" >&2
echo "====================" >&2
head -15 "$CHANGELOG_FILE" >&2
echo "..." >&2
echo "====================" >&2

# Commit if requested
if [[ "$SHOULD_COMMIT" == true ]]; then
    info "Committing changelog file..." >&2
    git add "$CHANGELOG_FILE"
    git commit -m "Add changelog for $VERSION"
    success "Changelog committed!" >&2
fi

# Output the file path for scripts to use
echo "" >&2
echo "CHANGELOG_FILE=$CHANGELOG_FILE" >&2 