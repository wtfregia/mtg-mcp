"""MTG Context Tools"""
import logging
from typing import Any, Dict

from mtg_mcp.utils import get_banned_cards, get_game_changers, get_rules

logger = logging.getLogger('mtg-mcp')

async def get_context() -> Dict[str, Any]:
    """Get the base context about Magic: The Gathering."""
    logger.info("Tool called: mtg.context.get")
    rules = await get_rules()
    logger.debug("Rules fetched successfully")

    return {
        "purpose": "This tool provides information about Magic: The Gathering card game concepts and rules. It is not intended for generating or modifying code.",
        "role": "Information provider for Magic: The Gathering knowledge and game details",
        "game": "Magic: The Gathering",
        "description": "A trading card game where players battle as powerful wizards called planeswalkers",
        "publisher": "Wizards of the Coast",
        "created": 1993,
        "rules_version": f"Using official Magic: The Gathering Comprehensive Rules (last updated: {rules.get('last_updated', 'unknown')})",
        "basic_concepts": {
            "mana": "The magical energy used to cast spells",
            "colors": ["White", "Blue", "Black", "Red", "Green"],
            "deck_construction": "Minimum 60 cards in constructed formats",
            "starting_life": 20
        },
        "available_tools": {
            "mtg.context.get": "Get basic MTG game information",
            "mtg.context.commander": "Get comprehensive Commander/EDH format rules and deck construction requirements",
            "mtg.cardtypes.get": "Get detailed information about card types, subtypes, and supertypes",
            "mtg.rules.get": "Get overview of the comprehensive rules",
            "mtg.rules.search": "Search specific rules by section number or keyword",
            "mtg.ruling.search": "Search for official rulings for a specific card",
            "mtg.combos.search": "Search for Commander format card combinations and interactions",
            "mtg.commander.recommend": "Get top 10 recommended cards for a commander from EDHREC",
            "mtg.commander.brackets": "Get information about Commander power level brackets and criteria",
            "mtg.export.format": "Get the proper format for exporting/importing decklists with quantity notation",
            "mtg.commander.deck": "Validate commanders and gather comprehensive data for generating a legal Commander deck",
            "mtg.archidekt.fetch": "Fetch deck information and card list from an Archidekt deck URL"
        },
        "usage_guidelines": {
            "intended_use": "Answering questions about Magic: The Gathering rules, cards, and concepts using official rules and data",
            "not_intended_for": "Generating code, creating programs, or software development tasks",
            "rules_queries": "Use mtg.rules.search for specific rule lookups"
        }
    }

async def get_commander_context() -> Dict[str, Any]:
    """Get comprehensive information about the Commander/EDH format."""
    logger.info("Tool called: mtg.context.commander")

    # Fetch game changers and banned cards dynamically
    game_changers_data = await get_game_changers()
    banned_cards_data = await get_banned_cards()

    return {
        "format": "Commander (also known as EDH - Elder Dragon Highlander)",
        "description": "A casual multiplayer format for Magic: The Gathering focused on social play and creative deck building",
        "deck_construction": {
            "total_cards": {
                "requirement": "EXACTLY 100 cards",
                "includes_commander": True,
                "note": "This is a strict requirement - decks must be exactly 100 cards, including the commander(s)"
            },
            "commander": {
                "requirement": "1 legendary creature OR 2 legendary creatures with Partner",
                "role": "Starts the game in the command zone",
                "rules": [
                    "Must be a legendary creature (or planeswalker with 'can be your commander' text)",
                    "Can be cast from the command zone",
                    "Returns to command zone if it would go to graveyard or exile (player's choice)",
                    "Costs {2} more for each previous time it was cast from command zone (commander tax)"
                ]
            },
            "singleton": {
                "rule": "Exactly 1 copy of each card (except basic lands)",
                "basic_lands": "Any number of basic lands allowed (Plains, Island, Swamp, Mountain, Forest, Wastes)"
            },
            "color_identity": {
                "critical_rule": "The color identity of your commander STRICTLY LIMITS the color identity of cards allowed in your deck",
                "definition": "A card's color identity includes: mana symbols in casting cost, mana symbols in rules text, and color indicator",
                "enforcement": "You CANNOT include any card with a color identity outside your commander's color identity",
                "examples": {
                    "mono_white_commander": "Can only include cards with white or colorless identity",
                    "azorius_commander": "Can only include white, blue, or colorless cards",
                    "five_color_commander": "Can include cards of any color"
                },
                "important_note": "Even if a card is colorless but has colored mana symbols in its rules text, it has that color identity"
            }
        },
        "gameplay": {
            "starting_life": {
                "amount": 40,
                "note": "Each player starts with 40 life (double the 20 life in standard formats)"
            },
            "player_count": {
                "traditional": "4 players (called a 'pod')",
                "minimum": 2,
                "maximum": 8,
                "optimal": "4 players is the most common and balanced configuration",
                "note": "While you can play with 2-8 players, the format is designed and balanced around 4-player pods"
            },
            "commander_damage": {
                "rule": "If a player takes 21 or more combat damage from a single commander, they lose the game",
                "tracking": "Damage is tracked per commander separately",
                "type": "Only combat damage counts (not damage from abilities)"
            },
            "multiplayer_rules": {
                "turn_order": "Proceeds clockwise around the table",
                "free_for_all": "Last player standing wins",
                "politics": "Negotiation and temporary alliances are part of the format",
                "social_contract": "Focus on fun and interactive gameplay over pure optimization"
            }
        },
        "banned_list": banned_cards_data,
        "game_changers": game_changers_data,
        "philosophy": {
            "social_format": "Commander is designed for social, multiplayer play",
            "rule_0": "Playgroups are encouraged to discuss and modify rules to fit their preferences",
            "power_level_discussion": "Players should discuss deck power levels before playing",
            "fun_over_competition": "The format prioritizes fun, creative play over pure competitive optimization"
        },
        "deck_building_tips": {
            "card_count_breakdown": "Common suggestion: ~35-40 lands, ~10 ramp, ~10 card draw, ~10 removal, ~30-35 other spells",
            "mana_curve": "Commander games tend to go longer, so higher mana curves are viable",
            "interaction": "Include removal and counterspells to interact with opponents",
            "win_conditions": "Have clear ways to win the game in longer multiplayer matches",
            "politics": "Cards that affect multiple players or enable deals can be powerful"
        },
        "resources": {
            "official_rules": "https://mtgcommander.net/",
            "deck_building": "Use mtg.commander.recommend tool for card recommendations",
            "power_levels": "Use mtg.commander.brackets tool for bracket information",
            "combos": "Use mtg.combos.search tool to find card combinations"
        }
    }
