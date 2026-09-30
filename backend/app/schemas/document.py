from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    category: str
    filepath: str
    file_size: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IngestionStatusResponse(BaseModel):
    total_documents: int
    processed_documents: int
    failed_documents: int
    total_chunks: int
    categories: Dict[str, int]
    documents: List[DocumentResponse]
