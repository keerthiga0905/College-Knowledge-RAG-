import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    filename = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # e.g., "01_College_information", "02_Syllabus"
    filepath = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # "pending", "processed", "failed"
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Document {self.filename} ({self.category}) - {self.status}>"
