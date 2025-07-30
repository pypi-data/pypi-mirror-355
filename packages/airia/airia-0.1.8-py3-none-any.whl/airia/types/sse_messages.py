from datetime import datetime, time
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict


class MessageType(str, Enum):
    AGENT_PING = "AgentPingMessage"
    AGENT_START = "AgentStartMessage"
    AGENT_END = "AgentEndMessage"
    AGENT_STEP_START = "AgentStepStartMessage"
    AGENT_STEP_HALT = "AgentStepHaltMessage"
    AGENT_STEP_END = "AgentStepEndMessage"
    AGENT_OUTPUT = "AgentOutputMessage"
    AGENT_AGENT_CARD = "AgentAgentCardMessage"
    AGENT_DATASEARCH = "AgentDatasearchMessage"
    AGENT_INVOCATION = "AgentInvocationMessage"
    AGENT_MODEL = "AgentModelMessage"
    AGENT_PYTHON_CODE = "AgentPythonCodeMessage"
    AGENT_TOOL_ACTION = "AgentToolActionMessage"
    AGENT_MODEL_STREAM_START = "AgentModelStreamStartMessage"
    AGENT_MODEL_STREAM_END = "AgentModelStreamEndMessage"
    AGENT_MODEL_STREAM_ERROR = "AgentModelStreamErrorMessage"
    AGENT_MODEL_STREAM_USAGE = "AgentModelStreamUsageMessage"
    AGENT_MODEL_STREAM_FRAGMENT = "AgentModelStreamFragmentMessage"
    MODEL_STREAM_FRAGMENT = "ModelStreamFragment"
    AGENT_AGENT_CARD_STREAM_START = "AgentAgentCardStreamStartMessage"
    AGENT_AGENT_CARD_STREAM_ERROR = "AgentAgentCardStreamErrorMessage"
    AGENT_AGENT_CARD_STREAM_FRAGMENT = "AgentAgentCardStreamFragmentMessage"
    AGENT_AGENT_CARD_STREAM_END = "AgentAgentCardStreamEndMessage"
    AGENT_TOOL_REQUEST = "AgentToolRequestMessage"
    AGENT_TOOL_RESPONSE = "AgentToolResponseMessage"


