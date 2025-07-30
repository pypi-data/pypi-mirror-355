import pytest
import pytest_asyncio
from dotenv import load_dotenv

from airia import AiriaAsyncClient, AiriaClient

load_dotenv()


# Fixtures for the sync client
@pytest.fixture
def sync_client():
    """Create a sync client with test API key."""
    return AiriaClient.with_openai_gateway(log_requests=True)


# Fixtures for the async client
@pytest_asyncio.fixture
async def async_client():
    """Create an async client with test API key."""
    return AiriaAsyncClient.with_openai_gateway(log_requests=True)


class TestOpenAIGateway:
    """Tests for the OpenAI gateway functionality."""

    def test_sync_openai_gateway_initialization(self, sync_client: AiriaClient):
        """Test initialization of the OpenAI gateway with sync client."""
        assert sync_client.openai is not None
        assert sync_client.openai.base_url == "https://gateway.airia.ai/openai/v1/"

    def test_sync_openai_gateway_creation(self, sync_client: AiriaClient):
        """Test creating a simple completion with the OpenAI gateway."""
        # Mock the OpenAI API call to avoid actual API calls during tests
        with pytest.MonkeyPatch().context() as m:
            # This is a simplified way to mock the response - in a real test you'd use pytest-mock
            def mock_create(*args, **kwargs):
                class MockCompletion:
                    class MockChoice:
                        class MockMessage:
                            content = "Hello from OpenAI gateway"

                        message = MockMessage()

                    choices = [MockChoice()]

                return MockCompletion()

            m.setattr(sync_client.openai.chat.completions, "create", mock_create)

            response = sync_client.openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"},
                ],
            )

            assert response.choices[0].message.content == "Hello from OpenAI gateway"


class TestAsyncOpenAIGateway:
    """Tests for the async OpenAI gateway functionality."""

    @pytest.mark.asyncio
    async def test_async_openai_gateway_initialization(
        self, async_client: AiriaAsyncClient
    ):
        """Test initialization of the OpenAI gateway with async client."""
        assert async_client.openai is not None
        assert async_client.openai.base_url == "https://gateway.airia.ai/openai/v1/"

    @pytest.mark.asyncio
    async def test_async_openai_gateway_creation(self, async_client: AiriaAsyncClient):
        """Test creating a simple completion with the async OpenAI gateway."""
        # Mock the OpenAI API call to avoid actual API calls during tests
        with pytest.MonkeyPatch().context() as m:
            # This is a simplified way to mock the response
            async def mock_create(*args, **kwargs):
                class MockCompletion:
                    class MockChoice:
                        class MockMessage:
                            content = "Hello from async OpenAI gateway"

                        message = MockMessage()

                    choices = [MockChoice()]

                return MockCompletion()

            m.setattr(async_client.openai.chat.completions, "create", mock_create)

            response = await async_client.openai.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"},
                ],
            )

            assert (
                response.choices[0].message.content == "Hello from async OpenAI gateway"
            )
