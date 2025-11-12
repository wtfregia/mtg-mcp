"""MTG Rules Tools"""
import logging
from typing import Any, Dict

from mtg_mcp.utils import get_rules

logger = logging.getLogger('mtg-mcp')

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
