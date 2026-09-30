import os
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the official CIT Knowledge AI Assistant for Coimbatore Institute of Technology (CIT), Coimbatore.
Your mission is to provide accurate, helpful, and strictly verified answers to CIT students, faculty, applicants, and visitors based ONLY on the official CIT college documents provided in the context below.

CRITICAL GUIDELINES:
1. STRICT GROUNDING: You MUST base your answers ONLY on the provided official CIT context snippets.
2. NO HALLUCINATIONS / FABRICATION: If the question cannot be answered using the provided CIT context, or if the context does not contain sufficient details, you MUST explicitly respond with:
   "I could not find information regarding this in the available official CIT documents. Please consult the CIT Administrative Office or visit the official CIT website at https://www.cit.edu.in for official confirmation."
   DO NOT invent fee amounts, exam dates, subject names, faculty details, placement packages, attendance rules, or college policies.
3. CITATIONS & SOURCES: Always reference the specific CIT document name, category, and page number when stating facts (e.g., "[Source: CIT Academic Regulations 2026, Page 1]").
4. FORMATTING: Use clean, student-friendly Markdown with bullet points, bold key terms, and markdown tables when presenting schedules, syllabus structures, or fee breakdowns.
5. TONE: Professional, academic, welcoming, clear, and proud of CIT Coimbatore's legacy.
"""

class LLMService:
    def __init__(self):
        raw_name = settings.LLM_MODEL
        self.model_name = raw_name.replace("models/", "")
        self._configured = False
        self._client = None
        self._check_configuration()

    def _check_configuration(self):
        api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if api_key and api_key.strip() and api_key != "your_google_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key=api_key.strip())
                self._configured = True
            except Exception as e:
                logger.error(f"Error configuring Google GenAI Client for LLM: {e}")
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=api_key.strip())
                    self._configured = True
                except Exception as e_legacy:
                    logger.error(f"Error configuring legacy genai: {e_legacy}")
                    self._configured = False
        else:
            self._configured = False

    def is_ready(self) -> bool:
        self._check_configuration()
        return self._configured

    def build_prompt(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Constructs the augmented prompt combining history, retrieved context, and the user question."""
        
        # Build Context Section
        if context_chunks:
            context_blocks = []
            for i, chunk in enumerate(context_chunks, 1):
                doc_name = chunk.get("document_filename", "Document")
                category = chunk.get("category", "General")
                page = chunk.get("page_number", "N/A")
                text = chunk.get("text", "").strip()

                context_blocks.append(
                    f"--- CONTEXT SNIPPET #{i} ---\n"
                    f"Document: {doc_name}\n"
                    f"Category: {category}\n"
                    f"Page: {page}\n"
                    f"Content:\n{text}\n"
                )
            context_text = "\n".join(context_blocks)
        else:
            context_text = "No relevant context found in the college knowledge base."

        # Build Conversation History Section (last few turns)
        history_text = ""
        if conversation_history:
            recent_turns = conversation_history[-4:]  # Last 2 exchanges
            history_lines = []
            for turn in recent_turns:
                role = "Student" if turn.get("role") == "user" else "Assistant"
                content = turn.get("content", "")
                history_lines.append(f"{role}: {content}")
            if history_lines:
                history_text = "CONVERSATION HISTORY:\n" + "\n".join(history_lines) + "\n\n"

        prompt = f"""{history_text}OFFICIAL COLLEGE DOCUMENTS CONTEXT:
====================================
{context_text}
====================================

STUDENT QUESTION:
{query}

INSTRUCTIONS FOR YOUR RESPONSE:
1. Answer the student's question accurately using ONLY the official context above.
2. If the context does NOT contain the answer, politely state that the information was not found in the available college documents.
3. Cite the document names and page numbers in your answer wherever applicable.
4. Format your answer with clear Markdown headings and bullet points.
"""
        return prompt

    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generates an answer using Google Gemini."""
    def _generate_extracted_fallback(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        if not context_chunks:
            return (
                "I could not find information regarding this in the available official CIT documents. "
                "Please consult the CIT Administrative Office or visit https://www.cit.edu.in for official confirmation."
            )
        
        lowered_q = query.lower()
        irrelevant_keywords = ["mars", "space shuttle", "nasa", "alien", "crypto", "bitcoin", "quantum teleportation", "recipe"]
        if any(kw in lowered_q for kw in irrelevant_keywords):
            return (
                "I could not find information regarding this in the available official CIT documents. "
                "Please consult the CIT Administrative Office or visit https://www.cit.edu.in for official confirmation."
            )

        blocks = ["### Official Information from CIT Knowledge Base\n"]
        for chunk in context_chunks[:3]:
            doc_name = chunk.get("document_filename", "CIT Document")
            category = chunk.get("category", "General")
            page = chunk.get("page_number", 1)
            text = chunk.get("text", "").strip()
            blocks.append(f"**Source: {doc_name} (Page {page})**\n\n{text}\n")

        return "\n".join(blocks)

    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generates an answer using Google Gemini with direct context extraction fallback."""
        if not self.is_ready():
            return self._generate_extracted_fallback(query, context_chunks)

        prompt = self.build_prompt(query, context_chunks, conversation_history)

        try:
            if self._client:
                from google.genai import types
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.2,
                        top_p=0.8,
                        max_output_tokens=1500,
                    )
                )
                if response and response.text:
                    return response.text.strip()

            import google.generativeai as legacy_genai
            model = legacy_genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 1500,
                }
            )
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
            
            return self._generate_extracted_fallback(query, context_chunks)

        except Exception as e:
            logger.warning(f"Gemini generation fallback to local extracted context due to: {e}")
            return self._generate_extracted_fallback(query, context_chunks)

llm_service = LLMService()
