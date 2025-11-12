"""Unit tests for mtg_mcp/tools/combos.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mtg_mcp.tools.combos import search_combos


class TestCombosTools:
    """Tests for MTG combo search tools"""

    @pytest.mark.asyncio
    async def test_search_combos_success(self):
        """Test successful combo search"""
        mock_data = {
            "results": [
                {
                    "id": "combo1",
                    "cards": ["Card A", "Card B"],
                    "colorIdentity": "UB",
                    "description": "Infinite combo"
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
            with patch('mtg_mcp.tools.combos.rate_limit_api_call', new_callable=AsyncMock):
                result = await search_combos("Thassa's Oracle")

                assert result["card_name"] == "Thassa's Oracle"
                assert result["total_combos"] == 1
                assert "combos" in result

    @pytest.mark.asyncio
    async def test_search_combos_no_results(self):
        """Test combo search with no results"""
        mock_data = {"results": []}

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
            with patch('mtg_mcp.tools.combos.rate_limit_api_call', new_callable=AsyncMock):
                result = await search_combos("Basic Plains")

                assert result["total_combos"] == 0
                assert result["combos"] == []

    @pytest.mark.asyncio
    async def test_search_combos_api_error(self):
        """Test combo search with API error"""
        mock_response = AsyncMock()
        mock_response.status = 500

        mock_get = MagicMock()
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.combos.rate_limit_api_call', new_callable=AsyncMock):
                result = await search_combos("Sol Ring")

                assert "error" in result
