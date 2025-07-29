from unittest.mock import patch

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from airia import AiriaAsyncClient, AiriaClient
from airia.exceptions import AiriaAPIError

# Load environment variables from .env file
load_dotenv()

# Test constants
SAMPLE_PIPELINE_IDS = {
    "items": [
        {"activeVersion": {"pipelineId": "pipeline-id-1"}},
        {"activeVersion": {"pipelineId": "pipeline-id-2"}},
        {"activeVersion": {"pipelineId": "pipeline-id-3"}},
    ]
}


@pytest.fixture
def sync_client():
    return AiriaClient(log_requests=True)


@pytest_asyncio.fixture
async def async_client():
    return AiriaAsyncClient(log_requests=True)


class TestSyncGetActivePipelineIds:
    """Test cases for synchronous get_active_pipelines_ids method."""

    def test_get_active_pipelines_ids_success(self, sync_client: AiriaClient):
        """Test successful retrieval of active pipeline IDs."""
        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.return_value = SAMPLE_PIPELINE_IDS

            result = sync_client.get_active_pipelines_ids()

            assert result == ["pipeline-id-1", "pipeline-id-2", "pipeline-id-3"]
            assert isinstance(result, list)
            assert len(result) == 3
            mock_request.assert_called_once()

    def test_get_active_pipelines_ids_empty_dict(self, sync_client: AiriaClient):
        """Test handling of empty pipeline list response."""
        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.return_value = {}

            result = sync_client.get_active_pipelines_ids()

            assert result == []
            assert isinstance(result, list)
            assert len(result) == 0

    def test_get_active_pipelines_ids_with_custom_api_version(
        self, sync_client: AiriaClient
    ):
        """Test using custom API version."""
        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.return_value = SAMPLE_PIPELINE_IDS

            result = sync_client.get_active_pipelines_ids(api_version="v1")

            assert result == ["pipeline-id-1", "pipeline-id-2", "pipeline-id-3"]
            mock_request.assert_called_once()

    def test_get_active_pipelines_ids_with_correlation_id(
        self, sync_client: AiriaClient
    ):
        """Test using custom correlation ID."""
        custom_correlation_id = "test-correlation-123"

        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.return_value = SAMPLE_PIPELINE_IDS

            result = sync_client.get_active_pipelines_ids(
                correlation_id=custom_correlation_id
            )

            assert result == ["pipeline-id-1", "pipeline-id-2", "pipeline-id-3"]
            mock_request.assert_called_once()

    def test_get_active_pipelines_ids_invalid_api_version(
        self, sync_client: AiriaClient
    ):
        """Test error handling for invalid API version."""
        with pytest.raises(ValueError, match="Invalid API version"):
            sync_client.get_active_pipelines_ids(api_version="invalid")

    def test_get_active_pipelines_ids_api_error(self, sync_client: AiriaClient):
        """Test error handling for API errors."""
        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.side_effect = AiriaAPIError(
                status_code=404, message="Pipelines not found"
            )

            with pytest.raises(AiriaAPIError) as exc_info:
                sync_client.get_active_pipelines_ids()

            assert "Pipelines not found" in str(exc_info.value)
            assert exc_info.value.status_code == 404

    def test_get_active_pipelines_ids_network_error(self, sync_client: AiriaClient):
        """Test error handling for network errors."""
        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.side_effect = AiriaAPIError(
                status_code=500, message="Internal server error"
            )

            with pytest.raises(AiriaAPIError) as exc_info:
                sync_client.get_active_pipelines_ids()

            assert exc_info.value.status_code == 500


class TestAsyncGetActivePipelineIds:
    """Test cases for asynchronous get_active_pipelines_ids method."""

    @pytest.mark.asyncio
    async def test_get_active_pipelines_ids_success(
        self, async_client: AiriaAsyncClient
    ):
        """Test successful retrieval of active pipeline IDs."""
        with patch.object(async_client, "_make_request") as mock_request:
            mock_request.return_value = SAMPLE_PIPELINE_IDS

            result = await async_client.get_active_pipelines_ids()

            assert result == ["pipeline-id-1", "pipeline-id-2", "pipeline-id-3"]
            assert isinstance(result, list)
            assert len(result) == 3
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_pipelines_ids_empty_list(
        self, async_client: AiriaAsyncClient
    ):
        """Test handling of empty pipeline list response."""
        with patch.object(async_client, "_make_request") as mock_request:
            mock_request.return_value = []

            result = await async_client.get_active_pipelines_ids()

            assert result == []
            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_active_pipelines_ids_with_custom_params(
        self, async_client: AiriaAsyncClient
    ):
        """Test using custom API version and correlation ID."""
        custom_correlation_id = "async-test-correlation-456"

        with patch.object(async_client, "_make_request") as mock_request:
            mock_request.return_value = SAMPLE_PIPELINE_IDS

            result = await async_client.get_active_pipelines_ids(
                api_version="v1", correlation_id=custom_correlation_id
            )

            assert result == ["pipeline-id-1", "pipeline-id-2", "pipeline-id-3"]
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_pipelines_ids_invalid_api_version(
        self, async_client: AiriaAsyncClient
    ):
        """Test error handling for invalid API version."""
        with pytest.raises(ValueError, match="Invalid API version"):
            await async_client.get_active_pipelines_ids(api_version="invalid")

    @pytest.mark.asyncio
    async def test_get_active_pipelines_ids_api_error(
        self, async_client: AiriaAsyncClient
    ):
        """Test error handling for API errors."""
        with patch.object(async_client, "_make_request") as mock_request:
            mock_request.side_effect = AiriaAPIError(
                status_code=403, message="Access forbidden"
            )

            with pytest.raises(AiriaAPIError) as exc_info:
                await async_client.get_active_pipelines_ids()

            assert "Access forbidden" in str(exc_info.value)
            assert exc_info.value.status_code == 403
