"""Unit tests for mtg_mcp/tools/archidekt.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mtg_mcp.tools.archidekt import fetch_archidekt_deck


class TestArchidektTools:
    """Tests for Archidekt deck fetching tools"""

    @pytest.mark.asyncio
    async def test_fetch_archidekt_deck_success(self):
        """Test successful deck fetching"""
        mock_data = {
            "id": 123,
            "name": "Test Deck",
            "description": "A test deck",
            "deckFormat": 5,  # Commander
            "createdAt": "2025-01-01",
            "updatedAt": "2025-01-02",
            "viewCount": 100,
            "owner": {"username": "testuser"},
            "categories": [
                {"id": 1, "name": "Commander", "isPremier": True, "includedInDeck": True}
            ],
            "cards": [
                {
                    "quantity": 1,
                    "categories": ["Commander"],
                    "card": {
                        "name": "Test Commander",
                        "oracleCard": {
                            "name": "Test Commander",
                            "manaCost": "{2}{U}",
                            "cmc": 3,
                            "types": ["Creature"],
                            "colors": ["U"],
                            "colorIdentity": ["U"],
                            "text": "Test text",
                            "power": "2",
                            "toughness": "2"
                        },
                        "edition": {"editionname": "Test Set", "editioncode": "TST"},
                        "rarity": "Rare"
                    }
                }
            ]
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)

        mock_get = MagicMock()
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.archidekt.rate_limit_api_call', new_callable=AsyncMock):
                result = await fetch_archidekt_deck("https://archidekt.com/decks/123/test-deck")

                assert result["success"]
                assert result["deck_info"]["name"] == "Test Deck"
                assert result["total_cards"] == 1
                assert len(result["commanders"]) == 1
                assert result["commanders"][0]["name"] == "Test Commander"

    @pytest.mark.asyncio
    async def test_fetch_archidekt_deck_invalid_url(self):
        """Test deck fetching with invalid URL"""
        result = await fetch_archidekt_deck("https://invalid.com/deck")

        assert "error" in result
        assert "Invalid Archidekt URL" in result["error"]

    @pytest.mark.asyncio
    async def test_fetch_archidekt_deck_not_found(self):
        """Test deck fetching for non-existent deck"""
        mock_response = AsyncMock()
        mock_response.status = 404

        mock_get = MagicMock()
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.archidekt.rate_limit_api_call', new_callable=AsyncMock):
                result = await fetch_archidekt_deck("https://archidekt.com/decks/999999/nonexistent")

                assert "error" in result
                assert result["error"] == "Deck not found"

    @pytest.mark.asyncio
    async def test_fetch_archidekt_deck_network_error(self):
        """Test deck fetching with network error"""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Network error")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.archidekt.rate_limit_api_call', new_callable=AsyncMock):
                result = await fetch_archidekt_deck("https://archidekt.com/decks/123/test")

                assert "error" in result
                assert "Unexpected error" in result["error"]
