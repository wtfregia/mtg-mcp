"""
Magic: The Gathering Context MCP Server.
This server provides AI chatbots with context about Magic: The Gathering.
"""

import asyncio
import aiohttp
from typing import Dict, Any, List
from mcp.server import fastmcp
from mtgsdk import Card, Type, Subtype, Supertype
import logging
import time
import sys
import argparse
import os

# Set up logging to stderr so VS Code can capture it
# Default to WARNING level, can be overridden with --debug flag
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger('mtg-mcp')

# Rate limiting for API calls (100ms minimum between calls)
_last_api_call_time = {
    'scryfall': 0.0,
    'commanderspellbook': 0.0
}
_api_rate_limit_ms = 100  # Minimum milliseconds between API calls

async def rate_limit_api_call(api_name: str) -> None:
    """
    Ensure at least 100ms has passed since the last API call to the specified API.
    
    Args:
        api_name: Either 'scryfall' or 'commanderspellbook'
    """
    global _last_api_call_time
    current_time = time.time()
    time_since_last_call = (current_time - _last_api_call_time.get(api_name, 0)) * 1000  # Convert to ms
    
    if time_since_last_call < _api_rate_limit_ms:
        sleep_time = (_api_rate_limit_ms - time_since_last_call) / 1000  # Convert back to seconds
        logger.debug(f"Rate limiting {api_name}: sleeping for {sleep_time:.3f}s")
        await asyncio.sleep(sleep_time)
    
    _last_api_call_time[api_name] = time.time()

async def fetch_and_parse_rules() -> Dict[str, Any]:
    """
    Fetch and parse the MTG comprehensive rules.
    """
    rules_url = "https://media.wizards.com/2025/downloads/MagicCompRules%2020250919.txt"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(rules_url) as response:
                text = await response.text()
                
        # Parse rules into sections
        sections = {}
        current_section = None
        current_text = []
        
        for line in text.split('\n'):
            if line.strip().startswith(tuple(str(i) + '.' for i in range(10))):
                # Save previous section
                if current_section and current_text:
                    sections[current_section] = '\n'.join(current_text)
                # Start new section
                current_section = line.strip()
                current_text = [line]
            elif current_section:
                current_text.append(line)
        
        # Add last section
        if current_section and current_text:
            sections[current_section] = '\n'.join(current_text)
            
        return {
            "last_updated": "2025-09-19",
            "sections": sections
        }
    except Exception:
        return {
            "error": "Could not fetch current rules",
            "last_updated": "2025-09-19"
        }

# Initialize MCP server with debug mode
mcp = fastmcp.FastMCP("mtg-context", debug=True)
logger.info("MCP Server initialized")

# Global rules cache
_rules_cache = None

async def get_rules() -> Dict[str, Any]:
    """Get and cache the comprehensive rules"""
    global _rules_cache
    if _rules_cache is None:
        _rules_cache = await fetch_and_parse_rules()
    return _rules_cache

# Global game changers cache
_game_changers_cache = None

# Global banned cards cache
_banned_cards_cache = None

async def fetch_banned_cards() -> Dict[str, Any]:
    """
    Fetch the list of cards banned in Commander format from Scryfall.
    """
    url = "https://api.scryfall.com/cards/search?q=banned:commander&unique=cards&order=name"
    try:
        async with aiohttp.ClientSession() as session:
            banned_cards = []
            next_page = url
            
            # Scryfall paginates results, so we need to follow the next_page links
            while next_page:
                # Rate limit before API call
                await rate_limit_api_call('scryfall')
                
                async with session.get(next_page) as response:
                    if response.status != 200:
                        return {
                            "error": "Could not fetch banned cards list",
                            "status": response.status
                        }
                    
                    data = await response.json()
                    cards = data.get("data", [])
                    
                    # Extract relevant information for each banned card
                    for card in cards:
                        card_info = {
                            "name": card.get("name", ""),
                            "type_line": card.get("type_line", ""),
                            "mana_cost": card.get("mana_cost", ""),
                            "cmc": card.get("cmc", 0),
                            "color_identity": card.get("color_identity", []),
                            "oracle_text": card.get("oracle_text", ""),
                            "scryfall_uri": card.get("scryfall_uri", "")
                        }
                        banned_cards.append(card_info)
                    
                    # Check if there's a next page
                    next_page = data.get("next_page")
            
            # Sort alphabetically by name
            banned_cards.sort(key=lambda x: x.get("name", ""))
            
            # Extract just card names for simple list
            card_names = [card["name"] for card in banned_cards]
            
            return {
                "source": "Scryfall API",
                "description": "Cards banned in the Commander format",
                "banned_cards": card_names,
                "banned_cards_with_details": banned_cards,
                "total_banned": len(card_names),
                "last_fetched": "dynamic",
                "note": "This list is automatically updated from Scryfall's database",
                "reference": "https://mtgcommander.net for official Commander ban list"
            }
    except Exception as e:
        logger.error(f"Failed to fetch banned cards: {e}")
        return {
            "error": "Could not fetch banned cards list",
            "details": str(e),
            "source": "https://api.scryfall.com/cards/search?q=banned:commander"
        }

async def get_banned_cards() -> Dict[str, Any]:
    """Get and cache the banned cards list"""
    global _banned_cards_cache
    if _banned_cards_cache is None:
        _banned_cards_cache = await fetch_banned_cards()
    return _banned_cards_cache

