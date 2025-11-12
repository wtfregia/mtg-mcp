"""Unit tests for mtg_mcp/tools/commander.py - Part 1: Recommendations and Brackets"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mtg_mcp.tools.commander import get_commander_brackets, get_export_format, recommend_commander_cards


class TestCommanderRecommendations:
    """Tests for commander card recommendations"""

    @pytest.mark.asyncio
    async def test_recommend_commander_cards_success(self):
        """Test successful commander recommendations"""
        mock_card_data = {
            "name": "Atraxa, Praetors' Voice",
            "type_line": "Legendary Creature - Phyrexian Angel"
        }

        mock_edhrec_data = {
            "container": {
                "json_dict": {
                    "card": {"num_decks": 5000},
                    "cardlists": [
                        {
                            "header": "Top Cards",
                            "cardviews": [
                                {
                                    "name": "Sol Ring",
                                    "sanitized_wo": "sol-ring",
                                    "label": "Staple",
                                    "num_decks": 4500,
                                    "potential_decks": 5000,
                                    "synergy": None
                                }
                            ]
                        }
                    ]
                }
            }
        }

        mock_price_data = {
            "mana_cost": "{1}",
            "cmc": 1,
            "type_line": "Artifact",
            "prices": {"usd": "1.50"}
        }

        mock_scryfall_response = AsyncMock()
        mock_scryfall_response.status = 200
        mock_scryfall_response.json = AsyncMock(return_value=mock_card_data)

        mock_edhrec_response = AsyncMock()
        mock_edhrec_response.status = 200
        mock_edhrec_response.json = AsyncMock(return_value=mock_edhrec_data)

        mock_price_response = AsyncMock()
        mock_price_response.status = 200
        mock_price_response.json = AsyncMock(return_value=mock_price_data)

        mock_get_scryfall = MagicMock()
        mock_get_scryfall.__aenter__ = AsyncMock(return_value=mock_scryfall_response)
        mock_get_scryfall.__aexit__ = AsyncMock(return_value=None)

        mock_get_edhrec = MagicMock()
        mock_get_edhrec.__aenter__ = AsyncMock(return_value=mock_edhrec_response)
        mock_get_edhrec.__aexit__ = AsyncMock(return_value=None)

        mock_get_price = MagicMock()
        mock_get_price.__aenter__ = AsyncMock(return_value=mock_price_response)
        mock_get_price.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[mock_get_scryfall, mock_get_edhrec, mock_get_price])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.tools.commander.rate_limit_api_call', new_callable=AsyncMock):
                with patch('asyncio.sleep', new_callable=AsyncMock):
                    result = await recommend_commander_cards("Atraxa", include_context=False)

                    assert result["card_name"] == "Atraxa, Praetors' Voice"
                    assert result["is_legendary_creature"]
                    assert "top_cards" in result

    @pytest.mark.asyncio
    async def test_recommend_commander_cards_not_found(self):
        """Test recommendations for non-existent card"""
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
            with patch('mtg_mcp.tools.commander.rate_limit_api_call', new_callable=AsyncMock):
                result = await recommend_commander_cards("NonexistentCard")

                assert "error" in result
                assert "not found" in result["error"]


class TestCommanderBrackets:
    """Tests for commander bracket information"""

    @pytest.mark.asyncio
    async def test_get_commander_brackets(self):
        """Test getting commander bracket information"""
        result = await get_commander_brackets()

        assert result["system"] == "Commander Bracket System"
        assert result["total_brackets"] == 5
        assert "Bracket 1" in result["brackets"]
        assert "Bracket 2" in result["brackets"]
        assert "Bracket 3" in result["brackets"]
        assert "Bracket 4" in result["brackets"]
        assert "Bracket 5" in result["brackets"]

        # Check bracket 1 details
        bracket1 = result["brackets"]["Bracket 1"]
        assert bracket1["power_level"] == "Lowest power level"
        assert "characteristics" in bracket1

        # Check guidelines
        assert "guidelines" in result
        assert "key_indicators" in result


class TestExportFormat:
    """Tests for deck export format information"""

    @pytest.mark.asyncio
    async def test_get_export_format(self):
        """Test getting export format information"""
        result = await get_export_format()

        assert result["format_name"] == "Standard Decklist Format"
        assert "format_structure" in result
        assert result["format_structure"]["pattern"] == "[quantity]x [Card Name]"
        assert "rules" in result
        assert "singleton_cards" in result["rules"]
        assert "basic_lands" in result["rules"]
        assert "critical_formatting_rules" in result
        assert "commander_specific" in result
