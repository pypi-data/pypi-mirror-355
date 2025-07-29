import json
import re
from typing import AsyncIterable, AsyncIterator, Iterable, Iterator

from ..types.sse_messages import SSEDict, SSEMessage


def _to_snake_case(name: str):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def parse_sse_stream_chunked(stream_chunks: Iterable[bytes]) -> Iterator[SSEMessage]:
    """
    Parse SSE stream from an iterable of chunks (e.g., from a streaming response).

    Args:
        stream_chunks: Iterable of string chunks

    Yields:
        dict: Dictionary containing 'event' and 'data' keys
    """
    buffer = ""

    for chunk in stream_chunks:
        buffer += chunk.decode("utf-8")

        # Look for complete events (ending with double newline)
        while "\n\n" in buffer:
            event_block, buffer = buffer.split("\n\n", 1)

            if not event_block.strip():
                continue

            event_name = None
            event_data = None

            # Parse each line in the event block
            for line in event_block.strip().split("\n"):
                line = line.strip()
                if line.startswith("event:"):
                    event_name = line[6:].strip()
                elif line.startswith("data:"):
                    data_json = line[5:].strip()
                    event_data = json.loads(data_json)

            if event_name and event_data:
                yield SSEDict[event_name](
                    **{_to_snake_case(k): v for k, v in event_data.items()}
                )


async def async_parse_sse_stream_chunked(
    stream_chunks: AsyncIterable[bytes],
) -> AsyncIterator[SSEMessage]:
    """
    Parse SSE stream from an iterable of chunks (e.g., from a streaming response).

    Args:
        stream_chunks: Iterable of string chunks

    Yields:
        dict: Dictionary containing 'event' and 'data' keys
    """
    buffer = ""

    async for chunk in stream_chunks:
        buffer += chunk.decode("utf-8")

        # Look for complete events (ending with double newline)
        while "\n\n" in buffer:
            event_block, buffer = buffer.split("\n\n", 1)

            if not event_block.strip():
                continue

            event_name = None
            event_data = None

            # Parse each line in the event block
            for line in event_block.strip().split("\n"):
                line = line.strip()
                if line.startswith("event:"):
                    event_name = line[6:].strip()
                elif line.startswith("data:"):
                    data_json = line[5:].strip()
                    event_data = json.loads(data_json)

            if event_name and event_data:
                yield SSEDict[event_name](
                    **{_to_snake_case(k): v for k, v in event_data.items()}
                )