async def fetch_game_changers() -> Dict[str, Any]:
    """
    Fetch and parse the game changers list from EDHREC JSON API.
    """
    url = "https://json.edhrec.com/pages/top/game-changers.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return {"error": "Could not fetch game changers list", "status": response.status}
                
                data = await response.json()
                
                # Extract card data from EDHREC JSON structure
                container = data.get("container", {})
                json_dict = container.get("json_dict", {})
                cardlists = json_dict.get("cardlists", [])
                
                game_changers = []
                seen = set()
                
                # Process each cardlist (should just be one for game changers)
                for cardlist in cardlists:
                    cardviews = cardlist.get("cardviews", [])
                    
                    for card in cardviews:
                        card_name = card.get("name", "")
                        if card_name and card_name not in seen:
                            game_changer_info = {
                                "name": card_name,
                                "num_decks": card.get("num_decks", 0),
                                "inclusion_percentage": None,
                                "synergy": card.get("synergy"),
                                "label": card.get("label", "")
                            }
                            
                            # Calculate inclusion percentage if data available
                            potential_decks = card.get("potential_decks", 0)
                            if potential_decks > 0:
                                game_changer_info["inclusion_percentage"] = round(
                                    (game_changer_info["num_decks"] / potential_decks) * 100, 1
                                )
                            
                            game_changers.append(game_changer_info)
                            seen.add(card_name)
                
                # Fetch additional Scryfall data for each card (in batches to respect rate limits)
                for card_info in game_changers:
                    card_name = card_info["name"]
                    try:
                        # Rate limit before each Scryfall call
                        await rate_limit_api_call('scryfall')
                        
                        card_search_url = f"https://api.scryfall.com/cards/named?exact={card_name}"
                        async with session.get(card_search_url) as scryfall_response:
                            if scryfall_response.status == 200:
                                scryfall_data = await scryfall_response.json()
                                
                                # Add useful Scryfall information
                                card_info["type_line"] = scryfall_data.get("type_line", "")
                                card_info["mana_cost"] = scryfall_data.get("mana_cost", "")
                                card_info["cmc"] = scryfall_data.get("cmc", 0)
                                card_info["oracle_text"] = scryfall_data.get("oracle_text", "")
                                card_info["color_identity"] = scryfall_data.get("color_identity", [])
                                
                                # Add pricing information
                                prices = scryfall_data.get("prices", {})
                                card_info["prices"] = {
                                    "usd": prices.get("usd"),
                                    "usd_foil": prices.get("usd_foil"),
                                    "eur": prices.get("eur")
                                }
                                
                                card_info["scryfall_uri"] = scryfall_data.get("scryfall_uri", "")
                                card_info["image_uris"] = scryfall_data.get("image_uris", {})
                            else:
                                # If Scryfall lookup fails, just set defaults
                                logger.debug(f"Could not fetch Scryfall data for {card_name}")
                                card_info["type_line"] = ""
                                card_info["mana_cost"] = ""
                                card_info["cmc"] = 0
                                card_info["oracle_text"] = ""
                                card_info["color_identity"] = []
                                card_info["prices"] = None
                    except Exception as e:
                        logger.debug(f"Failed to fetch Scryfall data for {card_name}: {e}")
                        # Continue processing other cards even if one fails
                        continue
                
                # Sort by popularity (num_decks)
                game_changers.sort(key=lambda x: x.get("num_decks", 0), reverse=True)
                
                # Extract just card names for simple list
                card_names = [gc["name"] for gc in game_changers]
                
                return {
                    "source": "EDHREC JSON API",
                    "description": "Game changers are cards that dramatically warp commander games. They are part of the bracket system used by Wizards of the Coast to help players identify deck power levels.",
                    "cards": card_names,
                    "cards_with_details": game_changers,
                    "total_cards": len(card_names),
                    "last_fetched": "dynamic",
                    "bracket_guidelines": {
                        "bracket_1_2": "Generally avoid game changers (Casual/Exhibition and Core decks)",
                        "bracket_3": "Generally run up to 3 game changers (Upgraded decks)",
                        "bracket_4_5": "Unrestricted on game changers (Optimized and cEDH decks)"
                    },
                    "note": "These cards significantly impact deck power level and should be discussed in Rule 0 conversations. This list is maintained by Wizards of the Coast and the Commander Format Panel.",
                    "url": url,
                    "web_url": "https://edhrec.com/top/game-changers"
                }
    except Exception as e:
        logger.error(f"Failed to fetch game changers: {e}")
        return {
            "error": "Could not fetch game changers list",
            "details": str(e),
            "source": "https://json.edhrec.com/pages/top/game-changers.json"
        }

async def get_game_changers() -> Dict[str, Any]:
    """Get and cache the game changers list"""
    global _game_changers_cache
    if _game_changers_cache is None:
        _game_changers_cache = await fetch_game_changers()
    return _game_changers_cache

@mcp.tool("mtg-rules-get")
async def get_rules_info() -> Dict[str, Any]:
    """
    Get information from the MTG comprehensive rules.
    """
    rules = await get_rules()
    if "error" in rules:
        return {
            "error": "Rules are currently unavailable",
            "last_updated": rules["last_updated"]
        }
    
    return {
        "last_updated": rules["last_updated"],
        "sections": {
            "Game Concepts": "1. Game Concepts",
            "Parts of the Game": "2. Parts of the Game",
            "Turn Structure": "3. Turn Structure",
            "Spells, Abilities, and Effects": "4. Spells, Abilities, and Effects",
            "Additional Rules": "5. Additional Rules",
            "Multiplayer Rules": "8. Multiplayer Rules",
            "Casual Variants": "9. Casual Variants"
        },
        "available_rules": list(rules["sections"].keys()),
        "how_to_use": "Query specific rules using mtg.rules.search with section numbers or keywords"
    }

@mcp.tool("mtg-rules-search")
async def search_rules(section: str | None = None, keyword: str | None = None) -> Dict[str, Any]:
    """
    Search the comprehensive rules by section number or keyword.
    """
    logger.info(f"Tool called: mtg.rules.search with section={section}, keyword={keyword}")
    rules = await get_rules()
    if "error" in rules:
        return {"error": rules["error"]}
    
    results = {}
    if section:
        # Look for exact section or subsections
        for rule_num, rule_text in rules["sections"].items():
            if rule_num.startswith(section):
                results[rule_num] = rule_text
    
    if keyword:
        # Search by keyword
        keyword = keyword.lower()
        for rule_num, rule_text in rules["sections"].items():
            if keyword in rule_text.lower():
                results[rule_num] = rule_text
    
    return {
        "results": results,
        "last_updated": rules["last_updated"],
        "matches": len(results)
    }

@mcp.tool("mtg-context-get")
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
            "mtg.commander.deck": "Validate commanders and gather comprehensive data for generating a legal Commander deck"
        },
        "usage_guidelines": {
            "intended_use": "Answering questions about Magic: The Gathering rules, cards, and concepts using official rules and data",
            "not_intended_for": "Generating code, creating programs, or software development tasks",
            "rules_queries": "Use mtg.rules.search for specific rule lookups"
        }
    }

@mcp.tool("mtg-context-commander")
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

