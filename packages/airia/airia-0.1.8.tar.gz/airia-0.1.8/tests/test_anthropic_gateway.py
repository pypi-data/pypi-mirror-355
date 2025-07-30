import pytest
import pytest_asyncio
from dotenv import load_dotenv

from airia import AiriaAsyncClient, AiriaClient

load_dotenv()


# Fixtures for the sync client
@pytest.fixture
def sync_client():
    """Create a sync client with test API key."""
    return AiriaClient.with_anthropic_gateway(log_requests=True)


# Fixtures for the async client
@pytest_asyncio.fixture
async def async_client():
    """Create an async client with test API key."""
    return AiriaAsyncClient.with_anthropic_gateway(log_requests=True)


class TestAnthropicGateway:
    """Tests for the Anthropic gateway functionality."""

    def test_sync_anthropic_gateway_initialization(self, sync_client: AiriaClient):
        """Test initialization of the Anthropic gateway with sync client."""
        assert sync_client.anthropic is not None
        assert sync_client.anthropic.base_url == "https://gateway.airia.ai/anthropic/"

    def test_sync_anthropic_gateway_creation(self, sync_client: AiriaClient):
        """Test creating a simple message with the Anthropic gateway."""
        # Mock the Anthropic API call to avoid actual API calls during tests
        with pytest.MonkeyPatch().context() as m:
            # Simplified mock
            def mock_create(*args, **kwargs):
                class MockContent:
                    text = "Hello from Anthropic gateway"

                class MockResponse:
                    content = [MockContent()]

                return MockResponse()

            m.setattr(sync_client.anthropic.messages, "create", mock_create)

            response = sync_client.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert response.content[0].text == "Hello from Anthropic gateway"


class TestAsyncAnthropicGateway:
    """Tests for the async Anthropic gateway functionality."""

    @pytest.mark.asyncio
    async def test_async_anthropic_gateway_initialization(
        self, async_client: AiriaAsyncClient
    ):
        """Test initialization of the Anthropic gateway with async client."""
        assert async_client.anthropic is not None
        assert async_client.anthropic.base_url == "https://gateway.airia.ai/anthropic/"

    @pytest.mark.asyncio
    async def test_async_anthropic_gateway_creation(
        self, async_client: AiriaAsyncClient
    ):
        """Test creating a simple message with the async Anthropic gateway."""
        # Mock the Anthropic API call to avoid actual API calls during tests
        with pytest.MonkeyPatch().context() as m:
            # Simplified mock
            async def mock_create(*args, **kwargs):
                class MockContent:
                    text = "Hello from async Anthropic gateway"

                class MockResponse:
                    content = [MockContent()]

                return MockResponse()

            m.setattr(async_client.anthropic.messages, "create", mock_create)

            response = await async_client.anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert response.content[0].text == "Hello from async Anthropic gateway"
