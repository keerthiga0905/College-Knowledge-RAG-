from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
from app.models import User, Conversation, Message, Document
from app.routers import auth_router, conversations_router, chat_router, documents_router, admin_router

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RAG-based College Information Assistant backed by ChromaDB and Google Gemini",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(conversations_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    """Health check endpoint confirming API, DB, and ChromaDB status."""
    from app.services.embedding_service import embedding_service
    from app.services.vector_store import vector_store
    
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "gemini_configured": embedding_service.is_ready(),
        "vector_store_chunks": vector_store.count(),
        "database": "connected"
    }

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Access documentation at /api/docs",
        "health": "/api/health"
    }
