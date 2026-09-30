"""
Authorization and dependency injection utilities.
Used to protect endpoints and enforce role-based access control.
"""

from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

async def verify_user_exists(user_id: str, db: Session = Depends(get_db)) -> User:
    """
    Dependency: Verify that a user exists.
    
    Returns:
        User: The user object if found
        
    Raises:
        HTTPException 401: If user not found
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not authenticated"
        )
    return user

async def verify_admin(user_id: str, db: Session = Depends(get_db)) -> User:
    """
    Dependency: Verify that user is authenticated AND has admin role.
    
    Returns:
        User: The admin user object if authorized
        
    Raises:
        HTTPException 401: If user not found
        HTTPException 403: If user is not admin
    """
    user = await verify_user_exists(user_id, db)
    
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource. Admin access required."
        )
    
    return user

async def get_current_user_with_permission(
    user_id: str = Query(..., description="Current user ID"),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency: Get current user from query parameter.
    Used for endpoints that need to verify the user making the request.
    """
    return await verify_user_exists(user_id, db)

def verify_conversation_ownership(conversation, requesting_user: User):
    """
    Helper: Verify that a user owns a conversation.
    
    Args:
        conversation: The Conversation object
        requesting_user: The User object making the request
        
    Raises:
        HTTPException 403: If user doesn't own the conversation
    """
    if conversation.user_id != requesting_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this conversation"
        )

def verify_message_access(message, requesting_user: User, db: Session):
    """
    Helper: Verify that a user can access a message (via conversation ownership).
    
    Args:
        message: The Message object
        requesting_user: The User object making the request
        db: Database session
        
    Raises:
        HTTPException 403: If user doesn't own the message's conversation
    """
    from app.models.conversation import Conversation
    
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == message.conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    verify_conversation_ownership(conversation, requesting_user)
