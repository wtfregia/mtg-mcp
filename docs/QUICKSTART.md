# Quick Start Guide

## Installation (Choose One)

### PyPI Installation (Recommended)
```bash
pip install mtg-mcp
```

### Development Installation
```bash
git clone https://github.com/wtfregia/mtg-mcp.git
cd mtg-mcp
pip install -e .
```

## Configuration Examples

### Claude Desktop

Edit your config file:
- **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mtg-mcp": {
      "command": "mtg-mcp"
    }
  }
}
```

### VS Code (Cline Extension)

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "mtg-mcp": {
      "type": "stdio",
      "command": "mtg-mcp"
    }
  }
}
```

## Test Your Installation

Run the following command:
```bash
mtg-mcp --debug
```

You should see server startup messages. Press Ctrl+C to exit.

## Available Tools

Once configured, you'll have access to these tools:

- `mtg-context-get` - Get MTG game information
- `mtg-context-commander` - Commander format rules
- `mtg-rules-search` - Search comprehensive rules
- `mtg-ruling-search` - Card rulings from Scryfall
- `mtg-combos-search` - Find card combos
- `mtg-commander-recommend` - EDHREC recommendations
- `mtg-commander-brackets` - Power level brackets
- `mtg-commander-deck` - Validate and generate decks
- `mtg-archidekt-fetch` - Import Archidekt decks

For detailed documentation, see:
- [Setup Guide](SETUP.md)
- [Tools Documentation](TOOLS.md)
