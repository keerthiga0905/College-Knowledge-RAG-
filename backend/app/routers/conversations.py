import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ConversationResponse,
    ConversationDetailResponse,
    MessageResponse
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])

class CreateConversationRequest(BaseModel):
    user_id: str
    title: Optional[str] = "New Conversation"

class UpdateConversationRequest(BaseModel):
    title: str

@router.get("", response_model=List[ConversationResponse])
def get_user_conversations(
    user_id: str = Query(..., description="Internal user ID"),
    db: Session = Depends(get_db)
):
    """Lists all conversations for a specific user, sorted by recent activity."""
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Query conversations with message counts
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )

    results = []
    for conv in conversations:
        count = db.query(func.count(Message.message_id)).filter(Message.conversation_id == conv.conversation_id).scalar() or 0
        results.append(
            ConversationResponse(
                conversation_id=conv.conversation_id,
                user_id=conv.user_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=count
            )
        )

    return results

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation_details(
    conversation_id: str,
    user_id: str = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Retrieves full conversation details including messages and citations.
    
    SECURITY: User must provide their user_id and can only access their own conversations.
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not authenticated"
        )
    
    # Get conversation
    conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    # SECURITY: Verify user owns this conversation
    if conv.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this conversation"
        )

    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

    formatted_messages = []
    for m in messages:
        formatted_messages.append(
            MessageResponse(
                message_id=m.message_id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                created_at=m.created_at
            )
        )

    return ConversationDetailResponse(
        conversation_id=conv.conversation_id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(formatted_messages),
        messages=formatted_messages
    )

@router.post("", response_model=ConversationResponse)
def create_new_conversation(
    payload: CreateConversationRequest,
    db: Session = Depends(get_db)
):
    """Creates a new conversation session for a user."""
    user = db.query(User).filter(User.user_id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_conv = Conversation(
        conversation_id=str(uuid.uuid4()),
        user_id=user.user_id,
        title=payload.title or "New Conversation"
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)

    return ConversationResponse(
        conversation_id=new_conv.conversation_id,
        user_id=new_conv.user_id,
        title=new_conv.title,
        created_at=new_conv.created_at,
        updated_at=new_conv.updated_at,
        message_count=0
    )

@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation_title(
    conversation_id: str,
    payload: UpdateConversationRequest,
    user_id: str = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Updates the title of a conversation.
    
    SECURITY: User must own the conversation to update it.
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not authenticated"
        )
    
    # Get conversation
    conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    # SECURITY: Verify user owns this conversation
    if conv.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this conversation"
        )

    conv.title = payload.title.strip()
    db.commit()
    db.refresh(conv)

    count = db.query(func.count(Message.message_id)).filter(Message.conversation_id == conv.conversation_id).scalar() or 0

    return ConversationResponse(
        conversation_id=conv.conversation_id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=count
    )

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    user_id: str = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Deletes a conversation and its messages.
    
    SECURITY: User must own the conversation to delete it.
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not authenticated"
        )
    
    # Get conversation
    conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    # SECURITY: Verify user owns this conversation
    if conv.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this conversation"
        )

    db.delete(conv)
    db.commit()

    return {"message": "Conversation deleted successfully.", "conversation_id": conversation_id}
