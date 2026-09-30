import uuid
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.config import settings

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageResponse,
    SourceReference
)

from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service


class RAGService:

    # ============================================================
    # MAIN CHAT FUNCTION
    # ============================================================

    def process_query(
        self,
        request: ChatRequest,
        db: Session
    ) -> ChatResponse:

        # --------------------------------------------------------
        # 1. VALIDATE USER
        # --------------------------------------------------------

        user = (
            db.query(User)
            .filter(
                User.user_id == request.user_id
            )
            .first()
        )

        if not user:

            raise ValueError(
                f"User with id "
                f"{request.user_id} not found."
            )

        # --------------------------------------------------------
        # 2. VALIDATE MESSAGE
        # --------------------------------------------------------

        user_question = (
            request.message or ""
        ).strip()

        if not user_question:

            raise ValueError(
                "Message cannot be empty."
            )

        # --------------------------------------------------------
        # 3. FIND OR CREATE CONVERSATION
        # --------------------------------------------------------

        conversation = None

        if request.conversation_id:

            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.conversation_id
                    == request.conversation_id,

                    Conversation.user_id
                    == user.user_id
                )
                .first()
            )

        if conversation is None:

            title = user_question

            if len(title) > 45:
                title = title[:42] + "..."

            conversation = Conversation(
                conversation_id=str(
                    uuid.uuid4()
                ),
                user_id=user.user_id,
                title=title
            )

            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # --------------------------------------------------------
        # 4. SAVE USER MESSAGE
        # --------------------------------------------------------

        user_message = Message(
            message_id=str(uuid.uuid4()),
            conversation_id=(
                conversation.conversation_id
            ),
            role="user",
            content=user_question
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        # --------------------------------------------------------
        # 5. CONVERSATION HISTORY
        # --------------------------------------------------------

        previous_messages = (
            db.query(Message)
            .filter(
                Message.conversation_id
                == conversation.conversation_id
            )
            .order_by(
                Message.created_at.asc()
            )
            .all()
        )

        history = []

        for message in previous_messages[:-1]:

            history.append(
                {
                    "role": message.role,
                    "content": message.content
                }
            )

        # Keep history reasonably small
        history = history[-6:]

        # --------------------------------------------------------
        # 6. RETRIEVE DOCUMENTS
        # --------------------------------------------------------

        retrieved_chunks: List[
            Dict[str, Any]
        ] = []

        source_refs: List[
            SourceReference
        ] = []

        try:

            if (
                embedding_service.is_ready()
                and vector_store.count() > 0
            ):

                query_embedding = (
                    embedding_service
                    .get_query_embedding(
                        user_question
                    )
                )

                retrieved_chunks = (
                    vector_store.similarity_search(
                        query_embedding=query_embedding,
                        top_k=settings.TOP_K_RESULTS,
                        query_text=user_question
                    )
                )

                # ------------------------------------------------
                # SOURCE REFERENCES
                # ------------------------------------------------

                for chunk in retrieved_chunks:

                    text = str(
                        chunk.get("text", "")
                    )

                    snippet = text[:350]

                    if len(text) > 350:
                        snippet += "..."

                    source_refs.append(
                        SourceReference(
                            document_filename=chunk.get(
                                "document_filename",
                                "Unknown Document"
                            ),

                            category=chunk.get(
                                "category",
                                "General"
                            ),

                            page_number=int(
                                chunk.get(
                                    "page_number",
                                    1
                                )
                            ),

                            chunk_index=int(
                                chunk.get(
                                    "chunk_index",
                                    0
                                )
                            ),

                            snippet=snippet,

                            score=chunk.get(
                                "similarity_score"
                            )
                        )
                    )

        except Exception as error:

            # Retrieval failure should not crash
            # the entire chat endpoint.

            print(
                f"RAG retrieval error: {error}"
            )

            retrieved_chunks = []
            source_refs = []

        # --------------------------------------------------------
        # 7. GENERATE ANSWER
        # --------------------------------------------------------

        if not embedding_service.is_ready():

            assistant_text = (
                "⚠️ **Knowledge Base Error**\n\n"
                "The local embedding model is not available. "
                "Please check the ChromaDB embedding dependencies."
            )

        elif vector_store.count() == 0:

            assistant_text = (
                "📚 **No Documents Ingested Yet**\n\n"
                "The knowledge base is currently empty.\n\n"
                "Please run the document ingestion process "
                "before asking questions."
            )

        elif not llm_service.is_ready():

            assistant_text = (
                "⚠️ **AI Answer Service Unavailable**\n\n"
                "The document database is working, but the "
                "Gemini language model is not configured.\n\n"
                "Please check your GEMINI_API_KEY in "
                "`backend/.env`."
            )

        else:

            try:

                assistant_text = (
                    llm_service.generate_answer(
                        query=user_question,
                        context_chunks=retrieved_chunks,
                        conversation_history=history
                    )
                )

            except Exception as error:

                print(
                    f"LLM generation error: {error}"
                )

                assistant_text = (
                    "⚠️ **Unable to generate an answer right now.**\n\n"
                    "The document retrieval system is working, "
                    "but the AI answer service returned an error.\n\n"
                    f"Error: {str(error)}"
                )

        # --------------------------------------------------------
        # 8. SAVE ASSISTANT MESSAGE
        # --------------------------------------------------------

        sources_payload = [
            ref.model_dump()
            for ref in source_refs
        ]

        assistant_message = Message(
            message_id=str(uuid.uuid4()),
            conversation_id=(
                conversation.conversation_id
            ),
            role="assistant",
            content=assistant_text
        )

        # Save sources only if the model supports it
        try:

            assistant_message.sources = (
                sources_payload
            )

        except Exception:

            pass

        db.add(assistant_message)

        # --------------------------------------------------------
        # 9. UPDATE CONVERSATION
        # --------------------------------------------------------

        conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(assistant_message)

        # --------------------------------------------------------
        # 10. RETURN RESPONSE
        # --------------------------------------------------------

        return ChatResponse(

            conversation_id=(
                conversation.conversation_id
            ),

            user_message=MessageResponse.model_validate(
                user_message
            ),

            assistant_message=MessageResponse(
                message_id=(
                    assistant_message.message_id
                ),

                conversation_id=(
                    assistant_message.conversation_id
                ),

                role=assistant_message.role,

                content=assistant_message.content,

                sources=sources_payload,

                created_at=(
                    assistant_message.created_at
                )
            ),

            sources=source_refs
        )


rag_service = RAGService()