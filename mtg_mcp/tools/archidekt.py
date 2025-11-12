"""MTG Archidekt Tool - Fetch decks from Archidekt"""
import logging
import re
from typing import Any, Dict

import aiohttp

from mtg_mcp.utils import rate_limit_api_call

logger = logging.getLogger('mtg-mcp')

async def fetch_archidekt_deck(deck_url: str) -> Dict[str, Any]:
    """
    Fetch a deck from Archidekt using a deck URL.

    Args:
        deck_url: The Archidekt deck URL (e.g., https://archidekt.com/decks/17187915/automation_testing)

    Returns:
        Dictionary containing deck information and card list or an error message.
    """
    logger.info(f"Tool called: mtg.archidekt.fetch with deck_url={deck_url}")

    # Extract deck ID from URL
    # URL format: https://archidekt.com/decks/{deck_id}/{deck_name}
    match = re.search(r'https?://(?:www\.)?archidekt\.com/decks/(\d+)', deck_url)

    if not match:
        return {
            "error": "Invalid Archidekt URL. Please provide a URL from archidekt.com in the correct format.",
            "expected_format": "https://archidekt.com/decks/{deck_id}/{deck_name}",
            "example": "https://archidekt.com/decks/17187915/automation_testing"
        }

    deck_id = match.group(1)
    api_url = f"https://archidekt.com/api/decks/{deck_id}/"

    logger.info(f"Fetching deck from Archidekt API: {api_url}")

    try:
        await rate_limit_api_call('archidekt')

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 404:
                    return {
                        "error": "Deck not found",
                        "deck_id": deck_id,
                        "message": "The deck may be private or does not exist"
                    }

                if response.status != 200:
                    return {
                        "error": f"Failed to fetch deck from Archidekt API (status {response.status})",
                        "deck_id": deck_id,
                        "api_url": api_url
                    }

                data = await response.json()

                # Extract deck information
                deck_info = {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "description": data.get("description", ""),
                    "format": data.get("deckFormat"),
                    "created_at": data.get("createdAt"),
                    "updated_at": data.get("updatedAt"),
                    "view_count": data.get("viewCount", 0),
                    "owner": data.get("owner", {}).get("username", "Unknown")
                }

                # Process cards
                cards = []
                categories_map = {}

                # Build categories map
                for category in data.get("categories", []):
                    categories_map[category.get("id")] = {
                        "name": category.get("name", "Unknown"),
                        "is_premier": category.get("isPremier", False),
                        "included_in_deck": category.get("includedInDeck", True)
                    }

                # Extract card information
                for card_entry in data.get("cards", []):
                    card_data = card_entry.get("card", {})
                    oracle_data = card_data.get("oracleCard", {})

                    # Get categories for this card (Archidekt returns category names as strings)
                    card_categories = card_entry.get("categories", [])

                    card_info = {
                        "quantity": card_entry.get("quantity", 1),
                        "name": oracle_data.get("name", card_data.get("name", "Unknown")),
                        "categories": card_categories,
                        "mana_cost": oracle_data.get("manaCost", ""),
                        "cmc": oracle_data.get("cmc", 0),
                        "type_line": " ".join(oracle_data.get("types", [])),
                        "colors": oracle_data.get("colors", []),
                        "color_identity": oracle_data.get("colorIdentity", []),
                        "text": oracle_data.get("text", ""),
                        "power": oracle_data.get("power"),
                        "toughness": oracle_data.get("toughness"),
                        "loyalty": oracle_data.get("loyalty"),
                        "rarity": card_data.get("rarity", ""),
                        "set": card_data.get("edition", {}).get("editionname", ""),
                        "set_code": card_data.get("edition", {}).get("editioncode", ""),
                        "collector_number": card_data.get("collectorNumber", ""),
                        "modifier": card_entry.get("modifier", "Normal")
                    }

                    cards.append(card_info)

                # Count cards by category and identify commanders
                category_counts = {}
                commanders = []

                for card in cards:
                    is_commander = False
                    for cat in card["categories"]:
                        if cat not in category_counts:
                            category_counts[cat] = 0
                        category_counts[cat] += card["quantity"]
                        if cat.lower() == "commander":
                            is_commander = True
                    # After processing all categories, add to commanders if needed
                    if is_commander:
                        commanders.append({
                            "name": card["name"],
                            "colors": card["colors"],
                            "color_identity": card["color_identity"],
                            "mana_cost": card["mana_cost"],
                            "cmc": card["cmc"],
                            "type_line": card["type_line"],
                            "text": card["text"],
                            "power": card["power"],
                            "toughness": card["toughness"],
                            "loyalty": card["loyalty"]
                        })

                # Calculate total cards
                total_cards = sum(card["quantity"] for card in cards)

                result = {
                    "success": True,
                    "deck_info": deck_info,
                    "commanders": commanders,
                    "cards": cards,
                    "categories": categories_map,
                    "category_counts": category_counts,
                    "total_cards": total_cards,
                    "source": "Archidekt",
                    "api_url": api_url
                }

                if commanders:
                    commander_names = ", ".join([c["name"] for c in commanders])
                    logger.info(f"Successfully fetched deck '{deck_info['name']}' with {total_cards} cards (Commander: {commander_names})")
                else:
                    logger.info(f"Successfully fetched deck '{deck_info['name']}' with {total_cards} cards (no commander identified)")

                return result

    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching deck from Archidekt: {e}")
        return {
            "error": "Network error while fetching deck",
            "details": str(e),
            "api_url": api_url
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching deck from Archidekt: {e}")
        return {
            "error": "Unexpected error while fetching deck",
            "details": str(e),
            "api_url": api_url
        }
