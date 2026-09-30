from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any, Dict

class SourceReference(BaseModel):
    document_filename: str
    category: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None
    snippet: str
    score: Optional[float] = None

class ChatRequest(BaseModel):
    user_id: str = Field(..., description="ID of the user making the query")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID, or None for new")
    message: str = Field(..., min_length=1, description="Question asked by the user")

class MessageResponse(BaseModel):
    message_id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    conversation_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True

class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []

class ChatResponse(BaseModel):
    conversation_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    sources: List[SourceReference] = []
