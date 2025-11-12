# MTG MCP Tools Documentation

This document provides detailed information about each tool available in the MTG Model Context Protocol (MCP) server.

## Table of Contents

1. [Context Tools](#context-tools)
2. [Rules Tools](#rules-tools)
3. [Card Information Tools](#card-information-tools)
4. [Commander Tools](#commander-tools)
5. [Deck Tools](#deck-tools)

---

## Context Tools

### mtg.context.get

**Purpose**: Retrieve base context information about Magic: The Gathering.

**File**: [`src/tools/context.py`](../src/tools/context.py)

**Intended Behavior**:
- Returns fundamental information about the Magic: The Gathering card game
- Provides an overview of available tools and their purposes
- Includes basic game concepts such as mana, colors, deck construction requirements
- Specifies the current version of comprehensive rules being used
- Defines usage guidelines for the MCP server

**Returns**:
- Game description and publisher information
- Basic concepts (mana, colors, deck construction, starting life)
- List of available tools with descriptions
- Usage guidelines and intended use cases
- Rules version and last updated date

**Use Cases**:
- Initial setup and orientation for new users
- Understanding what tools are available
- Getting basic MTG game information
- Checking the current rules version

---

### mtg.context.commander

**Purpose**: Retrieve comprehensive Commander/EDH format rules and deck construction requirements.

**File**: [`src/tools/context.py`](../src/tools/context.py)

**Intended Behavior**:
- Returns detailed information specific to the Commander format
- Provides deck construction rules (100 cards, singleton format, color identity)
- Explains the command zone and commander tax mechanics
- Lists banned cards in the Commander format
- Includes partner mechanics and special rules

**Returns**:
- Format name and description
- Deck construction requirements
- Commander-specific rules (command zone, commander tax)
- Banned cards list (fetched from Scryfall)
- Game-changing cards and staples
- Partner mechanics explanation
- Multiplayer and politics considerations

**Use Cases**:
- Understanding Commander format rules
- Checking Commander-specific deck construction requirements
- Verifying banned cards
- Learning about commander tax and the command zone

---

## Rules Tools

### mtg-rules-get

**Purpose**: Get an overview of the MTG comprehensive rules structure.

**File**: [`src/tools/rules.py`](../src/tools/rules.py)

**Intended Behavior**:
- Returns high-level information about the comprehensive rules
- Provides a list of major rule sections
- Shows the last updated date of the rules
- Guides users on how to search for specific rules

**Returns**:
- Last updated date
- Major sections (Game Concepts, Parts of the Game, Turn Structure, etc.)
- List of available rule sections
- Instructions on using `mtg.rules.search`

**Use Cases**:
- Getting an overview of rule categories
- Checking when rules were last updated
- Understanding the structure of comprehensive rules

---

### mtg.rules.search

**Purpose**: Search the comprehensive rules by section number or keyword.

**File**: [`src/tools/rules.py`](../src/tools/rules.py)

**Parameters**:
- `section` (optional): Section number to search (e.g., "100", "701.2")
- `keyword` (optional): Keyword to search in rule text (e.g., "combat", "mana")

**Intended Behavior**:
- Searches comprehensive rules by section number or keyword
- Returns exact matches for section numbers and all subsections
- Returns all rules containing the keyword when searching by text
- Case-insensitive keyword search

**Returns**:
- Dictionary of matching rule numbers and their text
- Error message if no matches found or if rules are unavailable

**Use Cases**:
- Looking up specific rule numbers
- Finding all rules related to a keyword (e.g., "trample", "mulligan")
- Getting detailed rule explanations
- Resolving rules disputes

---

## Card Information Tools

### mtg-cardtypes-get

**Purpose**: Get detailed information about Magic card types, subtypes, and supertypes.

**File**: [`src/tools/cardtypes.py`](../src/tools/cardtypes.py)

**Intended Behavior**:
- Fetches all card types from the MTG SDK
- Provides descriptions and timing rules for main types
- Lists subtypes organized by main type
- Includes supertypes like "Legendary" and "Basic"
- Provides example cards for each type

**Returns**:
- Main types with descriptions, timing/rules, and examples
- Subtypes organized by category (Creature, Land, Artifact, etc.)
- Supertypes list

**Use Cases**:
- Understanding different card types
- Learning about creature types and land types
- Finding example cards of specific types
- Understanding timing restrictions for card types

---

### mtg.ruling.search

**Purpose**: Search for official Scryfall rulings for a specific card.

**File**: [`src/tools/ruling.py`](../src/tools/ruling.py)

**Parameters**:
- `card_name`: The name of the card to search for rulings

**Intended Behavior**:
- Searches Scryfall for the card using fuzzy name matching
- Retrieves official rulings and clarifications for the card
- Returns card type information and oracle text
- Provides published dates for each ruling

**Returns**:
- Card name (exact match from Scryfall)
- Card type line
- Oracle text
- Total number of rulings
- List of rulings with published dates and commentary
- Source attribution (Scryfall)

**Use Cases**:
- Finding official rulings for specific cards
- Resolving card interaction questions
- Understanding complex card mechanics
- Checking judge rulings and clarifications

---

### mtg.combos.search

**Purpose**: Search for known card combinations and combos in Commander format.

**File**: [`src/tools/combos.py`](../src/tools/combos.py)

**Parameters**:
- `card_name`: The name of the card to find combos for

**Intended Behavior**:
- Queries the Commander Spellbook API for known combos
- Returns combos that are legal in Commander format
- Limits results to 5 combos for readability
- Provides color identity and combo descriptions

**Returns**:
- Card name
- Total number of combos found
- List of combo details (cards involved, color identity, description)
- Source attribution (Commander Spellbook)
- API URL for reference

**Use Cases**:
- Finding combo lines for a specific card
- Building combo-focused Commander decks
- Understanding card synergies
- Discovering infinite combos

---

## Commander Tools

### mtg.commander.recommend

**Purpose**: Get top recommended cards for a commander from EDHREC.

**File**: [`src/tools/commander.py`](../src/tools/commander.py)

**Parameters**:
- `card_name`: The commander name to get recommendations for
- `include_context` (optional, default=True): Include Commander format context

**Intended Behavior**:
- Validates the card exists using Scryfall
- Fetches top card recommendations from EDHREC
- Checks if the card is a legendary creature (valid commander)
- Returns popularity statistics (number of decks using the commander)
- Optionally includes full Commander format context

**Returns**:
- Card name (exact match)
- Whether card is a legendary creature
- Number of decks on EDHREC
- Top 10 recommended cards with:
  - Card names
  - Number of decks using each card
  - Card prices (if available)
- Optional: Full Commander format context and bracket information

**Use Cases**:
- Building a new Commander deck
- Finding staple cards for a commander
- Understanding popular card choices
- Getting deck-building inspiration

---

### mtg.commander.brackets

**Purpose**: Get information about Commander power level brackets and criteria.

**File**: [`src/tools/commander.py`](../src/tools/commander.py)

**Intended Behavior**:
- Returns the official Commander bracket system information
- Describes all 4 power level brackets (Bracket 1-4)
- Provides characteristics, strategies, and example cards for each bracket
- Explains bracket-defining cards and effects
- Helps players understand and communicate deck power levels

**Returns**:
- System description and source
- Total number of brackets (4)
- Detailed information for each bracket:
  - Power level description
  - Characteristics
  - Example strategies
  - Typical cards
  - Budget ranges
- Bracket-defining effects (fast mana, free interaction, combos, stax)
- Reference URL

**Use Cases**:
- Understanding deck power levels
- Communicating with playgroups about expectations
- Building decks for specific power levels
- Categorizing existing decks

---

### mtg-export-format

**Purpose**: Get the standard format for exporting/importing Magic decklists.

**File**: [`src/tools/commander.py`](../src/tools/commander.py)

**Intended Behavior**:
- Defines the standard decklist format for import/export
- Specifies the exact pattern: `[quantity]x [Card Name]`
- Provides strict formatting rules to ensure compatibility
- Lists what NOT to include (comments, headers, blank lines)
- Explains Commander-specific requirements (100 cards, singleton rule)

**Returns**:
- Format structure and pattern
- Singleton card rules
- Basic land rules (allowed multiple copies)
- Critical formatting rules (what to include/exclude)
- Commander-specific requirements
- Validation rules
- Compatible deck-building tools

**Use Cases**:
- Exporting decklists for import into Moxfield, Archidekt, etc.
- Understanding proper decklist formatting
- Ensuring decklist compatibility across platforms
- Validating decklist structure

---

### mtg.commander.deck

**Purpose**: Validate commanders and gather comprehensive data for generating a legal Commander deck.

**File**: [`src/tools/commander.py`](../src/tools/commander.py)

**Parameters**:
- `commanders`: List of commander names (1-2 commanders)
- `bracket` (optional, default=2): Target power level bracket (1-5)

**Intended Behavior**:
- Validates that commanders are legendary creatures
- Checks color identity compatibility for partner commanders
- Verifies partner abilities are valid
- Gathers comprehensive data for deck construction:
  - Commander recommendations from EDHREC
  - Known combos for each commander
  - Official rulings
  - Bracket-appropriate card suggestions
- Calculates combined color identity for deck building
- Provides deck construction guidance based on target bracket

**Returns**:
- Commander validation results
- Color identity (combined for partners)
- Validation status (valid/invalid)
- For each commander:
  - Card details (name, type, mana cost, colors)
  - EDHREC recommendations
  - Known combos
  - Official rulings
- Bracket information and guidelines
- Deck building resources and suggestions

**Use Cases**:
- Validating commander choices
- Starting a new Commander deck
- Gathering comprehensive data for deck generation
- Understanding color identity restrictions
- Finding synergistic cards for commanders

---

## Deck Tools

### mtg.archidekt.fetch

**Purpose**: Fetch deck information and card list from an Archidekt deck URL.

**File**: [`src/tools/archidekt.py`](../src/tools/archidekt.py)

**Parameters**:
- `deck_url`: The Archidekt deck URL (e.g., `https://archidekt.com/decks/12345/deck-name`)

**Intended Behavior**:
- Extracts deck ID from the provided URL
- Fetches deck data from the Archidekt API
- Parses deck information (name, format, owner, view count)
- Organizes cards by category (Commander, Creatures, Lands, etc.)
- Provides complete card details including oracle information

**Returns**:
- Success status
- Deck information:
  - Deck name
  - Description
  - Format (Commander, Modern, etc.)
  - Owner username
  - View count
  - Created/updated dates
- Commander cards (if applicable)
- Total card count
- Cards by category with full details:
  - Card name
  - Quantity
  - Mana cost
  - Card type
  - Colors and color identity
  - Oracle text
  - Power/toughness (for creatures)
  - Set information
  - Rarity

**Use Cases**:
- Importing decks from Archidekt
- Analyzing existing decklists
- Reviewing deck composition
- Extracting card lists for analysis or import

---

## Rate Limiting and Error Handling

All tools that make external API calls implement rate limiting to respect API usage policies:

- **Scryfall API**: 100ms delay between calls
- **EDHREC**: 100ms delay between calls
- **Commander Spellbook**: Rate limited
- **Archidekt**: Rate limited

All tools include comprehensive error handling and return meaningful error messages when:
- Cards are not found
- APIs are unavailable
- Invalid parameters are provided
- Network errors occur

---

## Additional Resources

- **Source Code**: All tool implementations are in [`src/tools/`](../src/tools/)
- **Tests**: Comprehensive unit tests are in [`tests/`](../tests/)
- **Utilities**: Shared utilities (rate limiting, caching) are in [`src/utils.py`](../src/utils.py)

---

## Contributing

When adding or modifying tools:
1. Update the function documentation in the source file
2. Add comprehensive unit tests in the `tests/` directory
3. Update this documentation with the new tool's behavior
4. Ensure rate limiting is implemented for external API calls
5. Include proper error handling and logging
