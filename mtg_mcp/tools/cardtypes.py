"""MTG Card Types Tool"""
import logging
from typing import Any, Dict, List

from mtgsdk import Card, Subtype, Supertype, Type

logger = logging.getLogger('mtg-mcp')

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

    type_descriptions = {}
    for name, (desc, rules) in descriptions.items():
        key = "rules" if "attack" in rules else "timing"
        type_descriptions[name] = {"description": desc, key: rules}

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
                    for main_type in result["subtypes"].keys():
                        if main_type.lower() in cards[0].type.lower():
                            result["subtypes"][main_type].append(subtype)
                            break
            except Exception:
                logger.exception(f"Failed to process subtype '{subtype}' in get_card_types")
                continue
    except Exception:
        logger.exception("Failed to fetch or process subtypes in get_card_types")

    try:
        result["supertypes"] = Supertype.all()
    except Exception:
        result["supertypes"] = ["Basic", "Legendary", "Snow", "World", "Ongoing"]

    return result
