"""MTG Moxfield Tool - Fetch decks from Moxfield"""
import logging
import re
from typing import Any, Dict

import aiohttp

from mtg_mcp.utils import rate_limit_api_call

logger = logging.getLogger('mtg-mcp')

async def fetch_moxfield_deck(deck_url: str) -> Dict[str, Any]:
    """
    Fetch a deck from Moxfield using a deck URL.

    Args:
        deck_url: The Moxfield deck URL (e.g., https://moxfield.com/decks/TdOsPBP3302BdskyLVzU-A)

    Returns:
        Dictionary containing deck information and card list or an error message.
    """
    logger.info(f"Tool called: mtg.moxfield.fetch with deck_url={deck_url}")

    # Extract deck ID from URL
    # URL format: https://moxfield.com/decks/{deck_id}
    match = re.search(r'https?://(?:www\.)?moxfield\.com/decks/([a-zA-Z0-9_-]+)', deck_url)

    if not match:
        return {
            "error": "Invalid Moxfield URL. Please provide a URL from moxfield.com in the correct format.",
            "expected_format": "https://moxfield.com/decks/{deck_id}",
            "example": "https://moxfield.com/decks/TdOsPBP3302BdskyLVzU-A"
        }

    deck_id = match.group(1)
    api_url = f"https://api2.moxfield.com/v3/decks/all/{deck_id}"

    logger.info(f"Fetching deck from Moxfield API: {api_url}")

    try:
        await rate_limit_api_call('moxfield')

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
                        "error": f"Failed to fetch deck from Moxfield API (status {response.status})",
                        "deck_id": deck_id,
                        "api_url": api_url
                    }

                data = await response.json()

                # Extract deck information
                deck_info = {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "description": data.get("description", ""),
                    "format": data.get("format"),
                    "public_url": data.get("publicUrl"),
                    "public_id": data.get("publicId"),
                    "visibility": data.get("visibility"),
                    "like_count": data.get("likeCount", 0),
                    "view_count": data.get("viewCount", 0),
                    "comment_count": data.get("commentCount", 0),
                    "created_by": data.get("createdByUser", {}).get("displayName", "Unknown"),
                    "authors": [author.get("displayName", "Unknown") for author in data.get("authors", [])]
                }

                # Extract commanders first to inform the AI
                commanders = []
                commanders_data = data.get("boards", {}).get("commanders", {})
                if commanders_data and commanders_data.get("count", 0) > 0:
                    for _card_id, card_entry in commanders_data.get("cards", {}).items():
                        card_data = card_entry.get("card", {})
                        commander_info = {
                            "name": card_data.get("name", "Unknown"),
                            "mana_cost": card_data.get("mana_cost", ""),
                            "cmc": card_data.get("cmc", 0),
                            "type_line": card_data.get("type_line", ""),
                            "oracle_text": card_data.get("oracle_text", ""),
                            "colors": card_data.get("colors", []),
                            "color_identity": card_data.get("color_identity", []),
                            "power": card_data.get("power"),
                            "toughness": card_data.get("toughness"),
                            "loyalty": card_data.get("loyalty"),
                            "set": card_data.get("set_name", ""),
                            "set_code": card_data.get("set", ""),
                            "rarity": card_data.get("rarity", "")
                        }
                        commanders.append(commander_info)

                # Process all boards (mainboard, sideboard, maybeboard, commanders)
                all_cards = []
                board_counts = {}

                for board_name, board_data in data.get("boards", {}).items():
                    if not isinstance(board_data, dict):
                        continue

                    board_count = board_data.get("count", 0)
                    board_counts[board_name] = board_count

                    cards_dict = board_data.get("cards", {})
                    if not cards_dict:
                        continue

                    for _card_id, card_entry in cards_dict.items():
                        card_data = card_entry.get("card", {})

                        card_info = {
                            "quantity": card_entry.get("quantity", 1),
                            "board": board_name,
                            "name": card_data.get("name", "Unknown"),
                            "mana_cost": card_data.get("mana_cost", ""),
                            "cmc": card_data.get("cmc", 0),
                            "type_line": card_data.get("type_line", ""),
                            "oracle_text": card_data.get("oracle_text", ""),
                            "colors": card_data.get("colors", []),
                            "color_identity": card_data.get("color_identity", []),
                            "power": card_data.get("power"),
                            "toughness": card_data.get("toughness"),
                            "loyalty": card_data.get("loyalty"),
                            "rarity": card_data.get("rarity", ""),
                            "set": card_data.get("set_name", ""),
                            "set_code": card_data.get("set", ""),
                            "collector_number": card_data.get("cn", ""),
                            "is_foil": card_entry.get("isFoil", False),
                            "finish": card_entry.get("finish", "nonFoil")
                        }

                        all_cards.append(card_info)

                # Calculate totals
                mainboard_count = board_counts.get("mainboard", 0)
                sideboard_count = board_counts.get("sideboard", 0)
                maybeboard_count = board_counts.get("maybeboard", 0)
                commanders_count = board_counts.get("commanders", 0)
                total_cards = mainboard_count + sideboard_count + commanders_count

                result = {
                    "success": True,
                    "deck_info": deck_info,
                    "commanders": commanders,
                    "cards": all_cards,
                    "board_counts": board_counts,
                    "mainboard_count": mainboard_count,
                    "sideboard_count": sideboard_count,
                    "maybeboard_count": maybeboard_count,
                    "commanders_count": commanders_count,
                    "total_cards": total_cards,
                    "source": "Moxfield",
                    "api_url": api_url
                }

                # Log with commander information prominently
                if commanders:
                    commander_names = ", ".join([c["name"] for c in commanders])
                    result["commander_summary"] = f"This is a {deck_info['format']} deck with commander(s): {commander_names}"
                    logger.info(f"Successfully fetched deck '{deck_info['name']}' - Format: {deck_info['format']}, Commander(s): {commander_names}, Total cards: {total_cards}")
                else:
                    logger.info(f"Successfully fetched deck '{deck_info['name']}' - Format: {deck_info['format']}, Total cards: {total_cards} (no commander)")

                return result

    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching deck from Moxfield: {e}")
        return {
            "error": "Network error while fetching deck",
            "details": str(e),
            "api_url": api_url
        }
    except Exception as e:
        logger.error(f"Unexpected error fetching deck from Moxfield: {e}")
        return {
            "error": "Unexpected error while fetching deck",
            "details": str(e),
            "api_url": api_url
        }
