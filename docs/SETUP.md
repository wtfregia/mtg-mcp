# Setup Guide for MTG-MCP

This guide provides step-by-step instructions for installing and configuring MTG-MCP with various MCP clients.

## Installation

### Option 1: Install from PyPI (Recommended)

The simplest way to install MTG-MCP is from PyPI:

```bash
pip install mtg-mcp
```

This will install the `mtg-mcp` command globally, making it available from anywhere on your system.

### Option 2: Install with uv

If you're using `uv` for faster package management:

```bash
uv pip install mtg-mcp
```

### Option 3: Development Installation

For development or testing unreleased features:

```bash
git clone https://github.com/wtfregia/mtg-mcp.git
cd mtg-mcp
pip install -e .
```

## Configuration

### Claude Desktop

Claude Desktop uses a JSON configuration file to manage MCP servers.

#### Configuration File Locations

- **MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Basic Configuration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mtg-mcp": {
      "command": "mtg-mcp"
    }
  }
}
```

#### Virtual Environment Configuration

If you installed MTG-MCP in a virtual environment, specify the full path:

**MacOS/Linux**:
```json
{
  "mcpServers": {
    "mtg-mcp": {
      "command": "/full/path/to/.venv/bin/mtg-mcp"
    }
  }
}
```

**Windows**:
```json
{
  "mcpServers": {
    "mtg-mcp": {
      "command": "C:\\full\\path\\to\\.venv\\Scripts\\mtg-mcp.exe"
    }
  }
}
```

#### With Debug Logging

To enable debug logging for troubleshooting:

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

### VS Code with Cline Extension

The Cline extension for VS Code uses a `.vscode/mcp.json` file in your workspace.

#### Basic Configuration

Create or edit `.vscode/mcp.json` in your workspace:

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

#### Development Configuration

If working on the MTG-MCP repository itself:

**Linux/MacOS**:
```json
{
  "servers": {
    "mtg-mcp": {
      "type": "stdio",
      "command": "./.venv/bin/python",
      "args": ["-m", "mtg_mcp"]
    }
  }
}
```

**Windows**:
```json
{
  "servers": {
    "mtg-mcp": {
      "type": "stdio",
      "command": ".venv\\Scripts\\python.exe",
      "args": ["-m", "mtg_mcp"]
    }
  }
}
```

#### With Debug Logging

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

### Other MCP Clients

For other MCP-compatible clients, use the following patterns:

#### Stdio Configuration
```json
{
  "command": "mtg-mcp",
  "args": [],
  "type": "stdio"
}
```

#### With Python Module
```json
{
  "command": "python",
  "args": ["-m", "mtg_mcp"],
  "type": "stdio"
}
```

## Verification

### Test the Installation

To verify that MTG-MCP is installed correctly, run:

```bash
mtg-mcp --debug
```

You should see output similar to:
```
2025-11-11 23:17:56,135 - mtg-mcp - INFO - Starting MTG MCP server...
2025-11-11 23:17:56,135 - mtg-mcp - INFO - Python version: 3.13.x
```

Press `Ctrl+C` to stop the server.

### Check Available Commands

After installation, you should have access to:

1. **Command-line tool**: `mtg-mcp`
2. **Python module**: `python -m mtg_mcp`

Both methods start the same MCP server.

## Troubleshooting

### Command Not Found

If you get "command not found" when running `mtg-mcp`:

1. **Check Python's scripts directory is in PATH**:
   ```bash
   python -m site --user-base
   ```
   Add `<user-base>/bin` (Linux/Mac) or `<user-base>\Scripts` (Windows) to your PATH.

2. **Use the full path**:
   ```bash
   python -m mtg_mcp
   ```

3. **Reinstall the package**:
   ```bash
   pip install --force-reinstall mtg-mcp
   ```

### Import Errors

If you see import errors related to `src.tools`:

1. Make sure you're running from the correct directory
2. Ensure the package is properly installed:
   ```bash
   pip show mtg-mcp
   ```

### MCP Server Not Connecting

1. **Check the configuration file syntax** - JSON must be valid
2. **Verify the command path** - Use absolute paths if relative paths don't work
3. **Enable debug logging** - Add `"args": ["--debug"]` to see detailed logs
4. **Restart the client application** - Changes to config files require a restart

### Permission Issues

On Unix-like systems, you may need to make the script executable:

```bash
chmod +x $(which mtg-mcp)
```

## Updating

To update to the latest version:

```bash
pip install --upgrade mtg-mcp
```

## Uninstallation

To remove MTG-MCP:

```bash
pip uninstall mtg-mcp
```

Remember to also remove the configuration from your MCP client's config file.

## Support

For issues, questions, or contributions:

- **GitHub Issues**: https://github.com/wtfregia/mtg-mcp/issues
- **Repository**: https://github.com/wtfregia/mtg-mcp
- **PyPI Package**: https://pypi.org/project/mtg-mcp/