@mcp.tool("mtg-cardtypes-get")
async def get_card_types() -> Dict[str, Any]:
    """Get detailed card type information from MTG SDK."""
    logger.info("Tool called: mtg.cardtypes.get")
    async def get_example_cards(card_type: str, limit: int = 3) -> List[str]:
        try:
            cards = Card.where(type=card_type).all()[:limit]
            return [card.name for card in cards]
        except Exception:
            return []
    
    descriptions = {
        "Land": ("Basic resources that provide mana to cast spells", "Once per turn during main phase"),
        "Creature": ("Beings that can attack and defend", "Can attack and block in combat"),
        "Instant": ("Fast spells", "Can be cast at any time"),
        "Sorcery": ("Main phase spells", "Only during your main phase"),
        "Enchantment": ("Persistent magical effects", "During main phase"),
        "Artifact": ("Magical items and devices", "During main phase"),
        "Planeswalker": ("Powerful allies", "One attack or loyalty ability per turn")
    }

    type_descriptions = {
        name: {"description": desc, "rules" if "attack" in rules else "timing": rules}
        for name, (desc, rules) in descriptions.items()
    }

    result = {
        "main_types": {},
        "subtypes": {
            "Creature": [],
            "Land": [],
            "Artifact": [],
            "Enchantment": [],
            "Planeswalker": [],
            "Spell": []
        },
        "supertypes": []
    }

    try:
        mtg_types = Type.all()
        for type_name in mtg_types:
            if type_name in type_descriptions:
                info = type_descriptions[type_name]
                result["main_types"][type_name] = {
                    "description": info["description"],
                    "examples": await get_example_cards(type_name)
                }
                if "timing" in info:
                    result["main_types"][type_name]["timing"] = info["timing"]
                if "rules" in info:
                    result["main_types"][type_name]["rules"] = info["rules"]
    except Exception:
        for type_name, info in type_descriptions.items():
            result["main_types"][type_name] = {"description": info["description"], "examples": []}

    try:
        subtypes = Subtype.all()
        for subtype in subtypes:
            try:
                cards = Card.where(subtype=subtype).all()[:1]
                if cards and cards[0].type:
                    for category in result["subtypes"].keys():
                        if category.lower() in cards[0].type.lower():
                            if subtype not in result["subtypes"][category]:
                                result["subtypes"][category].append(subtype)
                            break
            except Exception:
                continue
    except Exception:
        pass

    try:
        result["supertypes"] = Supertype.all()
    except Exception:
        result["supertypes"] = ["Basic", "Legendary", "Snow", "World", "Ongoing"]

    return result

@mcp.tool("mtg-ruling-search")
async def search_rulings(card_name: str) -> Dict[str, Any]:
    """
    Search for official rulings for a specific Magic: The Gathering card.
    
    Args:
        card_name: The name of the card to search for rulings.
    
    Returns:
        Dictionary containing ruling information or an error message.
    """
    logger.info(f"Tool called: mtg.ruling.search with card_name={card_name}")
    
    # Use Scryfall API to get card rulings
    # First, search for the card to get its ID
    search_url = f"https://api.scryfall.com/cards/named?fuzzy={card_name}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Rate limit before first API call
            await rate_limit_api_call('scryfall')
            
            # Get card data
            async with session.get(search_url) as response:
                if response.status == 404:
                    return {
                        "card_name": card_name,
                        "error": f"Card '{card_name}' not found",
                        "suggestion": "Check the spelling or try a different card name"
                    }
                elif response.status != 200:
                    return {
                        "error": f"Failed to fetch card information for '{card_name}'",
                        "status_code": response.status
                    }
                
                card_data = await response.json()
                card_id = card_data.get("id")
                actual_name = card_data.get("name")
                oracle_text = card_data.get("oracle_text", "")
                type_line = card_data.get("type_line", "")
                
                if not card_id:
                    return {
                        "error": "Could not retrieve card ID",
                        "card_name": card_name
                    }
            
            # Rate limit before second API call
            await rate_limit_api_call('scryfall')
            
            # Get rulings for the card
            rulings_url = f"https://api.scryfall.com/cards/{card_id}/rulings"
            async with session.get(rulings_url) as rulings_response:
                if rulings_response.status != 200:
                    return {
                        "card_name": actual_name,
                        "rulings": [],
                        "total_rulings": 0,
                        "message": "No rulings available for this card"
                    }
                
                rulings_data = await rulings_response.json()
                rulings = rulings_data.get("data", [])
                
                formatted_rulings = []
                for ruling in rulings:
                    formatted_rulings.append({
                        "date": ruling.get("published_at", ""),
                        "source": ruling.get("source", ""),
                        "text": ruling.get("comment", "")
                    })
                
                return {
                    "card_name": actual_name,
                    "type_line": type_line,
                    "oracle_text": oracle_text,
                    "rulings": formatted_rulings,
                    "total_rulings": len(formatted_rulings),
                    "source": "Scryfall API",
                    "scryfall_url": card_data.get("scryfall_uri", "")
                }
                
    except Exception as e:
        return {
            "error": "Failed to fetch rulings",
            "card_name": card_name,
            "details": str(e)
        }

@mcp.tool("mtg-combos-search")
async def search_combos(card_name: str) -> Dict[str, Any]:
    """
    Search for Commander combos involving a specific card using the Commander Spellbook API.
    
    Args:
        card_name: The name of the card to search for combos.
    
    Returns:
        Dictionary containing combo information or an error message.
    """
    logger.info(f"Tool called: mtg.combos.search with card_name={card_name}")
    
    api_url = f"https://backend.commanderspellbook.com/variants/?q=card:{card_name}+legal:commander&limit=5"
    
    try:
        # Rate limit before API call
        await rate_limit_api_call('commanderspellbook')
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # The API returns paginated results
                    variants = data.get("results", [])
                    
                    if not variants:
                        return {
                            "card_name": card_name,
                            "total_combos": 0,
                            "message": f"No combos found involving '{card_name}'",
                            "combos": []
                        }
                    
                    # Format the combo data (limit to 5)
                    formatted_combos = []
                    for variant in variants[:5]:
                        # Extract card names from the uses array
                        card_names = []
                        for card_usage in variant.get("uses", []):
                            card_info = card_usage.get("card", {})
                            if isinstance(card_info, dict):
                                card_names.append(card_info.get("name", ""))
                            elif isinstance(card_info, str):
                                card_names.append(card_info)
                        
                        # Extract result/feature names from produces array
                        result_names = []
                        for feature in variant.get("produces", []):
                            feature_info = feature.get("feature", {})
                            if isinstance(feature_info, dict):
                                result_names.append(feature_info.get("name", ""))
                            elif isinstance(feature_info, str):
                                result_names.append(feature_info)
                        
                        formatted_combo = {
                            "id": variant.get("id", ""),
                            "cards_used": card_names,
                            "color_identity": variant.get("identity", ""),
                            "prerequisites": variant.get("easyPrerequisites", "") or variant.get("notablePrerequisites", ""),
                            "steps": variant.get("description", ""),
                            "results": result_names,
                            "mana_needed": variant.get("manaNeeded", ""),
                            "mana_value_needed": variant.get("manaValueNeeded", 0),
                            "popularity": variant.get("popularity"),
                            "status": variant.get("status", "")
                        }
                        formatted_combos.append(formatted_combo)

                    return {
                        "card_name": card_name,
                        "total_combos": data.get("count", len(variants)),
                        "combos_returned": len(formatted_combos),
                        "combos": formatted_combos,
                        "query_info": {
                            "api_version": "v1",
                            "source": "Commander Spellbook API",
                            "limit": 5
                        }
                    }
                else:
                    return {
                        "error": f"Failed to fetch combos for '{card_name}'",
                        "status_code": response.status
                    }
    except Exception as e:
        return {
            "error": "Failed to fetch combos",
            "card_name": card_name,
            "details": str(e)
        }

