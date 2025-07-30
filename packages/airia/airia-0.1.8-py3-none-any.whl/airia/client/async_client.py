import asyncio
import weakref
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, overload
from urllib.parse import urljoin

import aiohttp
import loguru

from ..exceptions import AiriaAPIError
from ..types import (
    ApiVersion,
    GetPipelineConfigResponse,
    PipelineExecutionDebugResponse,
    PipelineExecutionResponse,
    PipelineExecutionV1StreamedResponse,
    PipelineExecutionV2AsyncStreamedResponse,
    RequestData,
)
from ..utils.sse_parser import async_parse_sse_stream_chunked
from .base_client import AiriaBaseClient


class AiriaAsyncClient(AiriaBaseClient):
    """Asynchronous client for interacting with the Airia API."""

    def __init__(
        self,
        base_url: str = "https://api.airia.ai/",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        log_requests: bool = False,
        custom_logger: Optional["loguru.Logger"] = None,
    ):
        """
        Initialize the asynchronous Airia API client.

        Args:
            base_url: Base URL of the Airia API.
            api_key: API key for authentication. If not provided, will attempt to use AIRIA_API_KEY environment variable.
            timeout: Request timeout in seconds.
            log_requests: Whether to log API requests and responses. Default is False.
            custom_logger: Optional custom logger object to use for logging. If not provided, will use a default logger when `log_requests` is True.
        """
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            log_requests=log_requests,
            custom_logger=custom_logger,
        )

        # Session will be initialized in __aenter__
        self.headers = {"Content-Type": "application/json"}
        self.session = aiohttp.ClientSession(headers=self.headers)

        # Register finalizer to clean up session when client is garbage collected
        self._finalizer = weakref.finalize(self, self._cleanup_session, self.session)

    @staticmethod
    def _cleanup_session(session: aiohttp.ClientSession):
        """Static method to clean up session - called by finalizer"""
        if session and not session.closed:
            # Create a new event loop if none exists
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Close the session
            if not loop.is_running():
                loop.run_until_complete(session.close())
            else:
                # If loop is running, schedule the close operation
                asyncio.create_task(session.close())

    @classmethod
    def with_openai_gateway(
        cls,
        base_url: str = "https://api.airia.ai/",
        gateway_url: str = "https://gateway.airia.ai/openai/v1",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        log_requests: bool = False,
        custom_logger: Optional["loguru.Logger"] = None,
        **kwargs,
    ):
        """
        Initialize the asynchronous Airia API client with AsyncOpenAI gateway capabilities.

        Args:
            base_url: Base URL of the Airia API.
            gateway_url: Base URL of the Airia Gateway API.
            api_key: API key for authentication. If not provided, will attempt to use AIRIA_API_KEY environment variable.
            timeout: Request timeout in seconds.
            log_requests: Whether to log API requests and responses. Default is False.
            custom_logger: Optional custom logger object to use for logging. If not provided, will use a default logger when `log_requests` is True.
            **kwargs: Additional keyword arguments to pass to the AsyncOpenAI client initialization.
        """
        from openai import AsyncOpenAI

        api_key = cls._get_api_key(api_key)
        cls.openai = AsyncOpenAI(
            api_key=api_key,
            base_url=gateway_url,
            **kwargs,
        )

        return cls(base_url, api_key, timeout, log_requests, custom_logger)

    @classmethod
    def with_anthropic_gateway(
        cls,
        base_url: str = "https://api.airia.ai/",
        gateway_url: str = "https://gateway.airia.ai/anthropic",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        log_requests: bool = False,
        custom_logger: Optional["loguru.Logger"] = None,
        **kwargs,
    ):
        """
        Initialize the asynchronous Airia API client with AsyncAnthropic gateway capabilities.

        Args:
            base_url: Base URL of the Airia API.
            gateway_url: Base URL of the Airia Gateway API.
            api_key: API key for authentication. If not provided, will attempt to use AIRIA_API_KEY environment variable.
            timeout: Request timeout in seconds.
            log_requests: Whether to log API requests and responses. Default is False.
            custom_logger: Optional custom logger object to use for logging. If not provided, will use a default logger when `log_requests` is True.
            **kwargs: Additional keyword arguments to pass to the AsyncAnthropic client initialization.
        """
        from anthropic import AsyncAnthropic

        api_key = cls._get_api_key(api_key)
        cls.anthropic = AsyncAnthropic(
            api_key=api_key,
            base_url=gateway_url,
            **kwargs,
        )

        return cls(base_url, api_key, timeout, log_requests, custom_logger)

    def _handle_exception(
        self, e: aiohttp.ClientResponseError, url: str, correlation_id: str
    ):
        # Log the error response if enabled
        if self.log_requests:
            self.logger.error(
                f"API Error: {e.status} {e.message}\n"
                f"URL: {url}\n"
                f"Correlation ID: {correlation_id}"
            )

        # Extract error details from response
        error_message = e.message

        # Make sure API key is not included in error messages
        sanitized_message = (
            error_message.replace(self.api_key, "[REDACTED]")
            if self.api_key in error_message
            else error_message
        )

        # Raise custom exception with status code and sanitized message
        raise AiriaAPIError(status_code=e.status, message=sanitized_message) from e

    async def _make_request(
        self, method: str, request_data: RequestData
    ) -> Dict[str, Any]:
        """
        Makes an asynchronous HTTP request to the Airia API.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST')
            request_data: A dictionary containing the following request information:
                - url: The endpoint URL for the request
                - headers: HTTP headers to include in the request
                - payload: The JSON payload/body for the request
                - correlation_id: Unique identifier for request tracing

        Returns:
            resp ([Dict[str, Any]): The JSON response from the API as a dictionary.

        Raises:
            AiriaAPIError: If the API returns an error response, with details about the error
            aiohttp.ClientResponseError: For HTTP-related errors

        Note:
            This is an internal method used by other client methods to make API requests.
            It handles logging, error handling, and API key redaction in error messages.
        """
        try:
            # Make the request
            async with self.session.request(
                method=method,
                url=request_data.url,
                json=request_data.payload,
                headers=request_data.headers,
                timeout=self.timeout,
            ) as response:
                # Log the response if enabled
                if self.log_requests:
                    self.logger.info(
                        f"API Response: {response.status} {response.reason}\n"
                        f"URL: {request_data.url}\n"
                        f"Correlation ID: {request_data.correlation_id}"
                    )

                # Check for HTTP errors
                response.raise_for_status()

                # Return the response as a dictionary
                return await response.json()

        except aiohttp.ClientResponseError as e:
            self._handle_exception(e, request_data.url, request_data.correlation_id)

    async def _make_request_stream(
        self, method: str, request_data: RequestData
    ) -> AsyncIterator[str]:
        """
        Makes an asynchronous HTTP request to the Airia API.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST')
            request_data: A dictionary containing the following request information:
                - url: The endpoint URL for the request
                - headers: HTTP headers to include in the request
                - payload: The JSON payload/body for the request
                - correlation_id: Unique identifier for request tracing

        Yields:
            resp AsyncIterator[str]]: yields chunks of the response as they are received.

        Raises:
            AiriaAPIError: If the API returns an error response, with details about the error
            aiohttp.ClientResponseError: For HTTP-related errors

        Note:
            This is an internal method used by other client methods to make API requests.
            It handles logging, error handling, and API key redaction in error messages.
        """
        try:
            # Make the request
            async with self.session.request(
                method=method,
                url=request_data.url,
                json=request_data.payload,
                headers=request_data.headers,
                timeout=self.timeout,
                chunked=True,
            ) as response:
                # Log the response if enabled
                if self.log_requests:
                    self.logger.info(
                        f"API Response: {response.status} {response.reason}\n"
                        f"URL: {request_data.url}\n"
                        f"Correlation ID: {request_data.correlation_id}"
                    )

                # Check for HTTP errors
                response.raise_for_status()

                # Yields the response content as a stream if streaming
                async for message in async_parse_sse_stream_chunked(
                    response.content.iter_any()
                ):
                    yield message

        except aiohttp.ClientResponseError as e:
            self._handle_exception(e, request_data.url, request_data.correlation_id)

    @overload
    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_input: str,
        debug: Literal[False] = False,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        async_output: Literal[False] = False,
        include_tools_response: bool = False,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        data_source_folders: Optional[Dict[str, Any]] = None,
        data_source_files: Optional[Dict[str, Any]] = None,
        in_memory_messages: Optional[List[Dict[str, str]]] = None,
        current_date_time: Optional[str] = None,
        save_history: bool = True,
        additional_info: Optional[List[Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        api_version: str = ApiVersion.V2.value,
    ) -> PipelineExecutionResponse: ...

    @overload
    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_input: str,
        debug: Literal[True] = True,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        async_output: Literal[False] = False,
        include_tools_response: bool = False,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        data_source_folders: Optional[Dict[str, Any]] = None,
        data_source_files: Optional[Dict[str, Any]] = None,
        in_memory_messages: Optional[List[Dict[str, str]]] = None,
        current_date_time: Optional[str] = None,
        save_history: bool = True,
        additional_info: Optional[List[Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        api_version: str = ApiVersion.V2.value,
    ) -> PipelineExecutionDebugResponse: ...

    @overload
    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_input: str,
        debug: bool = False,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        async_output: Literal[True] = True,
        include_tools_response: bool = False,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        data_source_folders: Optional[Dict[str, Any]] = None,
        data_source_files: Optional[Dict[str, Any]] = None,
        in_memory_messages: Optional[List[Dict[str, str]]] = None,
        current_date_time: Optional[str] = None,
        save_history: bool = True,
        additional_info: Optional[List[Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        api_version: Literal["v2"] = ApiVersion.V2.value,
    ) -> PipelineExecutionV2AsyncStreamedResponse: ...

    @overload
    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_input: str,
        debug: bool = False,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        async_output: Literal[True] = True,
        include_tools_response: bool = False,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        data_source_folders: Optional[Dict[str, Any]] = None,
        data_source_files: Optional[Dict[str, Any]] = None,
        in_memory_messages: Optional[List[Dict[str, str]]] = None,
        current_date_time: Optional[str] = None,
        save_history: bool = True,
        additional_info: Optional[List[Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        api_version: Literal["v1"] = ApiVersion.V1.value,
    ) -> PipelineExecutionV1StreamedResponse: ...

    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_input: str,
        debug: bool = False,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        async_output: bool = False,
        include_tools_response: bool = False,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        data_source_folders: Optional[Dict[str, Any]] = None,
        data_source_files: Optional[Dict[str, Any]] = None,
        in_memory_messages: Optional[List[Dict[str, str]]] = None,
        current_date_time: Optional[str] = None,
        save_history: bool = True,
        additional_info: Optional[List[Any]] = None,
        prompt_variables: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        api_version: str = ApiVersion.V2.value,
    ) -> Dict[str, Any]:
        """
        Execute a pipeline with the provided input asynchronously.

        Args:
            pipeline_id: The ID of the pipeline to execute.
            user_input: input text to process.
            debug: Whether debug mode execution is enabled. Default is False.
            user_id: Optional ID of the user making the request (guid).
            conversation_id: Optional conversation ID (guid).
            async_output: Whether to stream the response. Default is False.
            include_tools_response: Whether to return the initial LLM tool result. Default is False.
            images: Optional list of images formatted as base64 strings.
            files: Optional list of files formatted as base64 strings.
            data_source_folders: Optional data source folders information.
            data_source_files: Optional data source files information.
            in_memory_messages: Optional list of in-memory messages, each with a role and message.
            current_date_time: Optional current date and time in ISO format.
            save_history: Whether to save the userInput and output to conversation history. Default is True.
            additional_info: Optional additional information.
            prompt_variables: Optional variables to be used in the prompt.
            correlation_id: Optional correlation ID for request tracing. If not provided,
                        one will be generated automatically.
            api_version: API version to use. Default is `v2`

        Returns:
            The API response as a dictionary.

        Raises:
            AiriaAPIError: If the API request fails with details about the error.
            aiohttp.ClientError: For other request-related errors.

        Example:
            >>> async with AiriaAsyncClient(api_key="your_api_key") as client:
            ...     response = await client.execute_pipeline(
            ...         pipeline_id="pipeline_123",
            ...         user_input="Tell me about quantum computing"
            ...     )
            >>> print(response.result)
        """
        request_data = self._pre_execute_pipeline(
            pipeline_id=pipeline_id,
            user_input=user_input,
            debug=debug,
            user_id=user_id,
            conversation_id=conversation_id,
            async_output=async_output,
            include_tools_response=include_tools_response,
            images=images,
            files=files,
            data_source_folders=data_source_folders,
            data_source_files=data_source_files,
            in_memory_messages=in_memory_messages,
            current_date_time=current_date_time,
            save_history=save_history,
            additional_info=additional_info,
            prompt_variables=prompt_variables,
            correlation_id=correlation_id,
            api_version=api_version,
        )
        stream = async_output and api_version == ApiVersion.V2.value
        if stream:
            resp = self._make_request_stream(method="POST", request_data=request_data)
        else:
            resp = await self._make_request("POST", request_data)

        if not async_output:
            if not debug:
                return PipelineExecutionResponse(**resp)
            return PipelineExecutionDebugResponse(**resp)

        if api_version == ApiVersion.V1.value:
            url = urljoin(
                self.base_url, f"{api_version}/StreamSocketConfig/GenerateUrl"
            )
            request_data = self._prepare_request(
                url,
                {"socketIdentifier": resp},
                request_data.headers["X-Correlation-ID"],
            )
            resp = await self._make_request("POST", request_data)

            return PipelineExecutionV1StreamedResponse(**resp)

        return PipelineExecutionV2AsyncStreamedResponse(stream=resp)

    async def get_active_pipelines_ids(
        self,
        correlation_id: Optional[str] = None,
        api_version: str = ApiVersion.V1.value,
    ) -> List[str]:
        """
        Retrieve a list of active pipeline IDs.
        
        This method fetches all currently active pipeline IDs from the Airia API.
        These IDs can be used with other methods like execute_pipeline() or 
        get_pipeline_config().
        
        Args:
            api_version (str, optional): API version to use for the request. 
                Must be one of the supported versions. Defaults to "v1".
            correlation_id (str, optional): Unique identifier for request tracing
                and logging. If not provided, a new UUID will be automatically 
                generated.
        
        Returns:
            List[str]: A list of active pipeline ID strings. Returns an empty list
                if no active pipelines are found.
        
        Raises:
            ValueError: If the provided API version is not supported.
            AiriaAPIError: If the API request fails, including network errors,
                authentication failures, or server errors.
        
        Example:
            >>> client = AiriaClient(api_key="your_api_key")
            >>> pipeline_ids = client.get_active_pipelines_ids()
            >>> print(f"Found {len(pipeline_ids)} active pipelines")
            >>> for pipeline_id in pipeline_ids:
            ...     print(f"Pipeline ID: {pipeline_id}")
        """
        request_data = self._pre_get_active_pipelines_ids(
            correlation_id=correlation_id, api_version=api_version
        )
        resp = await self._make_request("GET", request_data)

        if "items" not in resp or len(resp["items"]) == 0:
            return []

        pipeline_ids = [r["activeVersion"]["pipelineId"] for r in resp["items"]]

        return pipeline_ids

    async def get_pipeline_config(
        self,
        pipeline_id: str,
        correlation_id: Optional[str] = None,
        api_version: str = ApiVersion.V1.value,
    ) -> GetPipelineConfigResponse:
        """
        Retrieve configuration details for a specific pipeline.

        This method fetches comprehensive information about a pipeline including its
        deployment details, execution statistics, version information, and metadata.

        Args:
            pipeline_id (str): The unique identifier of the pipeline to retrieve
                configuration for.
            api_version (str, optional): The API version to use for the request.
                Defaults to "v1". Valid versions are defined in ApiVersion enum.
            correlation_id (str, optional): A unique identifier for request tracing
                and logging. If not provided, one will be automatically generated.

        Returns:
            GetPipelineConfigResponse: A response object containing the pipeline
                configuration.

        Raises:
            ValueError: If the provided api_version is not valid.
            AiriaAPIError: If the API request fails, including cases where:
                - The pipeline_id doesn't exist (404)
                - Authentication fails (401)
                - Access is forbidden (403)
                - Server errors (5xx)

        Example:
            ```python
            from airia import AiriaClient

            client = AiriaClient(api_key="your_api_key")

            # Get pipeline configuration
            config = client.get_pipeline_config(
                pipeline_id="your_pipeline_id"
            )

            print(f"Pipeline: {config.deployment_name}")
            print(f"Description: {config.deployment_description}")
            print(f"Success rate: {config.execution_stats.success_count}")
            print(f"Active version: {config.active_version.version_number}")
            ```

        Note:
            This method only retrieves configuration information and does not
            execute the pipeline. Use execute_pipeline() to run the pipeline.
        """
        request_data = self._pre_get_pipeline_config(
            pipeline_id=pipeline_id,
            correlation_id=correlation_id,
            api_version=api_version,
        )
        resp = await self._make_request("GET", request_data)

        return GetPipelineConfigResponse(**resp)