class BaseSSEMessage(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    message_type: MessageType


class AgentPingMessage(BaseSSEMessage):
    message_type: MessageType = MessageType.AGENT_PING
    timestamp: datetime


### Agent Messages ###


class BaseAgentMessage(BaseSSEMessage):
    agent_id: str
    execution_id: str


class AgentStartMessage(BaseAgentMessage):
    message_type: MessageType = MessageType.AGENT_START


class AgentEndMessage(BaseAgentMessage):
    message_type: MessageType = MessageType.AGENT_END


### Step Messages ###


class BaseStepMessage(BaseAgentMessage):
    step_id: str
    step_type: str
    step_title: Optional[str] = None


class AgentStepStartMessage(BaseStepMessage):
    message_type: MessageType = MessageType.AGENT_STEP_START
    start_time: datetime


class AgentStepHaltMessage(BaseStepMessage):
    message_type: MessageType = MessageType.AGENT_STEP_HALT
    approval_id: str


class AgentStepEndMessage(BaseStepMessage):
    message_type: MessageType = MessageType.AGENT_STEP_END
    end_time: datetime
    duration: time
    status: str


class AgentOutputMessage(BaseStepMessage):
    message_type: MessageType = MessageType.AGENT_OUTPUT
    step_result: str


### Status Messages ###


class BaseStatusMessage(BaseStepMessage):
    pass


class AgentAgentCardMessage(BaseStatusMessage):
    message_type: MessageType = MessageType.AGENT_AGENT_CARD
    step_name: str


class AgentDatasearchMessage(BaseStatusMessage):
    message_type: MessageType = MessageType.AGENT_DATASEARCH
    datastore_id: str
    datastore_type: str
    datastore_name: str


class AgentInvocationMessage(BaseStatusMessage):
    message_type: MessageType = MessageType.AGENT_INVOCATION
    agent_name: str


class AgentModelMessage(BaseStatusMessage):
    message_type: MessageType = MessageType.AGENT_MODEL
    model_name: str


class AgentPythonCodeMessage(BaseStatusMessage):
    message_type: MessageType = MessageType.AGENT_PYTHON_CODE
    step_name: str


class AgentToolActionMessage(BaseStatusMessage):
    message_type: MessageType = MessageType.AGENT_TOOL_ACTION
    step_name: str
    tool_name: str


### Model Stream Messages ###


class BaseModelStreamMessage(BaseAgentMessage):
    step_id: str
    stream_id: str


class AgentModelStreamStartMessage(BaseModelStreamMessage):
    message_type: MessageType = MessageType.AGENT_MODEL_STREAM_START
    model_name: str


class AgentModelStreamErrorMessage(BaseModelStreamMessage):
    message_type: MessageType = MessageType.AGENT_MODEL_STREAM_ERROR
    error_message: str


class AgentModelStreamFragmentMessage(BaseModelStreamMessage):
    message_type: MessageType = MessageType.AGENT_MODEL_STREAM_FRAGMENT
    index: int
    content: Optional[str] = None


class AgentModelStreamEndMessage(BaseModelStreamMessage):
    message_type: MessageType = MessageType.AGENT_MODEL_STREAM_END
    content_id: str
    duration: Optional[float] = None


class AgentModelStreamUsageMessage(BaseModelStreamMessage):
    message_type: MessageType = MessageType.AGENT_MODEL_STREAM_USAGE
    token: Optional[int] = None
    tokens_cost: Optional[float] = None


### Agent Card Messages ###


class BaseAgentAgentCardStreamMessage(BaseAgentMessage):
    step_id: str
    stream_id: str


class AgentAgentCardStreamStartMessage(BaseAgentAgentCardStreamMessage):
    message_type: MessageType = MessageType.AGENT_AGENT_CARD_STREAM_START
    content: Optional[str] = None


class AgentAgentCardStreamErrorMessage(BaseAgentAgentCardStreamMessage):
    message_type: MessageType = MessageType.AGENT_AGENT_CARD_STREAM_ERROR
    error_message: str


class AgentAgentCardStreamFragmentMessage(BaseAgentAgentCardStreamMessage):
    message_type: MessageType = MessageType.AGENT_AGENT_CARD_STREAM_FRAGMENT
    index: int
    content: Optional[str]


class AgentAgentCardStreamEndMessage(BaseAgentAgentCardStreamMessage):
    message_type: MessageType = MessageType.AGENT_AGENT_CARD_STREAM_END
    content: Optional[str] = None


### Tool Messages ###


class BaseAgentToolMessage(BaseStepMessage):
    id: str
    name: str


class AgentToolRequestMessage(BaseAgentToolMessage):
    message_type: MessageType = MessageType.AGENT_TOOL_REQUEST


class AgentToolResponseMessage(BaseAgentToolMessage):
    message_type: MessageType = MessageType.AGENT_TOOL_RESPONSE
    duration: time
    success: bool


# Union type for all possible messages
SSEMessage = Union[
    AgentPingMessage,
    AgentStartMessage,
    AgentEndMessage,
    AgentStepStartMessage,
    AgentStepHaltMessage,
    AgentStepEndMessage,
    AgentOutputMessage,
    AgentAgentCardMessage,
    AgentDatasearchMessage,
    AgentInvocationMessage,
    AgentModelMessage,
    AgentPythonCodeMessage,
    AgentToolActionMessage,
    AgentModelStreamStartMessage,
    AgentModelStreamEndMessage,
    AgentModelStreamErrorMessage,
    AgentModelStreamUsageMessage,
    AgentModelStreamFragmentMessage,
    AgentAgentCardStreamStartMessage,
    AgentAgentCardStreamErrorMessage,
    AgentAgentCardStreamFragmentMessage,
    AgentAgentCardStreamEndMessage,
    AgentToolRequestMessage,
    AgentToolResponseMessage,
]

SSEDict = {
    MessageType.AGENT_PING.value: AgentPingMessage,
    MessageType.AGENT_START.value: AgentStartMessage,
    MessageType.AGENT_END.value: AgentEndMessage,
    MessageType.AGENT_STEP_START.value: AgentStepStartMessage,
    MessageType.AGENT_STEP_HALT.value: AgentStepHaltMessage,
    MessageType.AGENT_STEP_END.value: AgentStepEndMessage,
    MessageType.AGENT_OUTPUT.value: AgentOutputMessage,
    MessageType.AGENT_AGENT_CARD.value: AgentAgentCardMessage,
    MessageType.AGENT_DATASEARCH.value: AgentDatasearchMessage,
    MessageType.AGENT_INVOCATION.value: AgentInvocationMessage,
    MessageType.AGENT_MODEL.value: AgentModelMessage,
    MessageType.AGENT_PYTHON_CODE.value: AgentPythonCodeMessage,
    MessageType.AGENT_TOOL_ACTION.value: AgentToolActionMessage,
    MessageType.AGENT_MODEL_STREAM_START.value: AgentModelStreamStartMessage,
    MessageType.AGENT_MODEL_STREAM_END.value: AgentModelStreamEndMessage,
    MessageType.AGENT_MODEL_STREAM_ERROR.value: AgentModelStreamErrorMessage,
    MessageType.AGENT_MODEL_STREAM_USAGE.value: AgentModelStreamUsageMessage,
    MessageType.AGENT_MODEL_STREAM_FRAGMENT.value: AgentModelStreamFragmentMessage,
    MessageType.AGENT_AGENT_CARD_STREAM_START.value: AgentAgentCardStreamStartMessage,
    MessageType.AGENT_AGENT_CARD_STREAM_ERROR.value: AgentAgentCardStreamErrorMessage,
    MessageType.AGENT_AGENT_CARD_STREAM_FRAGMENT.value: AgentAgentCardStreamFragmentMessage,
    MessageType.AGENT_AGENT_CARD_STREAM_END.value: AgentAgentCardStreamEndMessage,
    MessageType.AGENT_TOOL_REQUEST.value: AgentToolRequestMessage,
    MessageType.AGENT_TOOL_RESPONSE.value: AgentToolResponseMessage,
}
