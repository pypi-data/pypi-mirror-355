from unittest.mock import patch

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from airia import AiriaAPIError, AiriaAsyncClient, AiriaClient
from airia.types import GetPipelineConfigResponse

# Load environment variables for testing
load_dotenv()
PYTHON_PIPELINE = "0134da17-c5a5-4730-a576-92f8eaf0926f"


@pytest.fixture
def sync_client():
    return AiriaClient(log_requests=True)


@pytest_asyncio.fixture
async def async_client():
    return AiriaAsyncClient(log_requests=True)


# Mock response data for testing
MOCK_PIPELINE_CONFIG_RESPONSE = {
    "metadata": {
        "id": "17554b31-2370-4d2d-91de-4fe4805b9ef9",
        "exportVersion": "20250612041452_AddAiInternalMcpServerActionsToUsage",
        "tagline": "",
        "agentDescription": "",
        "industry": "",
        "tasks": "",
        "credentialExportOption": "Placeholder",
        "dataSourceExportOption": "Placeholder",
        "versionInformation": "7.00",
        "state": "Preview",
    },
    "agent": {
        "name": "Omni Agent - Test Agent to be Described",
        "executionName": "untitled_agent_%281%29",
        "agentDescription": "",
        "videoLink": None,
        "industry": None,
        "subIndustries": [],
        "agentDetails": {},
        "id": "17554b31-2370-4d2d-91de-4fe4805b9ef9",
        "agentIcon": None,
        "steps": [
            {
                "id": "1d180b16-d097-45e8-bf3a-031a4c4b959d",
                "stepType": "pythonStep",
                "position": {"x": "12", "y": "378"},
                "handles": [
                    {
                        "uuid": "c75a1538-8ff5-4abb-acfd-d0554738e34f",
                        "type": "target",
                        "label": "",
                        "tooltip": "",
                        "x": 87,
                        "y": -3,
                    },
                    {
                        "uuid": "9734a974-9d0c-486b-b00d-aa2135c62bbc",
                        "type": "source",
                        "label": "",
                        "tooltip": "",
                        "x": 87,
                        "y": 53.299988,
                    },
                ],
                "dependenciesObject": [
                    {
                        "parentId": "f896b741-87d5-49de-92f9-881677da1dca",
                        "parentHandleId": "7099c54b-ebd1-46a4-b1b8-602ccbbab1d5",
                        "handleId": "c75a1538-8ff5-4abb-acfd-d0554738e34f",
                    }
                ],
                "pythonCodeBlockId": "1d180b16-d097-45e8-bf3a-031a4c4b959d",
                "stepTitle": "Python Code",
            },
            {
                "id": "5a03ca6c-8b1c-4cee-bad2-32507e767e41",
                "stepType": "outputStep",
                "position": {"x": "507", "y": "790"},
                "handles": [
                    {
                        "uuid": "04c6e2b3-b430-45bb-9bff-bb9e5b0ecdbb",
                        "type": "target",
                        "label": "",
                        "tooltip": "",
                        "x": 57,
                        "y": -3,
                    }
                ],
                "dependenciesObject": [
                    {
                        "parentId": "ac6467bf-999d-4aab-a747-73fa0c96b01e",
                        "parentHandleId": "36ddab85-8bdd-433b-9516-35391bc363da",
                        "handleId": "04c6e2b3-b430-45bb-9bff-bb9e5b0ecdbb",
                    }
                ],
                "stepTitle": "Output",
            },
            {
                "id": "9f6f9f66-712f-497d-bffd-3fe2823bd7ab",
                "stepType": "inputStep",
                "position": {"x": "483", "y": "12"},
                "handles": [
                    {
                        "uuid": "64b87a80-7e5c-47c5-8819-a2b0f780e600",
                        "type": "source",
                        "label": "",
                        "tooltip": "",
                        "x": 69,
                        "y": 39.300003,
                    }
                ],
                "dependenciesObject": [],
                "stepTitle": "Input",
            },
            {
                "id": "ac6467bf-999d-4aab-a747-73fa0c96b01e",
                "stepType": "AIOperation",
                "position": {"x": "447", "y": "584"},
                "handles": [
                    {
                        "uuid": "36ddab85-8bdd-433b-9516-35391bc363da",
                        "type": "source",
                        "label": "",
                        "tooltip": "",
                        "x": 87,
                        "y": 62.69998,
                    },
                    {
                        "uuid": "9921db77-05b9-4129-8a18-0c55a2ac038d",
                        "type": "target",
                        "label": "",
                        "tooltip": "",
                        "x": 87,
                        "y": -3,
                    },
                ],
                "dependenciesObject": [
                    {
                        "parentId": "1d180b16-d097-45e8-bf3a-031a4c4b959d",
                        "parentHandleId": "9734a974-9d0c-486b-b00d-aa2135c62bbc",
                        "handleId": "9921db77-05b9-4129-8a18-0c55a2ac038d",
                    },
                    {
                        "parentId": "ddd98da0-e1c7-42c1-abdf-8c4bf86d6fc2",
                        "parentHandleId": "a8988cf5-03ba-427c-9793-60173b7ab23d",
                        "handleId": "9921db77-05b9-4129-8a18-0c55a2ac038d",
                    },
                    {
                        "parentId": "f896b741-87d5-49de-92f9-881677da1dca",
                        "parentHandleId": "7099c54b-ebd1-46a4-b1b8-602ccbbab1d5",
                        "handleId": "9921db77-05b9-4129-8a18-0c55a2ac038d",
                    },
                ],
                "temperature": 0.7,
                "includeDateTimeContext": False,
                "promptId": "cfce7cf4-0ba3-47fd-9376-1138fd44ad45",
                "modelId": "4c511bda-95f6-4717-b210-0b9b4e331720",
                "toolIds": ["01976577-2452-7d96-815b-d590e7f16364"],
                "toolParams": {},
                "stepTitle": "AI Model 1",
            },
            {
                "id": "ddd98da0-e1c7-42c1-abdf-8c4bf86d6fc2",
                "stepType": "dataSearch",
                "position": {"x": "447", "y": "360"},
                "handles": [
                    {
                        "uuid": "a8988cf5-03ba-427c-9793-60173b7ab23d",
                        "type": "source",
                        "label": "",
                        "tooltip": "",
                        "x": 87,
                        "y": 71.29999,
                    },
                    {
                        "uuid": "427c9f8b-3b7d-4a52-a76f-9ce23548caac",
                        "type": "target",
                        "label": "",
                        "tooltip": "",
                        "x": 87,
                        "y": -3,
                    },
                ],
                "dependenciesObject": [
                    {
                        "parentId": "f896b741-87d5-49de-92f9-881677da1dca",
                        "parentHandleId": "7099c54b-ebd1-46a4-b1b8-602ccbbab1d5",
                        "handleId": "427c9f8b-3b7d-4a52-a76f-9ce23548caac",
                    }
                ],
                "dataSourceId": "01976170-1aa6-7900-8b6d-238bb32caa35",
                "topK": 5,
                "relevanceThreshold": 20,
                "neighboringChunksCount": 1,
                "hybridSearchAlpha": 0.5,
                "databaseType": "",
                "stepTitle": "Data Source",
            },
            {
                "id": "f896b741-87d5-49de-92f9-881677da1dca",
                "stepType": "routerStep",
                "position": {"x": "447", "y": "172"},
                "handles": [
                    {
                        "uuid": "8f4953a3-fe39-4b4c-bfbd-31ea473862f5",
                        "type": "target",
                        "label": "",
                        "tooltip": "",
                        "x": 87,
                        "y": -3,
                    },
                    {
                        "uuid": "7099c54b-ebd1-46a4-b1b8-602ccbbab1d5",
                        "type": "source",
                        "label": "Route 1",
                        "tooltip": "",
                        "x": 87,
                        "y": 53.299988,
                    },
                ],
                "dependenciesObject": [
                    {
                        "parentId": "9f6f9f66-712f-497d-bffd-3fe2823bd7ab",
                        "parentHandleId": "64b87a80-7e5c-47c5-8819-a2b0f780e600",
                        "handleId": "8f4953a3-fe39-4b4c-bfbd-31ea473862f5",
                    }
                ],
                "stepTitle": "Router",
            },
        ],
    },
    "dataSources": [],
    "prompts": [
        {
            "name": "Helpful Agent",
            "versionChangeDescription": "Initial version",
            "promptMessageList": [{"text": "You are a helpful agent.", "order": 0}],
            "id": "cfce7cf4-0ba3-47fd-9376-1138fd44ad45",
        }
    ],
    "tools": [
        {
            "toolType": "YoutubeSearch",
            "name": "Search Youtube",
            "standardizedName": "search_youtube",
            "toolDescription": "Search YouTube for videos on a specific subject",
            "purpose": "To search YouTube for videos on a specific subject",
            "apiEndpoint": "https://www.googleapis.com/youtube/v3/search?part=snippet&q=<Subject/>&maxResults=<maxResults/>",
            "credentialsDefinition": {
                "name": "YoutubeSearch",
                "credentialType": "Youtube",
                "sourceType": "library",
                "credentialDataList": [
                    {"key": "youtubeApiKey", "value": "**placeholder**"}
                ],
                "id": "4be7b206-c5be-405e-af59-ba292cd68bd9",
            },
            "headersDefinition": [{"key": "Accept", "value": "application/json"}],
            "body": "",
            "parametersDefinition": [
                {
                    "name": "Subject",
                    "parameterType": "string",
                    "parameterDescription": "The subject to search for",
                    "default": "",
                    "validOptions": [],
                    "id": "00000000-0000-0000-0000-000000000000",
                },
                {
                    "name": "maxResults",
                    "parameterType": "integer",
                    "parameterDescription": "The maximum number of results to return. If no values is provided from the user the default value is 5. If a value requested is less than 5 set it to 5.",
                    "default": "",
                    "validOptions": [],
                    "id": "00000000-0000-0000-0000-000000000000",
                },
            ],
            "methodType": "GET",
            "routeThroughACC": False,
            "useUserCredentials": False,
            "useUserCredentialsType": "YoutubeKey",
            "id": "01976577-2452-7d96-815b-d590e7f16364",
        }
    ],
    "models": [
        {
            "id": "4c511bda-95f6-4717-b210-0b9b4e331720",
            "displayName": "GPT 4.1",
            "modelName": "gpt-4.1-2025-04-14",
            "promptId": None,
            "systemPromptDefinition": None,
            "url": "https://api.openai.com/v1/chat/completions",
            "inputType": "image",
            "provider": "OpenAI",
            "credentialsDefinition": {
                "name": "OpenAI",
                "credentialType": "OpenAI",
                "sourceType": "library",
                "credentialDataList": [
                    {"key": "openaiApiKey", "value": "**placeholder**"}
                ],
                "id": "580e51d7-b4b0-410c-86ff-11e34cee1242",
            },
            "deploymentType": "marketplace",
            "sourceType": "library",
            "connectionString": None,
            "containerName": None,
            "deployedKey": None,
            "deployedUrl": None,
            "state": None,
            "uploadedContainerId": None,
            "libraryModelId": "7e9a1b22-3c5f-4a57-a9d4-8b6d1e5f8a27",
            "inputTokenPrice": "0.00000206",
            "outputTokenPrice": "0.00000824",
            "tokenUnits": 1000,
            "hasToolSupport": True,
            "allowAiriaCredentials": True,
            "allowBYOKCredentials": True,
            "author": "OpenAI",
            "priceType": "AITextOutputModelPrice",
        }
    ],
    "memories": None,
    "pythonCodeBlocks": [
        {
            "id": "1d180b16-d097-45e8-bf3a-031a4c4b959d",
            "code": "output = \"Always start your response with 'Let's do this!'\"",
        }
    ],
    "routers": [
        {
            "id": "f896b741-87d5-49de-92f9-881677da1dca",
            "modelId": "2e005300-b320-40ff-af41-b641486b559c",
            "model": None,
            "routerConfig": {
                "7099c54b-ebd1-46a4-b1b8-602ccbbab1d5": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "prompt": "",
                    "isDefault": True,
                }
            },
        }
    ],
    "deployment": None,
}