@mcp.tool("mtg-commander-recommend")
async def recommend_commander_cards(card_name: str, include_context: bool = True) -> Dict[str, Any]:
    """
    Get top 10 recommended cards for a commander from EDHREC.
    
    Args:
        card_name: The name of the card (assumed to be a commander).
        include_context: If True, also includes Commander format context and bracket information.
    
    Returns:
        Dictionary containing top recommended cards or an error message.
    """
    logger.info(f"Tool called: mtg.commander.recommend with card_name={card_name}, include_context={include_context}")
    
    # First, get the exact card name from Scryfall
    search_url = f"https://api.scryfall.com/cards/named?fuzzy={card_name}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Rate limit before Scryfall API call
            await rate_limit_api_call('scryfall')
            
            # Get exact card name
            async with session.get(search_url) as response:
                if response.status == 404:
                    return {
                        "card_name": card_name,
                        "error": f"Card '{card_name}' not found",
                        "suggestion": "Check the spelling or try a different card name"
                    }
                elif response.status != 200:
                    return {
                        "error": f"Failed to fetch card information for '{card_name}'",
                        "status_code": response.status
                    }
                
                card_data = await response.json()
                exact_name = card_data.get("name", card_name)
                type_line = card_data.get("type_line", "")
                
                # Check if it's a legendary creature (potential commander)
                is_legendary = "Legendary" in type_line
                is_creature = "Creature" in type_line
                
            # Convert card name to EDHREC URL format (lowercase, hyphens, remove special chars)
            url_name = exact_name.lower().replace(" ", "-").replace(",", "").replace("'", "")
            
            # Try EDHREC commanders endpoint
            edhrec_url = f"https://json.edhrec.com/pages/commanders/{url_name}.json"
            
            # Rate limit before EDHREC API call (treat as separate API)
            # Using a small delay since EDHREC is a different service
            await asyncio.sleep(0.1)  # 100ms delay
            
            async with session.get(edhrec_url) as edhrec_response:
                if edhrec_response.status != 200:
                    # Try the cards endpoint as fallback
                    edhrec_url = f"https://json.edhrec.com/pages/cards/{url_name}.json"
                    await asyncio.sleep(0.1)
                    
                    async with session.get(edhrec_url) as cards_response:
                        if cards_response.status != 200:
                            return {
                                "card_name": exact_name,
                                "error": f"No EDHREC data found for '{exact_name}'",
                                "is_legendary": is_legendary,
                                "is_creature": is_creature,
                                "suggestion": "This card may not have EDHREC commander data available"
                            }
                        edhrec_data = await cards_response.json()
                else:
                    edhrec_data = await edhrec_response.json()
            
            # Parse EDHREC data
            container = edhrec_data.get("container", {})
            json_dict = container.get("json_dict", {})
            
            # Get card information
            card_info = json_dict.get("card", {})
            num_decks = card_info.get("num_decks", 0)
            
            # Get top cards
            cardlists = container.get("json_dict", {}).get("cardlists", [])
            top_cards = []
            
            # Look for "Top Cards" or similar sections
            for cardlist in cardlists:
                header = cardlist.get("header", "").lower()
                # Look for top cards, high synergy cards, or new cards
                if any(keyword in header for keyword in ["top cards", "high synergy", "creatures", "artifacts", "enchantments", "instants", "sorceries", "planeswalkers"]):
                    cards = cardlist.get("cardviews", [])
                    for card in cards[:10]:  # Limit to 10 per category
                        card_dict = {
                            "name": card.get("name", ""),
                            "sanitized_name": card.get("sanitized_wo", ""),
                            "label": card.get("label", ""),
                            "num_decks": card.get("num_decks", 0),
                            "potential_decks": card.get("potential_decks", 0),
                            "synergy": card.get("synergy"),
                            "category": cardlist.get("header", "")
                        }
                        
                        # Calculate inclusion percentage if data available
                        if card_dict["potential_decks"] > 0:
                            card_dict["inclusion_percentage"] = round(
                                (card_dict["num_decks"] / card_dict["potential_decks"]) * 100, 1
                            )
                        
                        top_cards.append(card_dict)
                    
                    # If we have enough cards, stop
                    if len(top_cards) >= 10:
                        break
            
            # Sort by num_decks and take top 10
            top_cards.sort(key=lambda x: x.get("num_decks", 0), reverse=True)
            top_10 = top_cards[:10]
            
            # Fetch pricing information for each card from Scryfall
            for card_dict in top_10:
                card_search_name = card_dict["name"]
                try:
                    # Rate limit before each Scryfall call
                    await rate_limit_api_call('scryfall')
                    
                    card_search_url = f"https://api.scryfall.com/cards/named?exact={card_search_name}"
                    async with session.get(card_search_url) as price_response:
                        if price_response.status == 200:
                            price_data = await price_response.json()
                            prices = price_data.get("prices", {})
                            
                            # Add pricing information
                            card_dict["prices"] = {
                                "usd": prices.get("usd"),
                                "usd_foil": prices.get("usd_foil"),
                                "eur": prices.get("eur")
                            }
                            
                            # Also add mana cost for reference
                            card_dict["mana_cost"] = price_data.get("mana_cost", "")
                            card_dict["cmc"] = price_data.get("cmc", 0)
                            card_dict["type_line"] = price_data.get("type_line", "")
                        else:
                            # If we can't get pricing, set as None
                            card_dict["prices"] = None
                            card_dict["mana_cost"] = ""
                            card_dict["cmc"] = 0
                except Exception as e:
                    logger.debug(f"Failed to fetch pricing for {card_search_name}: {e}")
                    card_dict["prices"] = None
                    card_dict["mana_cost"] = ""
                    card_dict["cmc"] = 0
            
            result = {
                "card_name": exact_name,
                "type_line": type_line,
                "is_legendary_creature": is_legendary and is_creature,
                "total_decks": num_decks,
                "top_cards": top_10,
                "total_recommendations": len(top_cards),
                "source": "EDHREC",
                "edhrec_url": f"https://edhrec.com/commanders/{url_name}" if is_legendary and is_creature else f"https://edhrec.com/cards/{url_name}"
            }
            
            # If include_context is True, call the other tools and add their data
            if include_context:
                logger.info("Fetching additional Commander context and bracket information")
                
                # Call the other tool functions directly
                commander_context = await get_commander_context()
                commander_brackets = await get_commander_brackets()
                
                # Add the additional context to the result
                result["commander_context"] = commander_context
                result["commander_brackets"] = commander_brackets
                result["note"] = "Additional Commander format context and bracket information included"
            
            return result
            
    except Exception as e:
        logger.error(f"Failed to fetch EDHREC recommendations: {e}")
        return {
            "error": "Failed to fetch EDHREC recommendations",
            "card_name": card_name,
            "details": str(e)
        }

