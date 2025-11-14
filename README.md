# MTG-MCP

<!-- mcp-name: io.github.wtfregia/mtg-mcp -->

**Magic: The Gathering Model Context Protocol Server**

A comprehensive Model Context Protocol (MCP) server that provides AI assistants with rich Magic: The Gathering information, including card data, comprehensive rules, EDHREC recommendations, combo interactions, and intelligent Commander deck generation.

[![PyPI version](https://badge.fury.io/py/mtg-mcp.svg)](https://pypi.org/project/mtg-mcp/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## Quick Links

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[Tools Documentation](docs/TOOLS.md)** - Complete API reference
- **[PyPI Package](https://pypi.org/project/mtg-mcp/)** - Install from Python Package Index

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

### Deck Generation & Import

- **Commander Deck Validation**: Validates commander legality including partner rules (Partner, Partner with, Choose a Background, Friends Forever, Doctor's Companion)
- **[HIGHLY EXPERIMENTAL] Deck Generation**: Generates complete 100-card Commander decklists based on:
  - EDHREC recommendations
  - Target power level bracket (1-5)
  - Commander color identity restrictions
  - Deck composition best practices
  - Combo synergies
- **Deck Import**: Fetch and analyze decks from popular deck-building platforms:
  - **Moxfield**: Import decks with automatic commander detection
  - **Archidekt**: Import decks with category organization
- **Export Format**: Generates decklists in standard format compatible with Moxfield, Archidekt, and other deck building tools

## Installation

For detailed installation instructions and troubleshooting, see the **[Setup Guide](docs/SETUP.md)**.

### Quick Start (Recommended)

Install directly from PyPI:

```bash
pip install mtg-mcp
```

Or using `uv`:

```bash
uv pip install mtg-mcp
```

### Development Installation

For development or to use the latest unreleased features, see the [Development Installation section](docs/SETUP.md#option-3-development-installation) in the Setup Guide.

## Usage

For complete usage instructions and configuration examples, see the **[Configuration Guide](docs/CONFIGURATION.md)**.

### Running as a Standalone Server

After installation, you can run the server directly:

```bash
mtg-mcp
```

For debug logging:
```bash
mtg-mcp --debug
```

### MCP Client Integration

Configuration examples for popular MCP clients:

- **[Claude Desktop](docs/CONFIGURATION.md#claude-desktop-configuration)** - Desktop AI assistant
- **[VS Code with Cline](docs/CONFIGURATION.md#vs-code-cline-extension)** - Code editor integration

See the [Configuration Guide](docs/CONFIGURATION.md) for detailed setup instructions and troubleshooting.

### Available Tools

For complete API documentation with parameters, return types, and examples, see the **[Tools Documentation](docs/TOOLS.md)**.

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
- `mtg-archidekt-fetch`: Fetch deck data from Archidekt
- `mtg-moxfield-fetch`: Fetch deck data from Moxfield (with automatic commander detection)

## Examples

For more examples and detailed usage patterns, see the **[Quick Start Guide](docs/QUICKSTART.md)** and **[Tools Documentation](docs/TOOLS.md)**.

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
- **Archidekt**: Deck import
- **Moxfield**: Deck import

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

MTG-MCP includes support for the Commander bracket system (1-5). For detailed bracket criteria and guidelines, see the **[Tools Documentation - Commander Brackets](docs/TOOLS.md#mtg-commander-brackets)**.

- **Bracket 1**: Casual/Exhibition - Budget-friendly, thematic gameplay
- **Bracket 2**: Core - Focused strategies with some powerful cards
- **Bracket 3**: Upgraded - Optimized decks with powerful cards and combos
- **Bracket 4**: Optimized - Highly tuned with extensive tutors and fast mana
- **Bracket 5**: Competitive EDH (cEDH) - Maximum optimization

The deck generator respects bracket specifications when selecting cards and building strategies.

## Export Format

For complete export format specifications and examples, see the **[Tools Documentation - Export Format](docs/TOOLS.md#mtg-export-format)**.

Generated decklists follow the standard format compatible with popular deck building tools like Moxfield and Archidekt.

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
