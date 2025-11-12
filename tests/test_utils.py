"""Unit tests for mtg_mcp/utils.py"""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import mtg_mcp.utils
from mtg_mcp.utils import (
    _last_api_call_time,
    fetch_and_parse_rules,
    fetch_banned_cards,
    fetch_game_changers,
    get_banned_cards,
    get_game_changers,
    get_rules,
    rate_limit_api_call,
)

# Test constants
MOCK_RULES_DATE = "2025-09-19"


@pytest.fixture(autouse=True)
def reset_rate_limiting():
    """Reset rate limiting state before each test"""
    original = _last_api_call_time.copy()
    _last_api_call_time.clear()
    yield
    _last_api_call_time.clear()
    _last_api_call_time.update(original)


@pytest.fixture
def reset_rules_cache():
    """Reset rules cache before and after test"""
    original = mtg_mcp.utils._rules_cache
    mtg_mcp.utils._rules_cache = None
    yield
    mtg_mcp.utils._rules_cache = original


@pytest.fixture
def reset_banned_cards_cache():
    """Reset banned cards cache before and after test"""
    original = mtg_mcp.utils._banned_cards_cache
    mtg_mcp.utils._banned_cards_cache = None
    yield
    mtg_mcp.utils._banned_cards_cache = original


@pytest.fixture
def reset_game_changers_cache():
    """Reset game changers cache before and after test"""
    original = mtg_mcp.utils._game_changers_cache
    mtg_mcp.utils._game_changers_cache = None
    yield
    mtg_mcp.utils._game_changers_cache = original


class TestRateLimiting:
    """Tests for API rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limit_first_call(self):
        """First call should not sleep"""
        start_time = time.time()
        await rate_limit_api_call('test_api')
        elapsed = time.time() - start_time
        assert elapsed < 0.01  # Should be nearly instant

    @pytest.mark.asyncio
    async def test_rate_limit_second_call(self):
        """Second call within 100ms should sleep"""
        await rate_limit_api_call('test_api_2')
        start_time = time.time()
        await rate_limit_api_call('test_api_2')
        elapsed = time.time() - start_time
        assert elapsed >= 0.09  # Should sleep ~100ms

    @pytest.mark.asyncio
    async def test_rate_limit_different_apis(self):
        """Different APIs should have separate rate limits"""
        await rate_limit_api_call('scryfall')
        start_time = time.time()
        await rate_limit_api_call('commanderspellbook')
        elapsed = time.time() - start_time
        assert elapsed < 0.01  # Should not sleep


class TestRulesFetching:
    """Tests for rules fetching and parsing"""

    @pytest.mark.asyncio
    async def test_fetch_and_parse_rules_success(self):
        """Test successful rules fetching"""
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value="1. Game Concepts\nSome rules text\n2. Parts of the Game\nMore rules")

        mock_get = MagicMock()
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_get)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await fetch_and_parse_rules()

            assert "sections" in result
            assert "last_updated" in result
            assert isinstance(result["last_updated"], str) and len(result["last_updated"]) > 0

    @pytest.mark.asyncio
    async def test_fetch_and_parse_rules_error(self):
        """Test error handling in rules fetching"""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Network error")
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await fetch_and_parse_rules()

            assert "error" in result
            assert result["error"] == "Could not fetch current rules"

    @pytest.mark.asyncio
    async def test_get_rules_caching(self, reset_rules_cache):
        """Test that rules are cached after first fetch"""
        with patch('mtg_mcp.utils.fetch_and_parse_rules') as mock_fetch:
            mock_fetch.return_value = {"last_updated": MOCK_RULES_DATE, "sections": {}}

            # First call should fetch
            await get_rules()
            assert mock_fetch.call_count == 1

            # Second call should use cache
            await get_rules()
            assert mock_fetch.call_count == 1  # Still 1, not called again


class TestBannedCards:
    """Tests for banned cards fetching"""

    @pytest.mark.asyncio
    async def test_fetch_banned_cards_success(self):
        """Test successful banned cards fetching"""
        mock_data = {
            "data": [
                {
                    "name": "Banned Card",
                    "type_line": "Creature",
                    "mana_cost": "{2}{U}",
                    "colors": ["U"],
                    "color_identity": ["U"],
                    "oracle_text": "This card is banned",
                    "scryfall_uri": "https://scryfall.com/card"
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
            with patch('mtg_mcp.utils.rate_limit_api_call', new_callable=AsyncMock):
                result = await fetch_banned_cards()

                assert "banned_cards" in result
                assert len(result["banned_cards"]) == 1
                assert result["banned_cards"][0] == "Banned Card"

    @pytest.mark.asyncio
    async def test_get_banned_cards_caching(self, reset_banned_cards_cache):
        """Test that banned cards are cached"""
        with patch('mtg_mcp.utils.fetch_banned_cards') as mock_fetch:
            mock_fetch.return_value = {"banned_cards": ["Test"]}

            await get_banned_cards()
            assert mock_fetch.call_count == 1

            await get_banned_cards()
            assert mock_fetch.call_count == 1


class TestGameChangers:
    """Tests for game changers fetching"""

    @pytest.mark.asyncio
    async def test_fetch_game_changers_success(self):
        """Test successful game changers fetching"""
        mock_data = {
            "container": {
                "json_dict": {
                    "cardlists": [
                        {
                            "cardviews": [
                                {
                                    "name": "Powerful Card",
                                    "num_decks": 1000,
                                    "label": "Game Changer",
                                    "sanitized": "powerful-card"
                                }
                            ]
                        }
                    ]
                }
            }
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_data)

        # Mock Scryfall response
        mock_scryfall = AsyncMock()
        mock_scryfall.status = 200
        mock_scryfall.json = AsyncMock(return_value={
            "type_line": "Sorcery",
            "mana_cost": "{5}",
            "colors": [],
            "color_identity": [],
            "oracle_text": "Draw cards",
            "scryfall_uri": "https://scryfall.com",
            "prices": {"usd": "10.00"}
        })

        mock_get_edhrec = MagicMock()
        mock_get_edhrec.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get_edhrec.__aexit__ = AsyncMock(return_value=None)

        mock_get_scryfall = MagicMock()
        mock_get_scryfall.__aenter__ = AsyncMock(return_value=mock_scryfall)
        mock_get_scryfall.__aexit__ = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=[mock_get_edhrec, mock_get_scryfall])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with patch('mtg_mcp.utils.rate_limit_api_call', new_callable=AsyncMock):
                result = await fetch_game_changers()

                assert "cards" in result
                assert len(result["cards"]) == 1

    @pytest.mark.asyncio
    async def test_get_game_changers_caching(self, reset_game_changers_cache):
        """Test that game changers are cached"""
        with patch('mtg_mcp.utils.fetch_game_changers') as mock_fetch:
            mock_fetch.return_value = {"cards": ["Test"]}

            await get_game_changers()
            assert mock_fetch.call_count == 1

            await get_game_changers()
            assert mock_fetch.call_count == 1