@mcp.tool("mtg-commander-brackets")
async def get_commander_brackets() -> Dict[str, Any]:
    """
    Get information about Commander/EDH brackets and their criteria.
    
    Returns:
        Dictionary containing bracket information, criteria, and guidelines.
    """
    logger.info("Tool called: mtg.commander.brackets")
    
    return {
        "system": "Commander Bracket System",
        "description": "A tier system for Commander decks to help players find appropriately matched games",
        "source": "Official Commander Rules Committee and CAG guidance",
        "last_updated": "2025",
        "total_brackets": 5,
        "brackets": {
            "Bracket 1": {
                "name": "Bracket 1 (Casual)",
                "power_level": "Lowest power level",
                "description": "Casual builds focused on fun interactions and social play",
                "characteristics": [
                    "Budget-friendly builds (typically under $100)",
                    "Focuses on thematic gameplay over optimization",
                    "Win conditions are straightforward and telegraphed",
                    "Limited tutors and fast mana",
                    "Games typically last 10-15+ turns",
                    "Minimal combo presence"
                ],
                "example_strategies": [
                    "Thematic decks (e.g., chair tribal, sea creatures)",
                    "Beginner-friendly strategies",
                    "Budget-conscious builds"
                ],
                "banned_effects": [],
                "typical_cards": [
                    "Commander's Sphere",
                    "Rampant Growth",
                    "Sol Ring",
                    "Command Tower"
                ]
            },
            "Bracket 2": {
                "name": "Bracket 2 (Focused/Optimized Casual)",
                "power_level": "Mid-low power",
                "description": "Upgraded casual decks with clear strategies and some powerful cards",
                "characteristics": [
                    "Focused game plan with synergies",
                    "Some efficient tutors and card advantage",
                    "Moderate budget ($40-$300)",
                    "Some powerful staples but not fully optimized",
                    "May include some infinite combos but not as primary win condition",
                    "Games typically last 8-12 turns",
                    "Interaction and removal present but not excessive"
                ],
                "example_strategies": [
                    "Optimized tribal decks",
                    "Value-focused strategies",
                    "Aristocrats",
                    "Landfall",
                    "+1/+1 counters"
                ],
                "notable_inclusions": [
                    "Efficient card draw engines",
                    "Some mana-positive rocks",
                    "Board wipes",
                    "Targeted removal",
                    "Very few non-land tutors"
                ],
                "typical_cards": [
                    "Cultivate",
                    "Chaos Warp",
                    "Charms",
                    "Rampant Growth",
                    "Signets",
                    "Wrath of God",
                    "Evolving Wilds",
                    "Tangolands",
                    "Basic Lands",
                    "Abrade"
                ]
            },
            "Bracket 3": {
                "name": "Bracket 3 (Mid-High Power)",
                "power_level": "Mid-high power",
                "description": "Optimized decks with powerful cards and combos, but not fully competitive",
                "characteristics": [
                    "Well-tuned strategy with consistent game plan",
                    "Access to powerful cards and efficient tutors",
                    "Moderate to higher budget ($300-$900)",
                    "No fast mana (Mana Crypt, Mox Diamond, etc.)",
                    "Combo lines present but not fully streamlined",
                    "Games typically last 7-9 turns",
                    "Good interaction package",
                    "Efficient but not maximum optimization"
                ],
                "example_strategies": [
                    "Optimized combo decks",
                    "Powerful value engines",
                    "Efficient stax strategies",
                    "Storm-adjacent builds"
                ],
                "notable_inclusions": [
                    "Several tutors (4-8)",
                    "No fast mana",
                    "Powerful combos",
                    "Efficient interaction",
                    "Strong card advantage"
                ],
                "typical_cards": [
                    "Fetchlands",
                    "Mana Dorks and Rocks",
                    "Talismans",
                    "Mystic Remora",
                    "Painlands",
                    "Swan Song",
                    "Llanowar Elves",
                    "Three Tree City",
                    "Reanimate",
                    "Triomes",
                    "Battlebond Lands",
                    "Blasphemous Act",
                    "Untimely Malfunction"
                ]
            },
            "Bracket 4": {
                "name": "Bracket 4 (High Power/Optimized)",
                "power_level": "High power",
                "description": "Highly optimized decks approaching competitive levels with powerful combos and comprehensive interaction",
                "characteristics": [
                    "Highly tuned strategy with backup plans",
                    "Extensive tutors and card selection",
                    "Higher budget ($900+)",
                    "Full fast mana package available",
                    "Multiple infinite combo lines",
                    "Games typically last 5-8 turns",
                    "Comprehensive interaction and protection",
                    "Near-optimal card choices",
                    "Compact, efficient win conditions"
                ],
                "example_strategies": [
                    "Streamlined combo decks",
                    "Advanced stax strategies",
                    "Storm",
                    "Turbo strategies",
                    "High-efficiency control"
                ],
                "notable_inclusions": [
                    "Extensive tutor suite (8-10+)",
                    "Fast mana package",
                    "Free counterspells",
                    "Reserved list power cards",
                    "Multiple combo lines",
                    "Advanced stax pieces"
                ],
                "typical_cards": [
                    "Game Changers",
                    "Force of Will",
                    "Vampiric Tutor",
                    "Gaea's Cradle",
                    "Mox Diamond",
                    "Time Spiral",
                    "Deadly Rollick",
                    "Rhystic Study",
                    "Deflecting Swat",
                    "Shocklands",
                    "Dual Lands",
                    "Three Tree City",
                    "Nykthos, Shrine to Nyx",
                    "Orcish Bowmasters",
                    "Strip Mine",
                    "Channel Lands",
                    "Jeska's Will",
                    "Vandalblast",
                    "Esper Sentinel",
                    "Smothering Tithe",
                    "Teferi's Protection"
                ]
            },
            "Bracket 5": {
                "name": "Bracket 5 (Competitive EDH/cEDH)",
                "power_level": "Maximum power",
                "description": "Fully optimized competitive decks designed to win as fast as possible",
                "characteristics": [
                    "Every card choice optimized for efficiency",
                    "Extensive tutor suite",
                    "No budget constraints",
                    "Full fast mana package",
                    "Multiple compact combo wins",
                    "Games typically last 3-6 turns",
                    "Maximum interaction density",
                    "Wins turns 1-4 with protection",
                    "Every slot optimized"
                ],
                "example_strategies": [
                    "Turbo Naus (Ad Nauseam)",
                    "Consultation Oracle (Thassa's Oracle combo)",
                    "Food Chain strategies",
                    "Breach lines",
                    "Storm combos",
                    "Stax lock strategies"
                ],
                "notable_inclusions": [
                    "Full suite of tutors (8-12+)",
                    "All fast mana available",
                    "Free interaction (Force of Will, Force of Negation, Pact of Negation)",
                    "Reserved list power",
                    "Compact 2-card combos",
                    "Mana-positive rocks"
                ],
                "typical_cards": [
                    "Thassa's Oracle",
                    "Demonic Consultation",
                    "Tainted Pact",
                    "Mox Diamond",
                    "Chrome Mox",
                    "Timetwister",
                    "The Tabernacle at Pendrell Vale",
                    "Imperial Seal"
                ],
                "competitive_commanders": [
                    "Kinnan, Bonder Prodigy",
                    "Tymna the Weaver + Kraum",
                    "Kenrith, the Returned King",
                    "Najeela, the Blade-Blossom",
                    "Winota, Joiner of Forces"
                ]
            }
        },
        "guidelines": {
            "rule_0_conversation": "Players should discuss power levels and expectations before the game",
            "deck_disclosure": "Be honest about your deck's power level and strategy",
            "adjustment_encouraged": "Players are encouraged to adjust power levels to match their playgroup",
            "bracket_flexibility": "Some decks may fall between brackets - communicate clearly",
            "social_contract": "Commander is a social format - prioritize fun for all players"
        },
        "key_indicators": {
            "fast_mana": {
                "description": "Artifacts that produce more mana than they cost",
                "examples": ["Mana Crypt", "Mox Diamond", "Chrome Mox", "Jeweled Lotus", "Lotus Petal"],
                "impact": "Enables faster wins and more explosive plays"
            },
            "tutors": {
                "description": "Cards that search library for specific cards",
                "examples": ["Demonic Tutor", "Vampiric Tutor", "Imperial Seal", "Enlightened Tutor"],
                "impact": "Increases consistency and enables combo strategies"
            },
            "free_interaction": {
                "description": "Counterspells and removal that don't cost mana",
                "examples": ["Force of Will", "Force of Negation", "Fierce Guardianship", "Pact of Negation"],
                "impact": "Allows interaction while developing board"
            },
            "compact_combos": {
                "description": "2-card infinite combos",
                "examples": ["Thassa's Oracle + Demonic Consultation", "Kiki-Jiki + Zealous Conscripts"],
                "impact": "Enables quick wins with tutors"
            },
            "stax_effects": {
                "description": "Cards that restrict opponents' ability to play",
                "examples": ["Winter Orb", "Stasis", "Null Rod", "Rule of Law"],
                "impact": "Slows game and can lock opponents out"
            }
        },
        "reference_url": "https://moxfield.com/commanderbrackets",
        "note": "Brackets are guidelines, not strict rules. Communication with your playgroup is essential."
    }

