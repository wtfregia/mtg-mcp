"""Unit tests for mtg_mcp/tools/moxfield.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mtg_mcp.tools.moxfield import fetch_moxfield_deck


class TestMoxfieldTools:
    """Tests for Moxfield deck fetching tools"""

    @pytest.mark.asyncio
    async def test_fetch_moxfield_deck_success(self):
        """Test successful deck fetch from Moxfield"""
        mock_response_data = {
            "id": "DOyKdx",
            "name": "Test Commander Deck",
            "description": "A test deck",
            "format": "commander",
            "publicUrl": "https://moxfield.com/decks/TdOsPBP3302BdskyLVzU-A",
            "publicId": "TdOsPBP3302BdskyLVzU-A",
            "visibility": "public",
            "likeCount": 10,
            "viewCount": 100,
            "commentCount": 5,
            "createdByUser": {
                "displayName": "TestUser"
            },
            "authors": [
                {"displayName": "TestUser"}
            ],
            "boards": {
                "commanders": {
                    "count": 1,
                    "cards": {
                        "card1": {
                            "quantity": 1,
                            "boardType": "commanders",
                            "card": {
                                "name": "Atraxa, Praetors' Voice",
                                "mana_cost": "{G}{W}{U}{B}",
                                "cmc": 4.0,
                                "type_line": "Legendary Creature — Phyrexian Angel Horror",
                                "oracle_text": "Flying, vigilance, deathtouch, lifelink",
                                "colors": ["G", "W", "U", "B"],
                                "color_identity": ["G", "W", "U", "B"],
                                "power": "4",
                                "toughness": "4",
                                "rarity": "mythic",
                                "set_name": "Commander 2016",
                                "set": "c16"
                            }
                        }
                    }
                },
                "mainboard": {
                    "count": 99,
                    "cards": {
                        "card2": {
                            "quantity": 1,
                            "boardType": "mainboard",
                            "isFoil": False,
                            "finish": "nonFoil",
                            "card": {
                                "name": "Sol Ring",
                                "mana_cost": "{1}",
                                "cmc": 1.0,
                                "type_line": "Artifact",
                                "oracle_text": "{T}: Add {C}{C}.",
                                "colors": [],
                                "color_identity": [],
                                "rarity": "uncommon",
                                "set_name": "Commander 2016",
                                "set": "c16",
                                "cn": "250"
                            }
                        }
                    }
                },
                "sideboard": {
                    "count": 0,
                    "cards": {}
                },
                "maybeboard": {
                    "count": 5,
                    "cards": {}
                }
            }
        }

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)

        mock_get = MagicMock()
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get.return_value = mock_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('mtg_mcp.tools.moxfield.aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.moxfield.rate_limit_api_call', new_callable=AsyncMock):
                result = await fetch_moxfield_deck("https://moxfield.com/decks/TdOsPBP3302BdskyLVzU-A")

        assert result["success"] is True
        assert result["deck_info"]["name"] == "Test Commander Deck"
        assert result["deck_info"]["format"] == "commander"
        assert result["source"] == "Moxfield"
        assert len(result["commanders"]) == 1
        assert result["commanders"][0]["name"] == "Atraxa, Praetors' Voice"
        assert result["mainboard_count"] == 99
        assert result["commanders_count"] == 1
        assert result["total_cards"] == 100
        assert "commander_summary" in result
        assert "Atraxa, Praetors' Voice" in result["commander_summary"]

    @pytest.mark.asyncio
    async def test_fetch_moxfield_deck_invalid_url(self):
        """Test invalid URL format"""
        result = await fetch_moxfield_deck("https://invalid.com/deck/12345")

        assert "error" in result
        assert "Invalid Moxfield URL" in result["error"]

    @pytest.mark.asyncio
    async def test_fetch_moxfield_deck_not_found(self):
        """Test deck not found (404)"""
        mock_response = MagicMock()
        mock_response.status = 404

        mock_get = MagicMock()
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get.return_value = mock_get
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('mtg_mcp.tools.moxfield.aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.moxfield.rate_limit_api_call', new_callable=AsyncMock):
                result = await fetch_moxfield_deck("https://moxfield.com/decks/nonexistent")

        assert "error" in result
        assert result["error"] == "Deck not found"

    @pytest.mark.asyncio
    async def test_fetch_moxfield_deck_network_error(self):
        """Test network error handling"""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Network error")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('mtg_mcp.tools.moxfield.aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.moxfield.rate_limit_api_call', new_callable=AsyncMock):
                result = await fetch_moxfield_deck("https://moxfield.com/decks/TdOsPBP3302BdskyLVzU-A")

        assert "error" in result
        assert "error" in result["error"].lower()