class TestSyncGetPipelineConfig:
    """Test cases for synchronous get_pipeline_config method."""

    def test_get_pipeline_config_success(self, sync_client: AiriaClient):
        """Test successful pipeline configuration retrieval."""
        response = sync_client.get_pipeline_config(pipeline_id=PYTHON_PIPELINE)
        # Verify the response is properly typed
        assert isinstance(response, GetPipelineConfigResponse)

    def test_get_pipeline_config_with_custom_api_version(
        self, sync_client: AiriaClient
    ):
        """Test pipeline configuration retrieval with custom API version."""
        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.return_value = MOCK_PIPELINE_CONFIG_RESPONSE

            response = sync_client.get_pipeline_config(
                pipeline_id="test-pipeline-123", api_version="v1"
            )

            assert isinstance(response, GetPipelineConfigResponse)

    def test_get_pipeline_config_with_correlation_id(self, sync_client: AiriaClient):
        """Test pipeline configuration retrieval with custom correlation ID."""
        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.return_value = MOCK_PIPELINE_CONFIG_RESPONSE

            custom_correlation_id = "test-correlation-123"
            response = sync_client.get_pipeline_config(
                pipeline_id="test-pipeline-123", correlation_id=custom_correlation_id
            )

            assert isinstance(response, GetPipelineConfigResponse)

    def test_get_pipeline_config_invalid_api_version(self, sync_client: AiriaClient):
        """Test that invalid API version raises ValueError."""
        with pytest.raises(ValueError, match="Invalid API version"):
            sync_client.get_pipeline_config(
                pipeline_id="test-pipeline-123", api_version="invalid_version"
            )

    def test_get_pipeline_config_api_error(self, sync_client: AiriaClient):
        """Test handling of API errors."""
        with patch.object(sync_client, "_make_request") as mock_request:
            mock_request.side_effect = AiriaAPIError(
                status_code=404, message="Pipeline not found"
            )

            with pytest.raises(AiriaAPIError) as exc_info:
                sync_client.get_pipeline_config(pipeline_id="nonexistent-pipeline")

            assert exc_info.value.status_code == 404
            assert "Pipeline not found" in str(exc_info.value)


