#!/bin/bash

# Credential Manager - Add Credential Helper Script
# This script helps add credentials to the credential manager's JSON file

set -e

# Configuration
CRED_DIR="$HOME/.credential-manager-mcp"
CRED_FILE="$CRED_DIR/credentials.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}Error: $1${NC}" >&2
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

# Generate UUID (cross-platform)
generate_uuid() {
    if command -v uuidgen >/dev/null 2>&1; then
        uuidgen | tr '[:upper:]' '[:lower:]'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c "import uuid; print(str(uuid.uuid4()))"
    else
        # Fallback: create a pseudo-UUID using date and random
        echo "$(date +%s)-$(shuf -i 1000-9999 -n 1)-$(shuf -i 1000-9999 -n 1)-$(shuf -i 1000-9999 -n 1)-$(shuf -i 100000000000-999999999999 -n 1)"
    fi
}

# Validate URL format
validate_url() {
    local url="$1"
    if [[ ! "$url" =~ ^https?:// ]]; then
        error "Base URL must start with http:// or https://"
    fi
}

# Validate and format expiration date
validate_expires() {
    local expires="$1"
    
    # Allow "never" or empty
    if [[ -z "$expires" || "$expires" == "never" ]]; then
        echo "never"
        return 0
    fi
    
    # Check if it's already in ISO format (YYYY-MM-DDTHH:MM:SS)
    if [[ "$expires" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$ ]]; then
        echo "$expires"
        return 0
    fi
    
    # Check if it's a date only (YYYY-MM-DD) and convert to end of day
    if [[ "$expires" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "${expires}T23:59:59"
        return 0
    fi
    
    # Try to parse with date command for validation
    if command -v date >/dev/null 2>&1; then
        # Try different date formats
        if date -d "$expires" >/dev/null 2>&1; then
            # GNU date (Linux)
            formatted=$(date -d "$expires" '+%Y-%m-%dT%H:%M:%S' 2>/dev/null)
            if [[ -n "$formatted" ]]; then
                echo "$formatted"
                return 0
            fi
        elif date -j -f "%Y-%m-%d" "$expires" >/dev/null 2>&1; then
            # BSD date (macOS) - try YYYY-MM-DD format
            formatted=$(date -j -f "%Y-%m-%d" "$expires" '+%Y-%m-%dT23:59:59' 2>/dev/null)
            if [[ -n "$formatted" ]]; then
                echo "$formatted"
                return 0
            fi
        fi
    fi
    
    error "Invalid expiration format. Use ISO datetime (YYYY-MM-DDTHH:MM:SS), date (YYYY-MM-DD), or 'never'"
}

# Create credentials directory and file if they don't exist
setup_credentials_file() {
    if [[ ! -d "$CRED_DIR" ]]; then
        info "Creating credentials directory: $CRED_DIR"
        mkdir -p "$CRED_DIR"
    fi
    
    if [[ ! -f "$CRED_FILE" ]]; then
        info "Creating credentials file: $CRED_FILE"
        echo '{}' > "$CRED_FILE"
    fi
}

# Add credential to JSON file
add_credential() {
    local app="$1"
    local base_url="$2"
    local access_token="$3"
    local user_name="$4"
    local expires="$5"
    
    # Generate unique ID
    local cred_id=$(generate_uuid)
    
    # Validate inputs
    [[ -z "$app" ]] && error "App name is required"
    [[ -z "$base_url" ]] && error "Base URL is required"
    [[ -z "$access_token" ]] && error "Access token is required"
    
    validate_url "$base_url"
    
    # Validate and format expiration
    expires=$(validate_expires "$expires")
    
    # Set defaults
    [[ -z "$user_name" ]] && user_name=null || user_name="\"$user_name\""
    expires="\"$expires\""
    
    # Create credential JSON object
    local credential=$(cat <<EOF
{
  "app": "$app",
  "id": "$cred_id",
  "base_url": "$base_url",
  "access_token": "$access_token",
  "user_name": $user_name,
  "expires": $expires
}
EOF
    )
    
    # Add to credentials file using jq if available, otherwise use python
    if command -v jq >/dev/null 2>&1; then
        # Use jq for JSON manipulation
        local temp_file=$(mktemp)
        jq --argjson cred "$credential" --arg id "$cred_id" '.[$id] = $cred' "$CRED_FILE" > "$temp_file"
        mv "$temp_file" "$CRED_FILE"
    elif command -v python3 >/dev/null 2>&1; then
        # Use Python for JSON manipulation
        python3 << EOF
import json
import sys

try:
    with open('$CRED_FILE', 'r') as f:
        data = json.load(f)
    
    credential = $credential
    data['$cred_id'] = credential
    
    with open('$CRED_FILE', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Credential added successfully")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    else
        error "Either 'jq' or 'python3' is required to manipulate JSON"
    fi
    
    success "Added credential for '$app' with ID: $cred_id"
}

# Interactive mode
interactive_mode() {
    echo -e "${BLUE}🔐 Credential Manager - Add Credential${NC}"
    echo "======================================"
    echo
    
    read -p "App name (e.g., GitHub, Slack): " app
    read -p "Base URL (e.g., https://api.github.com): " base_url
    echo -n "Access token: "
    read -s access_token
    echo
    read -p "Username (optional): " user_name
    read -p "Expires (ISO datetime YYYY-MM-DDTHH:MM:SS, date YYYY-MM-DD, or 'never', default: never): " expires
    
    echo
    add_credential "$app" "$base_url" "$access_token" "$user_name" "$expires"
}

# Show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [APP] [BASE_URL] [ACCESS_TOKEN] [USERNAME] [EXPIRES]

Add credentials to the credential manager.

OPTIONS:
    -h, --help      Show this help message
    -i, --interactive    Interactive mode (default if no arguments)
    -l, --list      List existing credentials

ARGUMENTS:
    APP             Application name (e.g., GitHub, Slack)
    BASE_URL        Base URL for the API (e.g., https://api.github.com)
    ACCESS_TOKEN    API access token or key
    USERNAME        Username (optional)
    EXPIRES         ISO datetime (YYYY-MM-DDTHH:MM:SS), date (YYYY-MM-DD), or 'never' (optional, default: never)

EXAMPLES:
    # Interactive mode
    $0

    # Command line mode
    $0 GitHub https://api.github.com ghp_xxxxxxxxxxxx myusername 2024-12-31T23:59:59

    # List existing credentials
    $0 --list

STORAGE:
    Credentials are stored in: $CRED_FILE
EOF
}

# List existing credentials
list_credentials() {
    if [[ ! -f "$CRED_FILE" ]]; then
        warn "No credentials file found at: $CRED_FILE"
        return
    fi
    
    echo -e "${BLUE}📋 Existing Credentials${NC}"
    echo "======================"
    
    if command -v jq >/dev/null 2>&1; then
        jq -r 'to_entries[] | "\(.value.app) (\(.value.id)) - \(.value.base_url)"' "$CRED_FILE" 2>/dev/null || warn "No credentials found or invalid JSON"
    elif command -v python3 >/dev/null 2>&1; then
        python3 << EOF
import json
try:
    with open('$CRED_FILE', 'r') as f:
        data = json.load(f)
    
    if not data:
        print("No credentials found")
    else:
        for cred_id, cred in data.items():
            print(f"{cred['app']} ({cred['id']}) - {cred['base_url']}")
except Exception as e:
    print("No credentials found or invalid JSON")
EOF
    else
        warn "Either 'jq' or 'python3' is required to read credentials"
    fi
}

# Main script logic
main() {
    # Setup credentials file
    setup_credentials_file
    
    # Parse arguments
    case "${1:-}" in
        -h|--help)
            show_usage
            exit 0
            ;;
        -l|--list)
            list_credentials
            exit 0
            ;;
        -i|--interactive)
            interactive_mode
            exit 0
            ;;
        "")
            # No arguments - interactive mode
            interactive_mode
            exit 0
            ;;
        *)
            # Command line arguments
            if [[ $# -lt 3 ]]; then
                error "Insufficient arguments. Use --help for usage information."
            fi
            add_credential "$1" "$2" "$3" "$4" "$5"
            ;;
    esac
}

# Run main function
main "$@" 