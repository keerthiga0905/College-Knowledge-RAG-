"""
Admin-only routes for accessing system statistics, student information, and knowledge base management.
All endpoints in this router are protected by admin authorization checks.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.schemas.chat import ConversationResponse, MessageResponse, ConversationDetailResponse
from app.services.auth_utils import verify_admin

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class StatsResponse(BaseModel):
    """System-wide statistics for admin dashboard"""
    total_students: int
    total_conversations: int
    total_messages: int
    total_documents: int
    knowledge_base_chunks: int
    timestamp: datetime

class StudentListItem(BaseModel):
    """Brief student information for the student list"""
    user_id: str
    name: str
    email: str
    created_at: datetime
    conversation_count: int
    message_count: int

class StudentDetailResponse(BaseModel):
    """Detailed student information"""
    user_id: str
    name: str
    email: str
    created_at: datetime
    conversation_count: int
    message_count: int

class RecentActivityItem(BaseModel):
    """Recent activity entry"""
    user_id: str
    student_name: str
    student_email: str
    activity_type: str  # "message", "conversation"
    conversation_id: Optional[str] = None
    message_preview: Optional[str] = None
    timestamp: datetime

class DocumentListItem(BaseModel):
    """Document information"""
    document_id: str
    filename: str
    category: str
    status: str
    chunk_count: int
    file_size: int
    created_at: datetime
    updated_at: datetime

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.get("/stats", response_model=StatsResponse)
async def get_admin_stats(
    admin_id: str = Query(..., description="Admin user ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Get system-wide statistics.
    Requires admin authorization.
    """
    # Verify admin
    admin = await verify_admin(admin_id, db)
    
    # Count students (all users with role="student")
    total_students = db.query(func.count(User.user_id)).filter(
        User.role == "student"
    ).scalar() or 0
    
    # Count conversations
    total_conversations = db.query(func.count(Conversation.conversation_id)).scalar() or 0
    
    # Count messages
    total_messages = db.query(func.count(Message.message_id)).scalar() or 0
    
    # Count documents
    total_documents = db.query(func.count(Document.document_id)).scalar() or 0
    
    # Count knowledge base chunks (sum of chunk_count across all documents)
    knowledge_base_chunks = db.query(func.sum(Document.chunk_count)).scalar() or 0
    
    return StatsResponse(
        total_students=total_students,
        total_conversations=total_conversations,
        total_messages=total_messages,
        total_documents=total_documents,
        knowledge_base_chunks=int(knowledge_base_chunks),
        timestamp=datetime.utcnow()
    )

@router.get("/students", response_model=List[StudentListItem])
async def get_all_students(
    admin_id: str = Query(..., description="Admin user ID for authorization"),
    skip: int = Query(0, ge=0, description="Number of students to skip"),
    limit: int = Query(50, ge=1, le=200, description="Number of students to return"),
    db: Session = Depends(get_db)
):
    """
    Get list of all registered students with their statistics.
    Requires admin authorization.
    
    Returns paginated list of students.
    """
    # Verify admin
    admin = await verify_admin(admin_id, db)
    
    # Get students ordered by recent activity
    students = db.query(User).filter(
        User.role == "student"
    ).order_by(
        desc(User.created_at)
    ).offset(skip).limit(limit).all()
    
    results = []
    for student in students:
        conversation_count = db.query(func.count(Conversation.conversation_id)).filter(
            Conversation.user_id == student.user_id
        ).scalar() or 0
        
        message_count = db.query(func.count(Message.message_id)).join(
            Conversation, Message.conversation_id == Conversation.conversation_id
        ).filter(
            Conversation.user_id == student.user_id
        ).scalar() or 0
        
        results.append(StudentListItem(
            user_id=student.user_id,
            name=student.name,
            email=student.email,
            created_at=student.created_at,
            conversation_count=conversation_count,
            message_count=message_count
        ))
    
    return results