class TestAsyncGetPipelineConfig:
    """Test cases for asynchronous get_pipeline_config method."""

    @pytest.mark.asyncio
    async def test_get_pipeline_config_success(self, async_client: AiriaAsyncClient):
        """Test successful asynchronous pipeline configuration retrieval."""
        response = await async_client.get_pipeline_config(pipeline_id=PYTHON_PIPELINE)

        # Verify the response is properly typed
        assert isinstance(response, GetPipelineConfigResponse)

    @pytest.mark.asyncio
    async def test_get_pipeline_config_with_custom_params(
        self, async_client: AiriaAsyncClient
    ):
        """Test asynchronous pipeline configuration retrieval with custom parameters."""
        with patch.object(async_client, "_make_request") as mock_request:
            mock_request.return_value = MOCK_PIPELINE_CONFIG_RESPONSE

            response = await async_client.get_pipeline_config(
                pipeline_id="test-pipeline-123",
                api_version="v1",
                correlation_id="async-test-correlation",
            )

            assert isinstance(response, GetPipelineConfigResponse)

    @pytest.mark.asyncio
    async def test_get_pipeline_config_api_error(self, async_client: AiriaAsyncClient):
        """Test handling of API errors in async context."""
        with patch.object(async_client, "_make_request") as mock_request:
            mock_request.side_effect = AiriaAPIError(
                status_code=403, message="Access forbidden"
            )

            with pytest.raises(AiriaAPIError) as exc_info:
                await async_client.get_pipeline_config(pipeline_id="forbidden-pipeline")

            assert exc_info.value.status_code == 403
            assert "Access forbidden" in str(exc_info.value)