@mcp.tool("mtg-export-format")
async def get_export_format() -> Dict[str, Any]:
    """
    Get information about the proper format for exporting/importing Magic: The Gathering decklists.
    
    Returns:
        Dictionary containing deck export format guidelines and examples.
    """
    logger.info("Tool called: mtg.export.format")
    
    return {
        "format_name": "Standard Decklist Format",
        "description": "The standard format for importing and exporting Magic: The Gathering decklists",
        "format_structure": {
            "pattern": "[quantity]x [Card Name]",
            "example": "1x Sol Ring",
            "note": "Each card on a new line with quantity followed by 'x' and the card name"
        },
        "rules": {
            "singleton_cards": {
                "description": "Non-basic lands and other cards that follow singleton rule",
                "format": "1x [Card Name]",
                "examples": [
                    "1x Sol Ring",
                    "1x Command Tower",
                    "1x Reliquary Tower",
                    "1x Lightning Bolt"
                ],
                "note": "In Commander format, you can only have 1 copy of each card (except basic lands)"
            },
            "basic_lands": {
                "description": "Basic lands are the only cards allowed to have multiple copies in Commander",
                "allowed_basic_lands": [
                    "Plains",
                    "Island",
                    "Swamp",
                    "Mountain",
                    "Forest"
                ],
                "format": "[quantity]x [Basic Land Name]",
                "examples": [
                    "10x Island",
                    "15x Plains",
                    "20x Mountain",
                    "12x Swamp",
                    "8x Forest"
                ],
                "important_note": "Basic lands can be stacked (multiple copies allowed). Snow-covered basics and Wastes are also basic lands.",
                "snow_covered_basics": [
                    "Snow-Covered Plains",
                    "Snow-Covered Island",
                    "Snow-Covered Swamp",
                    "Snow-Covered Mountain",
                    "Snow-Covered Forest"
                ],
                "other_basics": ["Wastes"]
            }
        },
        "complete_example": {
            "description": "Example of a complete Commander decklist export format",
            "decklist": [
                "1x Atraxa, Praetors' Voice",
                "1x Sol Ring",
                "1x Arcane Signet",
                "1x Command Tower",
                "1x Exotic Orchard",
                "1x Cyclonic Rift",
                "1x Swords to Plowshares",
                "1x Beast Within",
                "1x Path to Exile",
                "1x Rhystic Study",
                "5x Plains",
                "5x Island",
                "5x Swamp",
                "5x Forest"
            ],
            "note": "This shows 15 cards as an example. A complete Commander deck has exactly 100 cards including the commander."
        },
        "formatting_guidelines": {
            "card_names": "Use the exact card name as printed",
            "capitalization": "Use proper capitalization for card names",
            "special_characters": "Include all apostrophes, commas, and special characters in card names",
            "double_faced_cards": "Use the front face name for double-faced cards",
            "split_cards": "Use the full name with // separator (e.g., 'Fire // Ice')",
            "no_comments": "DO NOT include any comments, headers, section dividers, or explanatory text in the decklist output",
            "no_blank_lines": "DO NOT include blank lines between cards - each line should contain exactly one card entry",
            "strict_format": "ONLY output lines in the format '[quantity]x [Card Name]' - nothing else"
        },
        "critical_formatting_rules": {
            "DO_NOT_INCLUDE": [
                "Comments (e.g., '# This is a comment' or '// Comment')",
                "Section headers (e.g., 'Creatures:', 'Lands:', 'Artifacts:')",
                "Blank lines or spacing between card groups",
                "Explanatory text or notes",
                "Card descriptions or annotations",
                "Mana value or type indicators",
                "Any markdown, HTML, or formatting symbols"
            ],
            "ONLY_INCLUDE": "Lines in the exact format: [quantity]x [Card Name]",
            "WHY": "Deck building tools like Moxfield and Archidekt cannot parse decklists with comments or extra formatting",
            "EXAMPLE_CORRECT": [
                "1x Atraxa, Praetors' Voice",
                "1x Sol Ring",
                "1x Command Tower",
                "10x Island"
            ],
            "EXAMPLE_INCORRECT": [
                "# Commander",
                "1x Atraxa, Praetors' Voice",
                "",
                "// Artifacts",
                "1x Sol Ring // Fast mana",
                "",
                "Lands:",
                "1x Command Tower",
                "10x Island"
            ]
        },
        "commander_specific": {
            "total_cards": "Exactly 100 cards including the commander(s)",
            "commander_notation": "The commander is typically listed first but follows the same 1x format",
            "deck_composition": "After accounting for the commander and lands, the remaining cards should follow the singleton rule (1x each)"
        },
        "validation": {
            "basic_land_check": "Only Plains, Island, Swamp, Mountain, Forest, Snow-Covered variants, and Wastes can have quantities greater than 1",
            "total_count": "Sum of all quantities must equal exactly 100 for Commander format",
            "singleton_enforcement": "All non-basic lands and spells must have quantity of 1",
            "format_check": "Every line must match the pattern '[quantity]x [Card Name]' with no additional text"
        },
        "common_deck_building_tools": [
            "Moxfield",
            "Archidekt",
            "TappedOut",
            "EDHREC",
            "Scryfall"
        ],
        "import_compatibility": {
            "moxfield": "Requires clean format with no comments or headers",
            "archidekt": "Requires clean format with no comments or headers",
            "note": "Most modern deck building tools expect a simple list without any additional formatting"
        }
    }

