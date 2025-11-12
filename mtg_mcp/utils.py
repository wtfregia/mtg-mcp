"""Utility functions for MTG MCP Server"""
import asyncio
import logging
import time
from typing import Any, Dict

import aiohttp

logger = logging.getLogger('mtg-mcp')

# Rate limiting for API calls (100ms minimum between calls)
_last_api_call_time = {
    'scryfall': 0.0,
    'commanderspellbook': 0.0,
    'archidekt': 0.0
}
_api_rate_limit_ms = 100  # Minimum milliseconds between API calls

async def rate_limit_api_call(api_name: str) -> None:
    """
    Ensure at least 100ms has passed since the last API call to the specified API.

    Args:
        api_name: Either 'scryfall', 'commanderspellbook', or 'archidekt'
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

# Global caches
_rules_cache = None
_game_changers_cache = None
_banned_cards_cache = None

async def get_rules() -> Dict[str, Any]:
    """Get and cache the comprehensive rules"""
    global _rules_cache
    if _rules_cache is None:
        _rules_cache = await fetch_and_parse_rules()
    return _rules_cache

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
                        banned_cards.append({
                            "name": card.get("name", ""),
                            "type_line": card.get("type_line", ""),
                            "mana_cost": card.get("mana_cost", ""),
                            "cmc": card.get("cmc", 0),
                            "color_identity": card.get("color_identity", []),
                            "oracle_text": card.get("oracle_text", ""),
                            "scryfall_uri": card.get("scryfall_uri", "")
                        })

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
                            seen.add(card_name)
                            game_changers.append({
                                "name": card_name,
                                "num_decks": card.get("num_decks", 0),
                                "label": card.get("label", ""),
                                "sanitized": card.get("sanitized", "")
                            })

                # Fetch additional Scryfall data for each card (in batches to respect rate limits)
                for card_info in game_changers:
                    card_name = card_info["name"]
                    try:
                        await rate_limit_api_call('scryfall')
                        search_url = f"https://api.scryfall.com/cards/named?exact={card_name}"
                        async with session.get(search_url) as scryfall_response:
                            if scryfall_response.status == 200:
                                scryfall_data = await scryfall_response.json()
                                card_info.update({
                                    "type_line": scryfall_data.get("type_line", ""),
                                    "mana_cost": scryfall_data.get("mana_cost", ""),
                                    "colors": scryfall_data.get("colors", []),
                                    "color_identity": scryfall_data.get("color_identity", []),
                                    "oracle_text": scryfall_data.get("oracle_text", ""),
                                    "scryfall_uri": scryfall_data.get("scryfall_uri", ""),
                                    "prices": {
                                        "usd": scryfall_data.get("prices", {}).get("usd"),
                                        "usd_foil": scryfall_data.get("prices", {}).get("usd_foil"),
                                        "eur": scryfall_data.get("prices", {}).get("eur"),
                                        "tix": scryfall_data.get("prices", {}).get("tix")
                                    }
                                })
                    except Exception as e:
                        logger.warning(f"Could not fetch Scryfall data for {card_name}: {e}")

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
