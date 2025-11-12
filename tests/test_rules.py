"""Unit tests for mtg_mcp/tools/rules.py"""
from unittest.mock import patch

import pytest

from mtg_mcp.tools.rules import get_rules_info, search_rules


class TestRulesTools:
    """Tests for MTG rules tools"""

    @pytest.mark.asyncio
    async def test_get_rules_info_success(self):
        """Test successful rules info retrieval"""
        mock_rules = {
            "last_updated": "2025-09-19",
            "sections": {
                "1. Game Concepts": "Text",
                "2. Parts of the Game": "Text"
            }
        }

        with patch('mtg_mcp.tools.rules.get_rules') as mock_get:
            mock_get.return_value = mock_rules

            result = await get_rules_info()

            assert result["last_updated"] == "2025-09-19"
            assert "sections" in result
            assert "available_rules" in result

    @pytest.mark.asyncio
    async def test_get_rules_info_error(self):
        """Test rules info retrieval with error"""
        with patch('mtg_mcp.tools.rules.get_rules') as mock_get:
            mock_get.return_value = {"error": "Failed", "last_updated": "2025-09-19"}

            result = await get_rules_info()

            assert "error" in result
            assert result["error"] == "Rules are currently unavailable"

    @pytest.mark.asyncio
    async def test_search_rules_by_section(self):
        """Test searching rules by section number"""
        mock_rules = {
            "sections": {
                "1. Game Concepts": "Game concepts text",
                "1.1 Overview": "Overview text",
                "2. Parts of the Game": "Parts text"
            },
            "last_updated": "2025-09-19"
        }

        with patch('mtg_mcp.tools.rules.get_rules') as mock_get:
            mock_get.return_value = mock_rules

            result = await search_rules(section="1")

            assert result["matches"] == 2  # Should match 1. and 1.1
            assert "1. Game Concepts" in result["results"]
            assert "1.1 Overview" in result["results"]

    @pytest.mark.asyncio
    async def test_search_rules_by_keyword(self):
        """Test searching rules by keyword"""
        mock_rules = {
            "sections": {
                "1. Game Concepts": "mana and spells",
                "2. Parts of the Game": "deck and hand"
            },
            "last_updated": "2025-09-19"
        }

        with patch('mtg_mcp.tools.rules.get_rules') as mock_get:
            mock_get.return_value = mock_rules

            result = await search_rules(keyword="mana")

            assert result["matches"] == 1
            assert "1. Game Concepts" in result["results"]
