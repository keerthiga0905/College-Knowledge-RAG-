from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["RAG Chat"])

@router.post("", response_model=ChatResponse)
def send_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Submits a student question to the RAG pipeline.
    Performs query embedding, similarity search in ChromaDB, context assembly,
    Gemini response generation with source citations, and saves history in the database.
    """
    try:
        response = rag_service.process_query(request=payload, db=db)
        return response
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG processing failed: {str(e)}")
