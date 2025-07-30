from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal
from google_a2a.common.types import JSONRPCRequest, JSONRPCResponse


class ProcessAttachmentsParams(BaseModel):
    """Parameters for processing attachments."""
    user_id: str
    project_id: str 
    conversation_id: str
    message_content: Union[str, List[Dict[str, Any]]]  # Original message content
    message_additional_kwargs: Dict[str, Any] = Field(default_factory=dict)  # Contains attachments
    message_id: Optional[str] = None
    space_id: Optional[str] = None  # Optional space ID for space-level search priority


class ProcessAttachmentsRequest(JSONRPCRequest):
    method: Literal["attachment/index"] = "attachment/index"
    params: ProcessAttachmentsParams


class ProcessAttachmentsResult(BaseModel):
    """Result of attachment processing."""
    processed_content: List[Dict[str, Any]]  # Processed message content with attachments
    processing_stats: Dict[str, Any] = Field(default_factory=dict)  # Processing statistics
    relevant_attachments_count: int = 0
    semantic_chunks_count: int = 0
    fallback_used: bool = False


class ProcessAttachmentsResponse(JSONRPCResponse):
    result: ProcessAttachmentsResult | None = None 