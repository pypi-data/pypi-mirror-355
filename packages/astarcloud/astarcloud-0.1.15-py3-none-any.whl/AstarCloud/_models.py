from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict


# -- Tool-calling models ----------------------------------
class ToolSpec(BaseModel):
    type: Literal["function"] = "function"
    function: Dict[str, Any]


class ToolChoice(BaseModel):
    type: Literal["function"] = "function"
    function: Dict[str, str]         # {"name": "my_tool"}


class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: Dict[str, str]         # {"name": "my_tool", "arguments": "..."}


# -- Updated Message model ----------------------------------
class Message(BaseModel):
    model_config = ConfigDict(exclude_none=True)
    
    role: str
    content: Optional[str] = None  # Allow None when tool calls are present
    tool_calls: Optional[List[ToolCall]] = None  # Tool calls belong in the message
    tool_call_id: Optional[str] = None  # Required for tool role messages


# -- Updated request/response models -------------------------
class CompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")  # catch-all for extra kwargs
    
    model: str
    messages: List[Message]
    stream: bool = False
    # New fields for tool calling
    tools: Optional[List[ToolSpec]] = None
    tool_choice: Optional[Union[str, ToolChoice]] = None


class Usage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None  # Allow None for cost_usd


class CompletionResponse(BaseModel):
    id: str
    created: int
    model: str
    message: Message
    finish_reason: Optional[str] = None
    usage: Optional[Usage] = None
    provider: Optional[str] = None
    response_ms: Optional[int] = None
    
    
class CompletionStreamResponse(BaseModel):
    id: str
    created: int
    model: str
    delta: Dict[str, Any]  # Streaming delta
    finish_reason: Optional[str] = None
    usage: Optional[Usage] = None
    provider: Optional[str] = None


# -- Transcription models ----------------------------------
class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionWord(BaseModel):
    word: str
    start: float
    end: float
    confidence: Optional[float] = None


class TranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None
    duration: Optional[float] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    response_ms: Optional[int] = None
    # For verbose_json format
    segments: Optional[List[TranscriptionSegment]] = None
    words: Optional[List[TranscriptionWord]] = None
