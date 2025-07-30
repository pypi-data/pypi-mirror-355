# 🔐 Credential Manager MCP Server

[![Test](https://github.com/mclamee/credential-manager-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/mclamee/credential-manager-mcp/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)

A secure MCP server for managing API credentials locally. **Read-only by default** with simple JSON storage.

## ✨ Features

- 🔒 **Secure by default** - Read-only mode prevents accidental changes
- 📁 **Simple storage** - `~/.credential-manager-mcp/credentials.json`
- 🔧 **Easy setup** - Interactive shell script
- 🔄 **Multi-instance safe** - Always reads fresh data from disk
- 🎯 **Minimal exposure** - Shows only essential data

## 🚀 Quick Start

### 1. Install & Configure

```bash
# Install from PyPI
uvx credential-manager-mcp
```

**Common config** (Claude Desktop):
```json
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
```

**Devlopment config** (run from source):
```json
{
  "mcpServers": {
    "credential-manager": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/credential-manager-mcp",
        "run", "credential-manager-mcp"
      ],
      "env": {
        "CREDENTIAL_MANAGER_READ_ONLY": "false"
      }
    }
  }
}
```

### 2. Add Credentials

```bash
# Interactive mode
./add-credential.sh

# Command line
./add-credential.sh "GitHub" "https://api.github.com" "ghp_token" "username" "2024-12-31T23:59:59"
```

## 🛠 Available Tools

**Read-Only Mode (Default):**
- `list_credentials()` - List credentials (id, app name only)
- `get_credential_details(credential_id)` - Get full details

**Read-Write Mode:**
- `add_credential(app, base_url, access_token, [user_name], [expires])`
- `update_credential(credential_id, [fields...])`
- `delete_credential(credential_id)`

## 📋 Usage Examples

```python
# List all credentials
list_credentials()
# {"credentials": [{"id": "abc...", "app": "GitHub"}], "count": 1}

# Get credential details
get_credential_details("credential-id")

# Add new credential (write mode only)
add_credential("GitHub", "https://api.github.com", "ghp_token", "user", "2024-12-31T23:59:59")
```

## ⚙️ Configuration

**Environment Variables:**
- `CREDENTIAL_MANAGER_READ_ONLY` - Set to `"false"` for write operations (default: `"true"`)

**Expiration Format:**
- `"2024-12-31T23:59:59"` - ISO datetime
- `"never"` - No expiration

## 🔒 Security

- Read-only by default
- Local storage only (`~/.credential-manager-mcp/credentials.json`)
- File locking for safe concurrent access
- Minimal data exposure in listings

## 🧪 Development

```bash
git clone https://github.com/mclamee/credential-manager-mcp.git
cd credential-manager-mcp
uv sync --dev
uv run pytest test/ -v
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details. 