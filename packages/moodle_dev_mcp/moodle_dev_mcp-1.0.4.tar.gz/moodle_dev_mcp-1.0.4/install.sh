#!/bin/bash
set -e

echo "🚀 Installing Moodle Developer Documentation MCP Server..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}📦 Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create installation directory
INSTALL_DIR="$HOME/.local/bin/moodle_dev_mcp"
mkdir -p "$INSTALL_DIR"

# Install via pip
echo -e "${YELLOW}📥 Installing moodle_dev_mcp...${NC}"
pip install moodle_dev_mcp

echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "📋 Configuration examples:"
echo ""
echo -e "${YELLOW}Continue.dev (~/.continue/config.json):${NC}"
echo '{
  "mcpServers": [
    {
      "name": "moodle_dev_docs",
      "command": "moodle_dev_mcp"
    }
  ]
}'
echo ""
echo -e "${YELLOW}Claude Desktop (~/Library/Application Support/Claude/claude_desktop_config.json):${NC}"
echo '{
  "mcpServers": {
    "moodle_dev_docs": {
      "command": "moodle_dev_mcp"
    }
  }
}'
echo ""
echo -e "${YELLOW}VS Code (.vscode/settings.json):${NC}"
echo '{
  "mcp.servers": {
    "moodle_dev_docs": {
      "command": "moodle_dev_mcp"
    }
  }
}'
