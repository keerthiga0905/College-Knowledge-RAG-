# CIT College Knowledge AI — Coimbatore Institute of Technology (CIT)

A complete end-to-end Machine Learning / NLP Retrieval-Augmented Generation (RAG) System built for **Coimbatore Institute of Technology (CIT), Coimbatore**.

This system ingests official CIT college documents (academic regulations, syllabi, department details, admission criteria, fee structures, placement statistics, library & hostel facilities, student guidelines, and campus events), indexes them into a high-performance vector database, and provides accurate, strictly-grounded answers with source citations via a modern React AI Chat interface.

---

## 🏗️ End-to-End System Architecture

```text
                 CIT OFFICIAL SOURCES & DOCUMENTS
                         (PDF, TXT, DOCX, Web HTML)
                                     │
                                     ▼
                      DATA COLLECTION & INGESTION
                                     │
                                     ▼
                         DATA CLEANING & PARSING
                         (PyMuPDF, python-docx, OCR)
                                     │
                                     ▼
                            DOCUMENT CHUNKING
                    (Configurable Chunk Size & Overlap)
                                     │
                                     ▼
                             EMBEDDING MODEL
                      (Local ONNX / all-MiniLM-L6-v2)
                                     │
                                     ▼
                           CHROMADB VECTOR STORE
                    (HNSW Index, Cosine Similarity)
                                     │
                                     │
User Question ───────────────────────┤
      │                              │
      ▼                              ▼
Query Embedding              Similarity Search
      │                              │
      └──────────────┬───────────────┘
                     ▼
            RELEVANT CIT CHUNKS
                     │
                     ▼
            CONTEXT CONSTRUCTION
                     │
                     ▼
           LLM GENERATION (GEMINI)
                     │
                     ▼
             ANSWER + CITATIONS
                     │
                     ▼
               CIT CHAT UI
```

---

## 🌟 Key Machine Learning & RAG Features

1. **Strictly Grounded RAG Pipeline**:
   Answers are generated exclusively from official CIT context. If an answer is not present in the ingested knowledge base (e.g. out-of-scope questions), the system explicitly states that the information was not found instead of hallucinating.

2. **Official Source Citation**:
   Every response contains verifiable citations detailing document title, page number, category, and reference link to official CIT sources.

3. **Multi-Format Ingestion Pipeline**:
   Supports PDF text extraction (PyMuPDF & PyPDF), DOCX parsing, TXT, Markdown, HTML, and image PDF fallback.

4. **Dense Vector Embeddings & Similarity Search**:
   Uses ChromaDB persistent vector database with 384-dimensional ONNX embeddings (`all-MiniLM-L6-v2`), performing cosine similarity search with domain-specific keyword reranking.

5. **Dataset Management & Ingestion Manager**:
   Admin interface allowing administrators to upload new PDFs/TXT documents, scrape web pages, re-index knowledge base embeddings, and inspect vector store status in real-time.

---

## 📁 Repository & Data Directory Structure

```text
College-AI-Knowledge-Base-Chatbot/
│
├── 01_College_information/        # CIT Overview, Governance, Departments & Facilities
├── 02_Syllabus/                   # CIT Academic Regulations 2026, Syllabus & Curriculum
├── 03_Academic_Calendar/          # CIT Academic Schedules, Exam Dates & Events
├── 04_Lab_Manuals/                # CIT Laboratory Infrastructure & Safety Rules
├── 05_Fees_Placement_Funding/     # CIT Fee Structure, Scholarships & Placement Stats
│
├── data/
│   ├── raw/                       # Unprocessed CIT documents & raw web pages
│   ├── cleaned/                   # Preprocessed and normalized text documents
│   ├── processed/                 # Extracted text chunks with metadata
│   └── metadata/                  # JSON metadata index of all CIT knowledge files
│
├── backend/
│   ├── app/
│   │   ├── config.py              # Application settings & RAG hyperparameters
│   │   ├── database.py            # SQLite / PostgreSQL database connection
│   │   ├── main.py                # FastAPI entrypoint & health checks
│   │   ├── models/                # User, Conversation, Message & Document ORM models
│   │   ├── routers/               # Auth, Chat, Conversations, Documents & Admin APIs
│   │   └── services/
│   │       ├── document_processor.py # Multi-format text extraction & chunking
│   │       ├── embedding_service.py  # Local ONNX embedding generator
│   │       ├── vector_store.py       # ChromaDB vector store search & reranking
│   │       ├── llm_service.py        # Gemini LLM answer generation & fallback
│   │       └── rag_service.py        # Core RAG orchestration pipeline
│   ├── data/chroma_db/            # Persistent ChromaDB vector database index
│   ├── college_ai.db              # SQLite relational database
│   ├── ingest.py                  # Document ingestion script
│   ├── requirements.txt           # Backend Python dependencies
│   └── test_rag.py                # RAG pipeline test suite
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # CIT Knowledge AI Chat UI & Dataset Manager Modal
│   │   ├── App.css                # Premium CIT Dark Mode CSS Design System
│   │   └── main.jsx               # React entrypoint
│   └── package.json               # Frontend dependencies (React, Vite, Tailwind-free)
│
├── scripts/
│   └── generate_cit_pdfs.py       # Utility to generate formatted CIT PDF documents
│
├── .env.example                   # Environment configuration template
├── README.md                      # Project documentation
└── test_diagnostic.py             # System diagnostic script
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `backend/.env` to configure your settings:
```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=local
CHROMA_PERSIST_DIR=./data/chroma_db
CHROMA_COLLECTION_NAME=cit_knowledge_base
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=6
```

### 3. Ingest CIT Knowledge Base

Run the ingestion script to parse all CIT documents and index vector embeddings into ChromaDB:

```bash
python backend/ingest.py --reset
```

### 4. Run Backend Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### 5. Frontend Setup & Launch

```bash
cd frontend

# Install packages
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Verification & Testing

Run the automated test suite to verify end-to-end RAG retrieval, vector search, and API endpoints:

```bash
# Run system diagnostic
python test_diagnostic.py

# Run end-to-end RAG test suite
python backend/test_rag.py

# Run API endpoint integration test
python backend/test_api.py
```

---

## 🏫 Official CIT Coimbatore Knowledge Coverage

The CIT knowledge base contains verified data across:
- **Autonomous Governance**: Established 1956 by VRET, Autonomous status since 1987, NAAC 'A' grade.
- **Academic Regulations 2026**: Minimum 75% attendance mandatory, condonation 65-74%, CBCS grading (O, A+, A, B+, B, C, RA).
- **Engineering Syllabi**: CSE, AIML, ECE, EEE, Mechanical, Civil, Chemical, AI & Data Science curriculum.
- **Placements**: 90%+ placement rate, Highest package 52 LPA, Average 7.5-9.5 LPA, Top recruiters (Amazon, Microsoft, Bosch, Texas Instruments, Qualcomm, TCS).
- **Scholarships & Fees**: Govt First Generation Graduate scholarship, BC/MBC/SC/ST post-matric schemes, fee structures for aided and self-supporting streams.
- **Campus Facilities**: Central Library, High Performance Computing (HPC) GPU labs, Men's & Women's Hostels, Rotaract Club, YUGAM Cultural Fest.
