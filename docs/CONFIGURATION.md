# Configuration Examples

After installing MTG-MCP with `pip install mtg-mcp`, use one of these configurations:

## Claude Desktop Configuration

**File Location**:
- MacOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Configuration**:
```json
{
  "mcpServers": {
    "mtg-mcp": {
      "command": "mtg-mcp"
    }
  }
}
```

## VS Code Cline Extension

**File Location**: `.vscode/mcp.json` (in your workspace root)

**Configuration**:
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

## Enable Debug Logging

Add the `--debug` argument to see detailed logs:

**Claude Desktop**:
```json
{
  "mcpServers": {
    "mtg-mcp": {
      "command": "mtg-mcp",
      "args": ["--debug"]
    }
  }
}
```

**VS Code**:
```json
{
  "servers": {
    "mtg-mcp": {
      "type": "stdio",
      "command": "mtg-mcp",
      "args": ["--debug"]
    }
  }
}
```

## Using with Virtual Environments

If you installed in a virtual environment and the `mtg-mcp` command isn't in your PATH, specify the full path:

**Claude Desktop (Linux/MacOS)**:
```json
{
  "mcpServers": {
    "mtg-mcp": {
      "command": "/full/path/to/venv/bin/mtg-mcp"
    }
  }
}
```

**Claude Desktop (Windows)**:
```json
{
  "mcpServers": {
    "mtg-mcp": {
      "command": "C:\\full\\path\\to\\venv\\Scripts\\mtg-mcp.exe"
    }
  }
}
```

**VS Code (Linux/MacOS)**:
```json
{
  "servers": {
    "mtg-mcp": {
      "type": "stdio",
      "command": "/full/path/to/venv/bin/python",
      "args": ["-m", "mtg_mcp"]
    }
  }
}
```

**VS Code (Windows)**:
```json
{
  "servers": {
    "mtg-mcp": {
      "type": "stdio",
      "command": "C:\\full\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["-m", "mtg_mcp"]
    }
  }
}
```
