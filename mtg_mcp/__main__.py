"""
Magic: The Gathering Context MCP Server.
This server provides AI chatbots with context about Magic: The Gathering.
"""
import argparse
import logging
import sys
from typing import Any, Dict, List

from mcp.server import fastmcp

# Import tool functions from mtg_mcp/tools
from mtg_mcp.tools.archidekt import fetch_archidekt_deck
from mtg_mcp.tools.cardtypes import get_card_types
from mtg_mcp.tools.combos import search_combos
from mtg_mcp.tools.commander import (
    generate_commander_deck_data,
    get_commander_brackets,
    get_export_format,
    recommend_commander_cards,
)
from mtg_mcp.tools.context import get_commander_context, get_context
from mtg_mcp.tools.moxfield import fetch_moxfield_deck
from mtg_mcp.tools.rules import get_rules_info, search_rules
from mtg_mcp.tools.ruling import search_rulings

# Set up logging to stderr so VS Code can capture it
# Default to WARNING level, can be overridden with --debug flag
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger('mtg-mcp')

# Initialize MCP server with debug mode
mcp = fastmcp.FastMCP("mtg-context", debug=True)
logger.info("MCP Server initialized")

# Register all tools with the MCP server
@mcp.tool("mtg-context-get")
async def tool_get_context() -> Dict[str, Any]:
    """Get the base context about Magic: The Gathering."""
    return await get_context()

@mcp.tool("mtg-context-commander")
async def tool_get_commander_context() -> Dict[str, Any]:
    """Get comprehensive information about the Commander/EDH format."""
    return await get_commander_context()

@mcp.tool("mtg-rules-get")
async def tool_get_rules_info() -> Dict[str, Any]:
    """Get information from the MTG comprehensive rules."""
    return await get_rules_info()

@mcp.tool("mtg-rules-search")
async def tool_search_rules(section: str | None = None, keyword: str | None = None) -> Dict[str, Any]:
    """Search the comprehensive rules by section number or keyword."""
    return await search_rules(section, keyword)

@mcp.tool("mtg-cardtypes-get")
async def tool_get_card_types() -> Dict[str, Any]:
    """Get detailed card type information from MTG SDK."""
    return await get_card_types()

@mcp.tool("mtg-ruling-search")
async def tool_search_rulings(card_name: str) -> Dict[str, Any]:
    """
    Search for official rulings for a specific Magic: The Gathering card.

    Args:
        card_name: The name of the card to search for rulings.

    Returns:
        Dictionary containing ruling information or an error message.
    """
    return await search_rulings(card_name)

@mcp.tool("mtg-combos-search")
async def tool_search_combos(card_name: str) -> Dict[str, Any]:
    """
    Search for Commander combos involving a specific card using the Commander Spellbook API.

    Args:
        card_name: The name of the card to search for combos.

    Returns:
        Dictionary containing combo information or an error message.
    """
    return await search_combos(card_name)

@mcp.tool("mtg-commander-recommend")
async def tool_recommend_commander_cards(card_name: str, include_context: bool = True) -> Dict[str, Any]:
    """
    Get top 10 recommended cards for a commander from EDHREC.

    Args:
        card_name: The name of the card (assumed to be a commander).
        include_context: If True, also includes Commander format context and bracket information.

    Returns:
        Dictionary containing top recommended cards or an error message.
    """
    return await recommend_commander_cards(card_name, include_context)

@mcp.tool("mtg-commander-brackets")
async def tool_get_commander_brackets() -> Dict[str, Any]:
    """
    Get information about Commander/EDH brackets and their criteria.

    Returns:
        Dictionary containing bracket information, criteria, and guidelines.
    """
    return await get_commander_brackets()

@mcp.tool("mtg-export-format")
async def tool_get_export_format() -> Dict[str, Any]:
    """
    Get information about the proper format for exporting/importing Magic: The Gathering decklists.

    Returns:
        Dictionary containing deck export format guidelines and examples.
    """
    return await get_export_format()

@mcp.tool("mtg-commander-deck")
async def tool_generate_commander_deck_data(commanders: List[str], bracket: int = 2) -> Dict[str, Any]:
    """
    Validate commanders and gather comprehensive data for generating a legal Commander deck.

    Args:
        commanders: List of commander names (1-2 commanders)
        bracket: Target power level bracket (1-5, default: 2)

    Returns:
        Dictionary containing validation results, commander data, and deck-building resources
    """
    return await generate_commander_deck_data(commanders, bracket)

@mcp.tool("mtg-archidekt-fetch")
async def tool_fetch_archidekt_deck(deck_url: str) -> Dict[str, Any]:
    """
    Fetch a deck from Archidekt using a deck URL.

    Args:
        deck_url: The Archidekt deck URL (e.g., https://archidekt.com/decks/17187915/automation_testing)

    Returns:
        Dictionary containing deck information and card list or an error message.
    """
    return await fetch_archidekt_deck(deck_url)

@mcp.tool("mtg-moxfield-fetch")
async def tool_fetch_moxfield_deck(deck_url: str) -> Dict[str, Any]:
    """
    Fetch a deck from Moxfield using a deck URL.

    Args:
        deck_url: The Moxfield deck URL (e.g., https://moxfield.com/decks/TdOsPBP3302BdskyLVzU-A)

    Returns:
        Dictionary containing deck information and card list or an error message.
        For Commander decks, the commander(s) will be prominently identified in the response.
    """
    return await fetch_moxfield_deck(deck_url)

def main():
    """Main entry point for the MCP server."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MTG MCP Server')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Set logging level based on --debug flag
    if args.debug:
        logging.getLogger('mtg-mcp').setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    logger.info("="*50)
    logger.info("Starting MTG MCP server...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Logging level: {'DEBUG' if args.debug else 'WARNING'}")
    logger.info("="*50)
    mcp.run()

if __name__ == "__main__":
    main()
