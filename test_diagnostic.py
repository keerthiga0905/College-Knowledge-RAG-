#!/usr/bin/env python
"""Diagnostic test script for College AI Knowledge Base system."""

import sys
from pathlib import Path

# Ensure backend is in path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service

print('=' * 60)
print('COLLEGE AI KNOWLEDGE BASE - DIAGNOSTIC TEST')
print('=' * 60)

print('\n=== A. CONFIGURATION CHECK ===')
print(f'Embedding Model Config: {settings.EMBEDDING_MODEL}')
print(f'LLM Model: {settings.LLM_MODEL}')
print(f'Gemini API Key Present: {bool(settings.GEMINI_API_KEY.strip())}')
print(f'Gemini Ready (Embedding): {embedding_service.is_gemini_ready()}')
print(f'LLM Ready: {llm_service.is_ready()}')
print(f'Embedding Provider: {embedding_service.get_embedding_provider_name()}')

print('\n=== B. EMBEDDING TEST ===')
try:
    test_text = "What is the syllabus for Artificial Intelligence?"
    embedding = embedding_service.get_embedding(test_text)
    print(f'Embedding generated successfully')
    print(f'Embedding dimension: {len(embedding)}')
    print(f'First 5 values: {embedding[:5]}')
    print(f'Data type: {type(embedding[0])}')
except Exception as e:
    print(f'ERROR: {e}')

print('\n=== C. VECTOR STORE STATUS ===')
try:
    count = vector_store.count()
    print(f'Total chunks in ChromaDB: {count}')
    stats = vector_store.get_stats()
    print(f'Total documents: {stats.get("total_documents", 0)}')
    print(f'Categories: {stats.get("categories", {})}')
    if stats.get("document_names"):
        print(f'Sample documents (first 5):')
        for doc in stats.get("document_names", [])[:5]:
            print(f'  - {doc}')
except Exception as e:
    print(f'ERROR: {e}')

print('\n=== D. SIMILARITY SEARCH TEST ===')
try:
    if vector_store.count() > 0:
        query_text = "What is the syllabus for Artificial Intelligence?"
        query_embedding = embedding_service.get_query_embedding(query_text)
        results = vector_store.similarity_search(query_embedding, top_k=5)
        print(f'Query: {query_text}')
        print(f'Results found: {len(results)}')
        for i, result in enumerate(results, 1):
            print(f'\n  Result #{i}:')
            print(f'    Document: {result.get("document_filename")}')
            print(f'    Category: {result.get("category")}')
            print(f'    Page: {result.get("page_number")}')
            print(f'    Similarity Score: {result.get("similarity_score")}')
            snippet = result.get("text", "")[:150]
            print(f'    Snippet: {snippet}...')
    else:
        print('No documents in vector store to search')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()

print('\n=== E. LLM TEST ===')
try:
    test_prompt = "Who is the president of the United States? (Answer from provided context or say not found)"
    response = llm_service.generate_answer(
        query=test_prompt,
        context_chunks=[]
    )
    print(f'Prompt: {test_prompt}')
    print(f'Response (first 200 chars): {response[:200]}...' if len(response) > 200 else f'Response: {response}')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '=' * 60)
print('DIAGNOSTIC TEST COMPLETE')
print('=' * 60)
