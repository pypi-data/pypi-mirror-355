from typing import List, Optional, Union
from pydantic import BaseModel, Field
import uuid


class ConversationAttachment(BaseModel):
    """Model for a conversation attachment."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    project_id: str
    conversation_id: str
    s3_key: str
    file_name: str
    file_type: str
    file_size: int
    is_indexed: bool = False  # Tracks whether the attachment has been indexed
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateConversationAttachmentRequest(BaseModel):
    """Request model for creating a conversation attachment."""
    user_id: str
    project_id: str
    conversation_id: str
    s3_key: str
    file_name: str
    file_type: str
    file_size: int


class CreateConversationAttachmentResponse(BaseModel):
    """Response model for creating a conversation attachment."""
    result: ConversationAttachment


class ListConversationAttachmentRequest(BaseModel):
    """Request model for listing conversation attachments."""
    user_id: str
    project_id: str
    conversation_id: str


class ListConversationAttachmentResponse(BaseModel):
    """Response model for listing conversation attachments."""
    result: List[ConversationAttachment]


class DeleteConversationAttachmentRequest(BaseModel):
    """Request model for deleting a conversation attachment."""
    user_id: str
    project_id: str
    conversation_id: str
    attachment_id: str


class DeleteConversationAttachmentResponse(BaseModel):
    """Response model for deleting a conversation attachment."""
    success: bool


# JSON-RPC wrapper models
class ConversationAttachmentRPCRequest(BaseModel):
    """JSON-RPC request wrapper for conversation attachment operations."""
    jsonrpc: str = "2.0"
    method: str  # "create", "list", or "delete"
    params: Union[CreateConversationAttachmentRequest, ListConversationAttachmentRequest, DeleteConversationAttachmentRequest]
    id: Optional[Union[str, int]] = None


class ConversationAttachmentRPCResponse(BaseModel):
    """JSON-RPC response wrapper for conversation attachment operations."""
    jsonrpc: str = "2.0"
    result: Union[ConversationAttachment, List[ConversationAttachment], bool] = None
    error: Optional[dict] = None
    id: Optional[Union[str, int]] = None 