@mcp.tool("mtg-commander-deck")
async def generate_commander_deck_data(commanders: List[str], bracket: int = 2) -> Dict[str, Any]:
    """
    Validate commanders and gather comprehensive data for generating a legal Commander deck.
    
    Args:
        commanders: List of commander names (1-2 commanders)
        bracket: Target power level bracket (1-5, default: 2)
    
    Returns:
        Dictionary containing validation results, commander data, and deck-building resources
    """
    logger.info(f"Tool called: mtg.commander.deck with commanders={commanders}, bracket={bracket}")
    
    # Validate bracket
    if bracket < 1 or bracket > 5:
        return {
            "error": "Bracket must be between 1 and 5",
            "valid": False,
            "provided_bracket": bracket
        }
    
    if not commanders or len(commanders) == 0:
        return {
            "error": "At least one commander must be provided",
            "valid": False
        }
    
    if len(commanders) > 2:
        return {
            "error": "Maximum of 2 commanders allowed",
            "valid": False,
            "provided_count": len(commanders)
        }
    
    result = {
        "commanders": [],
        "valid": False,
        "validation_results": {},
        "color_identity": [],
        "target_bracket": bracket,
        "deck_building_data": {},
        "format_rules": {},
        "export_format": {},
        "bracket_info": {}
    }
    
    # Fetch commander cards from Scryfall
    commander_cards = []
    
    try:
        async with aiohttp.ClientSession() as session:
            for commander_name in commanders:
                await rate_limit_api_call('scryfall')
                
                search_url = f"https://api.scryfall.com/cards/named?fuzzy={commander_name}"
                async with session.get(search_url) as response:
                    if response.status == 404:
                        return {
                            "error": f"Commander '{commander_name}' not found",
                            "valid": False,
                            "suggestion": "Check the spelling or try a different card name"
                        }
                    elif response.status != 200:
                        return {
                            "error": f"Failed to fetch card information for '{commander_name}'",
                            "status_code": response.status,
                            "valid": False
                        }
                    
                    card_data = await response.json()
                    commander_cards.append(card_data)
    except Exception as e:
        return {
            "error": "Failed to fetch commander information",
            "details": str(e),
            "valid": False
        }
    
    # Validate commanders
    validation_errors = []
    partner_keywords = [
        "Partner",
        "Partner with",
        "Choose a Background",
        "Friends forever",
        "Doctor's companion"
    ]
    
    for card in commander_cards:
        card_info = {
            "name": card.get("name", ""),
            "type_line": card.get("type_line", ""),
            "oracle_text": card.get("oracle_text", ""),
            "color_identity": card.get("color_identity", []),
            "mana_cost": card.get("mana_cost", ""),
            "cmc": card.get("cmc", 0),
            "keywords": card.get("keywords", []),
            "can_be_commander": False,
            "partner_type": None
        }
        
        # Check if card can be a commander
        is_legendary = "Legendary" in card_info["type_line"]
        is_creature = "Creature" in card_info["type_line"]
        has_commander_text = "can be your commander" in card_info["oracle_text"].lower()
        
        if is_legendary and is_creature:
            card_info["can_be_commander"] = True
        elif has_commander_text:
            card_info["can_be_commander"] = True
        else:
            validation_errors.append(f"{card_info['name']} is not a legendary creature and doesn't have 'can be your commander' text")
        
        # Check for partner abilities
        oracle_lower = card_info["oracle_text"].lower()
        for keyword in partner_keywords:
            if keyword.lower() in oracle_lower:
                card_info["partner_type"] = keyword
                break
        
        result["commanders"].append(card_info)
    
    # Validate partner rules if 2 commanders
    if len(commanders) == 2:
        cmd1 = result["commanders"][0]
        cmd2 = result["commanders"][1]
        
        # Check if both can be commanders
        if not cmd1["can_be_commander"] or not cmd2["can_be_commander"]:
            validation_errors.append("Both cards must be able to be commanders")
        
        # Check partner compatibility
        partner_valid = False
        
        # Case 1: Partner with [specific name]
        if cmd1["partner_type"] == "Partner with" and cmd2["name"] in cmd1["oracle_text"]:
            partner_valid = True
        elif cmd2["partner_type"] == "Partner with" and cmd1["name"] in cmd2["oracle_text"]:
            partner_valid = True
        # Case 2: Both have generic Partner
        elif cmd1["partner_type"] == "Partner" and cmd2["partner_type"] == "Partner":
            partner_valid = True
        # Case 3: Choose a Background + Background
        elif cmd1["partner_type"] == "Choose a Background" and "Background" in cmd2["type_line"]:
            partner_valid = True
        elif cmd2["partner_type"] == "Choose a Background" and "Background" in cmd1["type_line"]:
            partner_valid = True
        # Case 4: Friends forever
        elif cmd1["partner_type"] == "Friends forever" and cmd2["partner_type"] == "Friends forever":
            partner_valid = True
        # Case 5: Doctor's companion
        elif cmd1["partner_type"] == "Doctor's companion" and "Doctor" in cmd2["type_line"]:
            partner_valid = True
        elif cmd2["partner_type"] == "Doctor's companion" and "Doctor" in cmd1["type_line"]:
            partner_valid = True
        
        if not partner_valid:
            validation_errors.append(
                f"Commanders are not valid partners. {cmd1['name']} has {cmd1['partner_type'] or 'no partner ability'} "
                f"and {cmd2['name']} has {cmd2['partner_type'] or 'no partner ability'}"
            )
    
    # Determine combined color identity
    all_colors = set()
    for cmd in result["commanders"]:
        all_colors.update(cmd["color_identity"])
    result["color_identity"] = sorted(list(all_colors))
    
    # Set validation status
    result["valid"] = len(validation_errors) == 0
    result["validation_results"] = {
        "passed": len(validation_errors) == 0,
        "errors": validation_errors,
        "commander_count": len(commanders),
        "partner_rules_checked": len(commanders) == 2
    }
    
    if not result["valid"]:
        return result
    
    # If valid, gather deck-building data
    logger.info("Commanders validated successfully. Gathering deck-building data...")
    
    # Load essential context (always loaded)
    logger.info("Loading mtg.rules.get, mtg.context.commander, mtg.commander.brackets, and mtg.export.format...")
    result["format_rules"] = {
        "comprehensive_rules": await get_rules_info(),
        "commander_context": await get_commander_context()
    }
    
    # Load bracket information (always loaded)
    all_brackets = await get_commander_brackets()
    result["bracket_info"] = {
        "all_brackets": all_brackets,
        "target_bracket": bracket,
        "target_bracket_name": f"Bracket {bracket}",
        "target_bracket_details": all_brackets.get("brackets", {}).get(f"Bracket {bracket}", {})
    }
    
    # Load export format (always loaded)
    logger.info("Loading mtg.export.format...")
    result["export_format"] = await get_export_format()
    
    # Load data for each commander
    result["deck_building_data"]["commanders"] = []
    
    for cmd in result["commanders"]:
        commander_name = cmd["name"]
        logger.info(f"Loading deck-building data for {commander_name}...")
        
        commander_data = {
            "name": commander_name,
            "recommendations": None,
            "combos": None,
            "rulings": None
        }
        
        try:
            # Get EDHREC recommendations
            logger.info(f"Fetching EDHREC recommendations for {commander_name}...")
            recommendations = await recommend_commander_cards(commander_name, include_context=False)
            commander_data["recommendations"] = recommendations
        except Exception as e:
            logger.error(f"Failed to fetch recommendations for {commander_name}: {e}")
            commander_data["recommendations"] = {"error": str(e)}
        
        try:
            # Get combos
            logger.info(f"Searching combos for {commander_name}...")
            combos = await search_combos(commander_name)
            commander_data["combos"] = combos
        except Exception as e:
            logger.error(f"Failed to fetch combos for {commander_name}: {e}")
            commander_data["combos"] = {"error": str(e)}
        
        try:
            # Get rulings
            logger.info(f"Fetching rulings for {commander_name}...")
            rulings = await search_rulings(commander_name)
            commander_data["rulings"] = rulings
        except Exception as e:
            logger.error(f"Failed to fetch rulings for {commander_name}: {e}")
            commander_data["rulings"] = {"error": str(e)}
        
        result["deck_building_data"]["commanders"].append(commander_data)
    
    # Add deck generation instructions
    result["deck_generation_instructions"] = {
        "CRITICAL_INSTRUCTIONS": "YOU MUST NOW GENERATE A COMPLETE 100-CARD COMMANDER DECKLIST based on the data provided below. Do not just return this data - USE IT to create an actual decklist.",
        "total_cards": 100,
        "commander_slots": len(commanders),
        "remaining_slots": 100 - len(commanders),
        "target_bracket": bracket,
        "target_bracket_name": f"Bracket {bracket}",
        "bracket_description": result["bracket_info"]["target_bracket_details"].get("description", ""),
        "BRACKET_REQUIREMENT": f"The deck MUST be built to Bracket {bracket} specifications. Review the bracket_guidelines below carefully.",
        "color_identity_restriction": f"All cards must be within the color identity: {result['color_identity']} (or colorless). Lands must not generate mana that does not exist within the identified color identity.",
        "singleton_rule": "Exactly 1 copy of each card except basic lands",
        "basic_lands_allowed": ["Plains", "Island", "Swamp", "Mountain", "Forest", "Snow-Covered variants", "Wastes"],
        "recommended_composition": {
            "lands": "35-40 cards (including basic lands)",
            "ramp": "10-12 cards (mana rocks, land ramp)",
            "card_draw": "10-12 cards",
            "removal": "8-10 cards (single target and board wipes)",
            "threats_and_synergy": "Remaining slots for win conditions and synergy pieces"
        },
        "bracket_guidelines": {
            "power_level": result["bracket_info"]["target_bracket_details"].get("power_level", ""),
            "description": result["bracket_info"]["target_bracket_details"].get("description", ""),
            "characteristics": result["bracket_info"]["target_bracket_details"].get("characteristics", []),
            "typical_cards": result["bracket_info"]["target_bracket_details"].get("typical_cards", []),
            "game_changers_limit": {
                "bracket_1_2": "Generally avoid game changers",
                "bracket_3": "Generally run up to 3 game changers",
                "bracket_4_5": "Unrestricted on game changers"
            },
            "YOUR_BRACKET": f"You are building a Bracket {bracket} deck - follow the guidelines for this bracket specifically"
        },
        "data_sources": {
            "edhrec_recommendations": "Use the top recommended cards from EDHREC for each commander (found in deck_building_data.commanders[].recommendations)",
            "combos": f"Consider including combo pieces if appropriate for Bracket {bracket} (found in deck_building_data.commanders[].combos)",
            "color_identity": f"Filter all card selections by the combined color identity: {result['color_identity']}",
            "power_level": f"Build to Bracket {bracket} specifications - see bracket_guidelines for details",
            "game_changers": "Check the game changers list in format_rules.commander_context to manage power level appropriately",
            "banned_cards": "Avoid all cards in format_rules.commander_context.banned_list"
        },
        "deck_building_steps": [
            f"1. Start with the commander(s): {', '.join([cmd['name'] for cmd in result['commanders']])}",
            f"2. Review Bracket {bracket} guidelines in bracket_guidelines section",
            "3. Add essential mana base (lands appropriate to color identity)",
            f"4. Add mana ramp appropriate for Bracket {bracket} (use typical_cards from bracket_guidelines as reference)",
            "5. Add card draw engines",
            "6. Add removal and interaction",
            f"7. Add win conditions and synergy pieces from EDHREC recommendations (matching Bracket {bracket} power level)",
            f"8. If building Bracket 3+, consider adding game changers (limit based on bracket)",
            "9. Ensure total is exactly 100 cards",
            "10. Format output using the export_format specification (NO COMMENTS, NO HEADERS, JUST CARD LINES)"
        ],
        "validation_checklist": [
            "Total cards = 100",
            f"All cards match color identity: {result['color_identity']}",
            "Only 1 copy of non-basic lands",
            "Basic lands can have multiple copies",
            "All cards are legal in Commander format (not banned)",
            f"Deck matches Bracket {bracket} power level expectations",
            "Output format is clean (no comments, no headers, just quantity x card name per line)"
        ],
        "OUTPUT_INSTRUCTIONS": {
            "format": "Use the format specified in export_format",
            "CRITICAL": "DO NOT include comments, section headers, or blank lines",
            "example_start": [
                f"1x {result['commanders'][0]['name']}",
                "1x Sol Ring",
                "1x Arcane Signet"
            ],
            "GENERATE_NOW": "After reviewing all the provided data, generate the complete 100-card decklist now."
        }
    }
    
    logger.info("Deck-building data gathering complete")
    
    return result

if __name__ == "__main__":
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
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Logging level: {'DEBUG' if args.debug else 'WARNING'}")
    logger.info("="*50)
    mcp.run()