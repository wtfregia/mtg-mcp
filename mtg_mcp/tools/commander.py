"""MTG Commander Tools - Recommendations, Brackets, Export Format, and Deck Generation"""
import asyncio
import logging
from typing import Any, Dict, List

import aiohttp

from mtg_mcp.tools.combos import search_combos
from mtg_mcp.tools.context import get_commander_context
from mtg_mcp.tools.rules import get_rules_info
from mtg_mcp.tools.ruling import search_rulings
from mtg_mcp.utils import rate_limit_api_call

logger = logging.getLogger('mtg-mcp')

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
    result["color_identity"] = sorted(all_colors)

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
            "8. If building Bracket 3+, consider adding game changers (limit based on bracket)",
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
