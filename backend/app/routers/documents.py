import os
import uuid
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings, ROOT_DIR
from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, IngestionStatusResponse
from app.services.document_processor import document_processor
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

router = APIRouter(prefix="/documents", tags=["Document Management & Ingestion"])

FOLDER_CATEGORIES = [
    "01_College_information",
    "02_Syllabus",
    "03_Academic_Calendar",
    "04_Lab_Manuals",
    "05_Fees_Placement_Funding"
]

def scan_and_ingest_knowledge_base(db: Session):
    """Scans the 5 core folders and ingests all PDFs/DOCXs."""
    root_path = Path(settings.DOCUMENTS_ROOT_DIR)
    
    for category in FOLDER_CATEGORIES:
        category_dir = root_path / category
        if not category_dir.exists() or not category_dir.is_dir():
            continue

        for file_path in category_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in [".pdf", ".docx", ".doc"]:
                filename = file_path.name
                # Check or create DB record
                doc_record = db.query(Document).filter(
                    Document.filename == filename,
                    Document.category == category
                ).first()

                if not doc_record:
                    doc_record = Document(
                        document_id=str(uuid.uuid4()),
                        filename=filename,
                        category=category,
                        filepath=str(file_path.resolve()),
                        file_size=file_path.stat().st_size,
                        status="pending"
                    )
                    db.add(doc_record)
                    db.commit()
                    db.refresh(doc_record)

                try:
                    # Process and chunk
                    chunks = document_processor.process_file(str(file_path), category)
                    if not chunks:
                        doc_record.status = "processed"
                        doc_record.chunk_count = 0
                        db.commit()
                        continue

                    # If embeddings are configured, embed and index
                    if embedding_service.is_ready():
                        texts = [c.text for c in chunks]
                        embeddings = embedding_service.get_embeddings_batch(texts)
                        vector_store.add_chunks(chunks, embeddings)

                    doc_record.chunk_count = len(chunks)
                    doc_record.status = "processed"
                    doc_record.error_message = None
                    db.commit()

                except Exception as e:
                    doc_record.status = "failed"
                    doc_record.error_message = str(e)
                    db.commit()

@router.get("", response_model=IngestionStatusResponse)
def get_documents_status(db: Session = Depends(get_db)):
    """Returns the list of indexed documents and status breakdown."""
    documents = db.query(Document).order_by(Document.category, Document.filename).all()
    
    total_docs = len(documents)
    processed_docs = sum(1 for d in documents if d.status == "processed")
    failed_docs = sum(1 for d in documents if d.status == "failed")
    total_chunks = sum(d.chunk_count for d in documents)

    categories = {}
    for d in documents:
        categories[d.category] = categories.get(d.category, 0) + 1

    return IngestionStatusResponse(
        total_documents=total_docs,
        processed_documents=processed_docs,
        failed_documents=failed_docs,
        total_chunks=total_chunks,
        categories=categories,
        documents=[DocumentResponse.model_validate(d) for d in documents]
    )

@router.post("/ingest")
def trigger_ingest(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Triggers batch ingestion across all 5 knowledge base folders."""
    background_tasks.add_task(scan_and_ingest_knowledge_base, db)
    return {"message": "Knowledge base ingestion started in the background."}

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("01_College_information"),
    db: Session = Depends(get_db)
):
    """Uploads a new document, saves it to the category folder, and indexes it into ChromaDB."""
    if not file.filename.lower().endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(status_code=400, detail="Only PDF and Word (.docx) documents are supported.")

    target_dir = Path(settings.DOCUMENTS_ROOT_DIR) / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file.filename

    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc_record = db.query(Document).filter(
        Document.filename == file.filename,
        Document.category == category
    ).first()

    if not doc_record:
        doc_record = Document(
            document_id=str(uuid.uuid4()),
            filename=file.filename,
            category=category,
            filepath=str(target_path.resolve()),
            file_size=target_path.stat().st_size,
            status="pending"
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

    try:
        chunks = document_processor.process_file(str(target_path), category)
        if chunks and embedding_service.is_ready():
            texts = [c.text for c in chunks]
            embeddings = embedding_service.get_embeddings_batch(texts)
            vector_store.add_chunks(chunks, embeddings)

        doc_record.chunk_count = len(chunks)
        doc_record.status = "processed"
        doc_record.error_message = None
        db.commit()
        db.refresh(doc_record)

    except Exception as e:
        doc_record.status = "failed"
        doc_record.error_message = str(e)
        db.commit()
        db.refresh(doc_record)

    return DocumentResponse.model_validate(doc_record)

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Removes a document record and deletes its indexed vectors from ChromaDB."""
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove from vector store
    try:
        vector_store.delete_by_filename(doc.filename)
    except Exception:
        pass

    db.delete(doc)
    db.commit()

    return {"message": f"Document {doc.filename} removed successfully."}
