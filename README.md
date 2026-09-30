# College AI Knowledge Base — RAG-Based College Information Assistant

A genuine **Retrieval-Augmented Generation (RAG)** college information assistant that allows students and faculty to enter their Name and Email, ask verified questions about college documents, and receive grounded answers backed by **ChromaDB** vector similarity search and **Google Gemini AI**.

---

## 🌟 Key Features

1. **Genuine RAG Pipeline**:
   - **Document Processing**: Automatic text extraction and chunking of PDFs and Word documents across 5 core categories with page number tracking.
   - **Dense Embeddings**: Generates embeddings via Google Gemini (`models/text-embedding-004`).
   - **Vector Search**: Persistent ChromaDB vector store with cosine similarity ranking.
   - **Strict Grounding & Hallucination Prevention**: Explicit system constraints instruct the model never to fabricate college fees, dates, rules, syllabus, or faculty details when not in the official context.
   - **Interactive Citations**: Every answer highlights the exact source document, category, and page number with clickable citation snippets.

2. **User System (Zero Friction)**:
   - Students enter **Name** and **Email** (no passwords or college IDs to remember).
   - Backend automatically creates or retrieves an internal `user_id`.
   - Complete multi-user conversation history saved persistently in the database.

3. **Modern Student-Friendly UI**:
   - Built with **React** + **Vite** with modern dark glassmorphism theme, glowing indicators, responsive drawer sidebar, markdown formatting with tables and code blocks, and categorized suggested prompt cards.
   - **Document Knowledge Base Library Inspector**: View indexing status and chunk breakdowns across all 63 college documents.

---

## 📂 Project Architecture

```
College_AI_Knowledge_Base/
├── 01_College_information/       # Real college mandatory disclosures & OBE manuals
├── 02_Syllabus/                  # Department syllabi (AIML, CSE, DS, Civil, Mech, etc.)
├── 03_Academic_Calendar/         # Academic calendars & schedules
├── 04_Lab_Manuals/               # Lab manuals (CC, DBE, DevOps, Java, AI-ML)
├── 05_Fees_Placement_Funding/    # Fee structures (FRA) & placement brochures
├── backend/
│   ├── app/
│   │   ├── models/               # SQLAlchemy models (User, Conversation, Message, Document)
│   │   ├── routers/              # FastAPI routers (auth, conversations, chat, documents)
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── services/             # Document processor, Vector store, Embeddings, LLM, RAG
│   │   ├── config.py             # Settings & Environment variables
│   │   ├── database.py           # DB session & connection management
│   │   └── main.py               # FastAPI entry point
│   ├── data/                     # Persistent ChromaDB vector database directory
│   ├── venv/                     # Python virtual environment
│   ├── ingest.py                 # CLI batch document ingestion script
│   ├── test_api.py               # Automated test suite
│   ├── requirements.txt          # Python dependencies
│   ├── .env.example              # Environment variables template
│   └── .env                      # Local configuration file
├── frontend/
│   ├── src/
│   │   ├── components/           # UI components (ChatArea, Sidebar, Header, Modals, etc.)
│   │   ├── context/              # AuthContext for multi-user session state
│   │   ├── services/             # API client connecting to FastAPI backend
│   │   ├── App.jsx               # Main React application
│   │   └── index.css             # Modern design tokens, glassmorphism & responsive CSS
│   ├── package.json              # Frontend dependencies
│   └── vite.config.js            # Vite configuration
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Configure Backend Environment

Open `backend/.env` (or copy `backend/.env.example` to `backend/.env`) and add your Google Gemini API key:

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
DATABASE_URL=sqlite:///./college_ai.db
CHROMA_PERSIST_DIR=./data/chroma_db
LLM_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=models/text-embedding-004
```

> 🔑 Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).

---

### 2. Ingest the College Documents

Run the ingestion script to process the documents from the 5 folders into ChromaDB:

```powershell
# From the workspace root:
backend\venv\Scripts\python backend/ingest.py
```

Options:
- `--dry-run`: Test document extraction and chunking without calling the embedding API.
- `--reset`: Clear existing vector records and re-index from scratch.

---

### 3. Start the Backend Server

```powershell
# From workspace root:
backend\venv\Scripts\uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Backend API will run at:
- **API Docs (Swagger)**: http://localhost:8000/api/docs
- **Health Endpoint**: http://localhost:8000/api/health

---

### 4. Start the Frontend Application

In a separate terminal:

```powershell
cd frontend
npm run dev
```

Frontend application will run at:
- **Web App**: http://localhost:5173

---

## 🧪 Automated Testing

Run the automated backend test suite:

```powershell
backend\venv\Scripts\python backend/test_api.py
```

This verifies:
- API health check
- Name + Email user registration and duplicate lookup
- Conversation creation & history retrieval
- RAG pipeline invocation
- Database persistence

---

## 🔒 Security & Data Integrity

- API keys and secrets are loaded exclusively via environment variables and never exposed to the frontend or saved in git.
- The 5 original document folders remain untouched and read-only.
- Strict LLM prompt grounding ensures facts are derived solely from official college documents.
