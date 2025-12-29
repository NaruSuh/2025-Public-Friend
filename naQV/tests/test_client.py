"""Tests for ECOS API client."""

import os
from unittest.mock import patch

import pytest

from naqv import EcosClient
from naqv.client import EcosError


class TestEcosClientInit:
    """Test EcosClient initialization."""

    def test_init_with_api_key(self) -> None:
        """Test initialization with explicit API key."""
        client = EcosClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.language == "kr"
        assert client.format == "json"
        client.close()

    def test_init_from_env(self) -> None:
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {"ECOS_API_KEY": "env_key"}):
            client = EcosClient()
            assert client.api_key == "env_key"
            client.close()

    def test_init_no_key_raises(self) -> None:
        """Test initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove ECOS_API_KEY if exists
            os.environ.pop("ECOS_API_KEY", None)
            with pytest.raises(ValueError, match="API key required"):
                EcosClient()

    def test_context_manager(self) -> None:
        """Test context manager usage."""
        with EcosClient(api_key="test_key") as client:
            assert client.api_key == "test_key"


class TestEcosError:
    """Test EcosError exception."""

    def test_error_message(self) -> None:
        """Test error message format."""
        error = EcosError(100, "Invalid API key")
        assert error.code == 100
        assert error.message == "Invalid API key"
        assert str(error) == "[100] Invalid API key"


# Integration tests (requires real API key)
@pytest.mark.skipif(
    not os.environ.get("ECOS_API_KEY"),
    reason="ECOS_API_KEY not set",
)
class TestEcosClientIntegration:
    """Integration tests with real API."""

    @pytest.fixture
    def client(self) -> EcosClient:
        """Create client with real API key."""
        return EcosClient()

    def test_get_key_statistics(self, client: EcosClient) -> None:
        """Test fetching key statistics."""
        stats = client.get_key_statistics(start=1, end=5)
        assert len(stats) > 0
        assert stats[0].keystat_name  # Has name
        assert stats[0].data_value  # Has value
        client.close()

    def test_get_statistic_tables(self, client: EcosClient) -> None:
        """Test fetching statistic tables."""
        tables = client.get_statistic_tables(start=1, end=5)
        assert len(tables) > 0
        assert tables[0].stat_code  # Has code
        assert tables[0].stat_name  # Has name
        client.close()

    def test_search_gdp(self, client: EcosClient) -> None:
        """Test searching GDP data."""
        # 200Y001: 국내총생산(GDP)
        data = client.search(
            stat_code="200Y001",
            cycle="A",  # Annual
            start_time="2020",
            end_time="2023",
            start=1,
            end=10,
        )
        assert len(data) > 0
        client.close()