@router.get("/students/{user_id}", response_model=StudentDetailResponse)
async def get_student_detail(
    user_id: str,
    admin_id: str = Query(..., description="Admin user ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific student.
    Requires admin authorization.
    """
    # Verify admin
    admin = await verify_admin(admin_id, db)
    
    # Verify student exists
    student = db.query(User).filter(
        User.user_id == user_id,
        User.role == "student"
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Count conversations and messages
    conversation_count = db.query(func.count(Conversation.conversation_id)).filter(
        Conversation.user_id == user_id
    ).scalar() or 0
    
    message_count = db.query(func.count(Message.message_id)).join(
        Conversation, Message.conversation_id == Conversation.conversation_id
    ).filter(
        Conversation.user_id == user_id
    ).scalar() or 0
    
    return StudentDetailResponse(
        user_id=student.user_id,
        name=student.name,
        email=student.email,
        created_at=student.created_at,
        conversation_count=conversation_count,
        message_count=message_count
    )

@router.get("/students/{user_id}/conversations", response_model=List[ConversationResponse])
async def get_student_conversations(
    user_id: str,
    admin_id: str = Query(..., description="Admin user ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for a specific student.
    Requires admin authorization.
    """
    # Verify admin
    admin = await verify_admin(admin_id, db)
    
    # Verify student exists
    student = db.query(User).filter(
        User.user_id == user_id,
        User.role == "student"
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Get student's conversations
    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(
        desc(Conversation.updated_at)
    ).all()
    
    results = []
    for conv in conversations:
        message_count = db.query(func.count(Message.message_id)).filter(
            Message.conversation_id == conv.conversation_id
        ).scalar() or 0
        
        results.append(ConversationResponse(
            conversation_id=conv.conversation_id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=message_count
        ))
    
    return results

@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_details_admin(
    conversation_id: str,
    admin_id: str = Query(..., description="Admin user ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Get full conversation details including all messages.
    Requires admin authorization.
    
    This is the admin version that doesn't require user_id parameter.
    """
    # Verify admin
    admin = await verify_admin(admin_id, db)
    
    # Get conversation
    conv = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get all messages
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    
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

@router.get("/activity", response_model=List[RecentActivityItem])
async def get_recent_activity(
    admin_id: str = Query(..., description="Admin user ID for authorization"),
    limit: int = Query(20, ge=1, le=100, description="Number of activities to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent student activity across the system.
    Requires admin authorization.
    
    Shows recent messages and conversations created by students.
    """
    # Verify admin
    admin = await verify_admin(admin_id, db)
    
    # Get recent messages with student info
    recent_messages = db.query(
        User.user_id,
        User.name.label("student_name"),
        User.email.label("student_email"),
        Message.message_id,
        Message.conversation_id,
        Message.content,
        Message.created_at,
        Message.role
    ).join(
        Conversation, Message.conversation_id == Conversation.conversation_id
    ).join(
        User, Conversation.user_id == User.user_id
    ).filter(
        Message.role == "user",  # Only show user questions, not AI responses
        User.role == "student"
    ).order_by(
        desc(Message.created_at)
    ).limit(limit).all()
    
    results = []
    for item in recent_messages:
        # Get conversation title
        conv = db.query(Conversation).filter(
            Conversation.conversation_id == item.conversation_id
        ).first()
        
        results.append(RecentActivityItem(
            user_id=item.user_id,
            student_name=item.student_name,
            student_email=item.student_email,
            activity_type="message",
            conversation_id=item.conversation_id,
            message_preview=item.content[:100],  # First 100 chars
            timestamp=item.created_at
        ))
    
    return results

@router.get("/documents", response_model=List[DocumentListItem])
async def get_knowledge_base_documents(
    admin_id: str = Query(..., description="Admin user ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Get list of all indexed documents in the knowledge base.
    Requires admin authorization.
    
    Shows document status, chunk count, and file information.
    """
    # Verify admin
    admin = await verify_admin(admin_id, db)
    
    # Get all documents
    documents = db.query(Document).order_by(
        desc(Document.updated_at)
    ).all()
    
    results = []
    for doc in documents:
        results.append(DocumentListItem(
            document_id=doc.document_id,
            filename=doc.filename,
            category=doc.category,
            status=doc.status,
            chunk_count=doc.chunk_count,
            file_size=doc.file_size,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        ))
    
    return results

@router.post("/documents/re-index")
async def trigger_knowledge_base_reindex(
    admin_id: str = Query(..., description="Admin user ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Trigger re-indexing of the knowledge base.
    Requires admin authorization.
    
    This endpoint can be used to trigger the document ingestion process.
    The actual ingestion should be run via the existing ingest.py script or
    through the /api/documents/ingest endpoint.
    """
    # Verify admin
    admin = await verify_admin(admin_id, db)
    
    return {
        "status": "success",
        "message": "Re-indexing triggered. Use the documents/ingest endpoint or run 'python ingest.py' from the backend directory.",
        "admin_id": admin.user_id
    }
