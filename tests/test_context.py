"""Unit tests for mtg_mcp/tools/context.py"""
from unittest.mock import patch

import pytest

from mtg_mcp.tools.context import get_commander_context, get_context


class TestContextTools:
    """Tests for MTG context tools"""

    @pytest.mark.asyncio
    async def test_get_context(self):
        """Test basic MTG context retrieval"""
        with patch('mtg_mcp.tools.context.get_rules') as mock_rules:
            mock_rules.return_value = {"last_updated": "2025-09-19", "sections": {}}

            result = await get_context()

            assert result["game"] == "Magic: The Gathering"
            assert result["publisher"] == "Wizards of the Coast"
            assert result["created"] == 1993
            assert "available_tools" in result
            assert "mtg.context.get" in result["available_tools"]

    @pytest.mark.asyncio
    async def test_get_commander_context(self):
        """Test Commander format context retrieval"""
        with patch('mtg_mcp.tools.context.get_game_changers') as mock_gc:
            with patch('mtg_mcp.tools.context.get_banned_cards') as mock_bc:
                mock_gc.return_value = {"cards": ["Game Changer"]}
                mock_bc.return_value = {"banned_cards": ["Banned Card"]}

                result = await get_commander_context()

                assert result["format"] == "Commander (also known as EDH - Elder Dragon Highlander)"
                assert "deck_construction" in result
                assert result["deck_construction"]["total_cards"]["requirement"] == "EXACTLY 100 cards"
                assert result["gameplay"]["starting_life"]["amount"] == 40
                assert "banned_list" in result
                assert "game_changers" in result
