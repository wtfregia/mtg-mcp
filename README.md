# MTG-MCP

<!-- mcp-name: io.github.wtfregia/mtg-mcp -->

**Magic: The Gathering Model Context Protocol Server**

A comprehensive Model Context Protocol (MCP) server that provides AI assistants with rich Magic: The Gathering information, including card data, comprehensive rules, EDHREC recommendations, combo interactions, and intelligent Commander deck generation.

## Overview

MTG-MCP integrates multiple Magic: The Gathering data sources to provide AI assistants with authoritative information for answering questions, making recommendations, and generating legal Commander decklists. The server leverages official comprehensive rules, Scryfall card database, EDHREC statistics, and Commander Spellbook combo data.

## Features

### Core Information Tools

- **Comprehensive Rules Access**: Query the official Magic: The Gathering comprehensive rules by section or keyword
- **Card Information**: Retrieve detailed card data including type, mana cost, oracle text, and legality
- **Card Rulings**: Access official card rulings and clarifications from Scryfall
- **Card Type Information**: Get detailed information about card types, subtypes, and supertypes

### Commander-Specific Tools

- **Commander Format Context**: Comprehensive information about Commander/EDH format rules, deck construction, and gameplay
- **EDHREC Integration**: Pull top recommended cards for any commander based on EDHREC data
- **Combo Search**: Find card combinations and interactions from Commander Spellbook
- **Bracket System**: Access Commander power level brackets (1-5) with detailed criteria and guidelines
- **Dynamic Game Changers List**: Automatically updated list of high-impact cards that affect deck power level
- **Dynamic Banned List**: Real-time Commander banned cards list from Scryfall

### Deck Generation

- **Commander Deck Validation**: Validates commander legality including partner rules (Partner, Partner with, Choose a Background, Friends Forever, Doctor's Companion)
- **[HIGHLY EXPERIMENTAL] Deck Generation**: Generates complete 100-card Commander decklists based on:
  - EDHREC recommendations
  - Target power level bracket (1-5)
  - Commander color identity restrictions
  - Deck composition best practices
  - Combo synergies
- **Export Format**: Generates decklists in standard format compatible with Moxfield, Archidekt, and other deck building tools

## Installation

### Prerequisites

- Python 3.12 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mtg-mcp.git
cd mtg-mcp
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

## Usage

### Running the Server

Start the MCP server:
```bash
python main.py
```

For debug logging:
```bash
python main.py --debug
```

### VS Code Integration

Add the following configuration to your `.vscode/mcp.json` file:

```json
{
  "servers": {
    "mtg-mcp": {
      "type": "stdio",
      "command": "./.venv/bin/python",
      "args": [
        "main.py"
      ]
    }
  }
}
```

On Windows, use:
```json
{
  "servers": {
    "mtg-mcp": {
      "type": "stdio",
      "command": ".venv/Scripts/python.exe",
      "args": [
        "main.py"
      ]
    }
  }
}
```

### Available Tools

The server exposes the following MCP tools:

- `mtg-context-get`: Get basic MTG game information
- `mtg-context-commander`: Get comprehensive Commander/EDH format rules
- `mtg-cardtypes-get`: Get detailed card type information
- `mtg-rules-get`: Get overview of comprehensive rules
- `mtg-rules-search`: Search rules by section or keyword
- `mtg-ruling-search`: Search official card rulings
- `mtg-combos-search`: Search for card combos in Commander
- `mtg-commander-recommend`: Get EDHREC recommendations for a commander
- `mtg-commander-brackets`: Get Commander bracket information
- `mtg-export-format`: Get deck export format guidelines
- `mtg-commander-deck`: Validate commanders and generate deck data

## Examples

### Generate a Competitive EDH Deck

```
Use #mtg-commander-deck to generate a Bracket 5 (cEDH) commander deck with Tymna the Weaver and Kraum, Ludevic's Opus.
```

### Generate a Casual Commander Deck

```
Use #mtg-commander-deck to create a Bracket 2 casual deck with Atraxa, Praetors' Voice.
```

### Search for Card Rulings

```
Use #mtg-ruling-search to find rulings for Doubling Season.
```

### Find Commander Recommendations

```
Use #mtg-commander-recommend to get the top cards for Kinnan, Bonder Prodigy.
```

### Search for Combos

```
Use #mtg-combos-search to find combos with Thassa's Oracle.
```

## Data Sources

- **Scryfall API**: Card data, rulings, and legality information
- **EDHREC**: Commander recommendations and deck statistics
- **Commander Spellbook**: Combo interactions and synergies
- **MTG SDK**: Card types and subtypes
- **Wizards of the Coast**: Official comprehensive rules and banned list

## Development

### Running Tests

```bash
pytest
```

### Code Quality

The project uses Ruff for linting and formatting:

```bash
ruff check .
ruff format .
```

## Bracket System

MTG-MCP includes support for the Commander bracket system (1-5):

- **Bracket 1**: Casual/Exhibition - Budget-friendly, thematic gameplay
- **Bracket 2**: Core - Focused strategies with some powerful cards
- **Bracket 3**: Upgraded - Optimized decks with powerful cards and combos
- **Bracket 4**: Optimized - Highly tuned with extensive tutors and fast mana
- **Bracket 5**: Competitive EDH (cEDH) - Maximum optimization

The deck generator respects bracket specifications when selecting cards and building strategies.

## Export Format

Generated decklists follow the standard format compatible with popular deck building tools:

```
1x Commander Name
1x Sol Ring
1x Arcane Signet
10x Island
15x Plains
```

- No comments or section headers
- Format: `[quantity]x [Card Name]`
- Basic lands can have multiple copies
- All other cards follow singleton rule (1x each)

## Publishing

This project is published to both PyPI and the Model Context Protocol Registry for easy installation.

### Automated Publishing

The project uses GitHub Actions for automated publishing:

1. **Push a version tag** to trigger the workflow:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **GitHub Actions automatically**:
   - Builds the Python package
   - Publishes to PyPI
   - Publishes to MCP Registry using GitHub OIDC authentication

### Prerequisites for Publishing

To set up publishing for the first time, you need:

1. **PyPI API Token**: Create a token at https://pypi.org/manage/account/token/
   - Add it as a GitHub secret named `PYPI_API_TOKEN`
   - Go to: Repository Settings → Secrets and variables → Actions → New repository secret

2. **No additional secrets needed for MCP Registry**: The workflow uses GitHub OIDC for authentication

### Manual Publishing (Alternative)

If you prefer to publish manually:

1. Install the MCP publisher CLI (see [MCP Publishing Guide](https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/publish-server.md))
2. Authenticate with GitHub: `mcp-publisher login github`
3. Publish: `mcp-publisher publish`

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - See [LICENSE](LICENSE.md) file for details.

## Acknowledgments

- Scryfall for comprehensive card data API
- EDHREC for commander recommendations and statistics
- Commander Spellbook for combo database
- Wizards of the Coast for Magic: The Gathering

## Disclaimer

MTG-MCP is unofficial Fan Content permitted under the Fan Content Policy. Not approved/endorsed by Wizards of the Coast. Portions of the materials used are property of Wizards of the Coast. ©Wizards of the Coast LLC.
