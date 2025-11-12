"""Unit tests for mtg_mcp/tools/ruling.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mtg_mcp.tools.ruling import search_rulings


class TestRulingTools:
    """Tests for MTG ruling search tools"""

    @pytest.mark.asyncio
    async def test_search_rulings_success(self):
        """Test successful ruling search"""
        mock_card_data = {
            "id": "card123",
            "name": "Sol Ring",
            "type_line": "Artifact",
            "oracle_text": "Tap: Add {C}{C}"
        }

        mock_rulings_data = {
            "data": [
                {
                    "published_at": "2021-01-01",
                    "comment": "This is a ruling"
                }
            ]
        }

        mock_card_response = AsyncMock()
        mock_card_response.status = 200
        mock_card_response.json = AsyncMock(return_value=mock_card_data)

        mock_rulings_response = AsyncMock()
        mock_rulings_response.status = 200
        mock_rulings_response.json = AsyncMock(return_value=mock_rulings_data)

        mock_get_card = MagicMock()
        mock_get_card.__aenter__ = AsyncMock(return_value=mock_card_response)
        mock_get_card.__aexit__ = AsyncMock(return_value=None)

        mock_get_rulings = MagicMock()
        mock_get_rulings.__aenter__ = AsyncMock(return_value=mock_rulings_response)
        mock_get_rulings.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[mock_get_card, mock_get_rulings])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.ruling.rate_limit_api_call', new_callable=AsyncMock):
                result = await search_rulings("Sol Ring")

                assert result["card_name"] == "Sol Ring"
                assert result["total_rulings"] == 1
                assert "rulings" in result

    @pytest.mark.asyncio
    async def test_search_rulings_card_not_found(self):
        """Test ruling search for non-existent card"""
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
            with patch('mtg_mcp.tools.ruling.rate_limit_api_call', new_callable=AsyncMock):
                result = await search_rulings("NonexistentCard")

                assert "error" in result
                assert result["error"] == "Card not found"

    @pytest.mark.asyncio
    async def test_search_rulings_network_error(self):
        """Test ruling search with network error"""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Network error")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.ruling.rate_limit_api_call', new_callable=AsyncMock):
                result = await search_rulings("Sol Ring")

                assert "error" in result
                assert result["error"] == "Failed to fetch rulings"
