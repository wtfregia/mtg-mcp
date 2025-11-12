"""MTG Combo Search Tool"""
import logging
from typing import Any, Dict

import aiohttp

from mtg_mcp.utils import rate_limit_api_call

logger = logging.getLogger('mtg-mcp')

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
                if response.status != 200:
                    return {
                        "error": "Failed to fetch combos",
                        "card_name": card_name,
                        "status": response.status
                    }

                data = await response.json()
                combos = data.get("results", [])

                return {
                    "card_name": card_name,
                    "total_combos": len(combos),
                    "combos": combos,
                    "source": "Commander Spellbook",
                    "api_url": api_url,
                    "note": "These are known card combinations in Commander format"
                }

    except Exception as e:
        return {
            "error": "Failed to fetch combos",
            "card_name": card_name,
            "details": str(e)
        }
