"""Unit tests for mtg_mcp/tools/cardtypes.py"""
from unittest.mock import MagicMock, patch

import pytest

from mtg_mcp.tools.cardtypes import get_card_types


class TestCardTypesTools:
    """Tests for MTG card types tools"""

    @pytest.mark.asyncio
    async def test_get_card_types_success(self):
        """Test successful card types retrieval"""
        with patch('mtg_mcp.tools.cardtypes.Type.all') as mock_types:
            with patch('mtg_mcp.tools.cardtypes.Subtype.all') as mock_subtypes:
                with patch('mtg_mcp.tools.cardtypes.Supertype.all') as mock_supertypes:
                    with patch('mtg_mcp.tools.cardtypes.Card.where') as mock_card:
                        mock_types.return_value = ["Land", "Creature", "Instant"]
                        mock_subtypes.return_value = ["Human", "Island"]
                        mock_supertypes.return_value = ["Basic", "Legendary"]

                        mock_card_obj = MagicMock()
                        mock_card_obj.name = "Example Card"
                        mock_card_obj.type = "Creature - Human"
                        mock_card.return_value.all.return_value = [mock_card_obj]

                        result = await get_card_types()

                        assert "main_types" in result
                        assert "subtypes" in result
                        assert "supertypes" in result
                        assert "Land" in result["main_types"]
                        assert "Creature" in result["main_types"]

    @pytest.mark.asyncio
    async def test_get_card_types_with_error(self):
        """Test card types retrieval with errors"""
        with patch('mtg_mcp.tools.cardtypes.Type.all') as mock_types:
            with patch('mtg_mcp.tools.cardtypes.Subtype.all') as mock_subtypes:
                with patch('mtg_mcp.tools.cardtypes.Supertype.all') as mock_supertypes:
                    mock_types.side_effect = Exception("API Error")
                    mock_subtypes.return_value = []
                    mock_supertypes.return_value = []

                    result = await get_card_types()

                    # Should still return structure with empty data
                    assert "main_types" in result
                    assert "subtypes" in result
                    assert "supertypes" in result
