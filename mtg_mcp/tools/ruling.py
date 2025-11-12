"""MTG Ruling Search Tool"""
import logging
from typing import Any, Dict

import aiohttp

from mtg_mcp.utils import rate_limit_api_call

logger = logging.getLogger('mtg-mcp')

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
                if response.status != 200:
                    return {
                        "error": "Card not found",
                        "card_name": card_name,
                        "status": response.status
                    }

                card_data = await response.json()
                card_id = card_data.get("id")
                exact_name = card_data.get("name")
                type_line = card_data.get("type_line", "")
                oracle_text = card_data.get("oracle_text", "")

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
                        "error": "Could not fetch rulings",
                        "card_name": exact_name,
                        "status": rulings_response.status
                    }

                rulings_data = await rulings_response.json()
                rulings_list = rulings_data.get("data", [])

                return {
                    "card_name": exact_name,
                    "type_line": type_line,
                    "oracle_text": oracle_text,
                    "total_rulings": len(rulings_list),
                    "rulings": rulings_list,
                    "source": "Scryfall",
                    "note": "Rulings are official clarifications from judges and Wizards of the Coast"
                }

    except Exception as e:
        return {
            "error": "Failed to fetch rulings",
            "card_name": card_name,
            "details": str(e)
        }
