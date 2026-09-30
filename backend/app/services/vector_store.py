from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.services.document_processor import ProcessedChunk


class VectorStore:
    """
    ChromaDB vector store for the College AI RAG system.
    """

    def __init__(self):

        persist_dir = Path(
            settings.CHROMA_PERSIST_DIR
        )

        persist_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )

        self.collection = None

        self._ensure_collection()

    # ============================================================
    # COLLECTION
    # ============================================================

    def _ensure_collection(self):

        try:

            self.collection = (
                self.client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={
                        "hnsw:space": "cosine"
                    }
                )
            )

            self.collection.count()

            return self.collection

        except Exception as error:

            print(
                f"Chroma collection recovery: {error}"
            )

            self.collection = (
                self.client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={
                        "hnsw:space": "cosine"
                    }
                )
            )

            return self.collection

    def _get_collection(self):

        if self.collection is None:
            return self._ensure_collection()

        try:

            self.collection.count()

            return self.collection

        except Exception:

            return self._ensure_collection()

    # ============================================================
    # ADD / UPDATE CHUNKS
    # ============================================================

    def add_chunks(
        self,
        chunks: List[ProcessedChunk],
        embeddings: List[List[float]]
    ) -> int:

        if not chunks:
            return 0

        if not embeddings:
            return 0

        if len(chunks) != len(embeddings):

            raise ValueError(
                "Number of chunks and embeddings "
                "must be the same."
            )

        collection = self._get_collection()

        batch_size = 100

        total_added = 0

        for start in range(
            0,
            len(chunks),
            batch_size
        ):

            chunk_batch = chunks[
                start:start + batch_size
            ]

            embedding_batch = embeddings[
                start:start + batch_size
            ]

            ids = []

            documents = []

            metadatas = []

            clean_embeddings = []

            for chunk, embedding in zip(
                chunk_batch,
                embedding_batch
            ):

                ids.append(
                    str(chunk.chunk_id)
                )

                documents.append(
                    str(chunk.text)
                )

                metadatas.append(
                    chunk.to_metadata()
                )

                clean_embeddings.append(
                    [
                        float(value)
                        for value in embedding
                    ]
                )

            try:

                collection.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=clean_embeddings,
                    metadatas=metadatas
                )

            except Exception as error:

                error_text = str(
                    error
                ).lower()

                if (
                    "collection" in error_text
                    or "not found" in error_text
                    or "does not exist" in error_text
                ):

                    collection = (
                        self._ensure_collection()
                    )

                    collection.upsert(
                        ids=ids,
                        documents=documents,
                        embeddings=clean_embeddings,
                        metadatas=metadatas
                    )

                else:

                    raise

            total_added += len(chunk_batch)

        return total_added

    # ============================================================
    # SIMILARITY SEARCH
    # ============================================================

    def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = None,
        category: Optional[str] = None,
        query_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:

        collection = self._get_collection()

        count = collection.count()

        if count == 0:
            return []

        k = (
            top_k
            if top_k is not None
            else settings.TOP_K_RESULTS
        )

        k = max(1, int(k))

        fetch_k = min(
            count,
            max(k * 3, 15)
        )

        where_clause = None

        if category:

            where_clause = {
                "category": category
            }

        try:

            if where_clause:

                results = collection.query(
                    query_embeddings=[
                        query_embedding
                    ],
                    n_results=fetch_k,
                    where=where_clause,
                    include=[
                        "documents",
                        "metadatas",
                        "distances"
                    ]
                )

            else:

                results = collection.query(
                    query_embeddings=[
                        query_embedding
                    ],
                    n_results=fetch_k,
                    include=[
                        "documents",
                        "metadatas",
                        "distances"
                    ]
                )

        except Exception as error:

            error_text = str(
                error
            ).lower()

            if (
                "collection" in error_text
                or "not found" in error_text
                or "does not exist" in error_text
            ):

                collection = (
                    self._ensure_collection()
                )

                results = collection.query(
                    query_embeddings=[
                        query_embedding
                    ],
                    n_results=fetch_k,
                    include=[
                        "documents",
                        "metadatas",
                        "distances"
                    ]
                )

            else:

                raise

        if not results:
            return []

        documents = (
            results.get("documents")
            or [[]]
        )

        metadatas = (
            results.get("metadatas")
            or [[]]
        )

        distances = (
            results.get("distances")
            or [[]]
        )

        ids = (
            results.get("ids")
            or [[]]
        )

        if not documents or not documents[0]:
            return []

        docs = documents[0]

        metas = (
            metadatas[0]
            if metadatas
            and metadatas[0]
            else [{} for _ in docs]
        )

        dists = (
            distances[0]
            if distances
            and distances[0]
            else [0.0 for _ in docs]
        )

        chunk_ids = (
            ids[0]
            if ids
            and ids[0]
            else ["" for _ in docs]
        )

        query = (
            query_text.lower().strip()
            if query_text
            else ""
        )

        # ========================================================
        # QUERY DETECTION
        # ========================================================

        is_aiml = any(
            term in query
            for term in [
                "aiml",
                "a i m l",
                "artificial intelligence",
                "machine learning"
            ]
        )

        is_third_year = any(
            term in query
            for term in [
                "ty",
                "third year",
                "3rd year",
                "third-year",
                "semester v",
                "semester vi",
                "sem v",
                "sem vi"
            ]
        )

        is_syllabus = any(
            term in query
            for term in [
                "syllabus",
                "curriculum",
                "subjects",
                "subject",
                "course",
                "courses"
            ]
        )

        formatted_results = []

        # ========================================================
        # RERANK
        # ========================================================

        for (
            doc_text,
            metadata,
            distance,
            chunk_id
        ) in zip(
            docs,
            metas,
            dists,
            chunk_ids
        ):

            metadata = metadata or {}

            document_name = str(
                metadata.get(
                    "document_filename",
                    ""
                )
            )

            document_lower = (
                document_name.lower()
            )

            text = str(
                doc_text or ""
            )

            text_lower = text.lower()

            # Chroma cosine distance
            # 0 = most similar
            # 2 = least similar

            distance_value = float(
                distance
            )

            similarity = max(
                0.0,
                1.0 - (
                    distance_value / 2.0
                )
            )

            adjusted_score = similarity

            # ====================================================
            # AIML BOOST
            # ====================================================

            if is_aiml:

                if any(
                    term in document_lower
                    for term in [
                        "aiml",
                        "artificial",
                        "machine"
                    ]
                ):

                    adjusted_score += 0.20

                if any(
                    term in text_lower
                    for term in [
                        "aiml",
                        "artificial intelligence",
                        "machine learning"
                    ]
                ):

                    adjusted_score += 0.15

                if any(
                    term in document_lower
                    for term in [
                        "mechanical",
                        "civil",
                        "chemical"
                    ]
                ):

                    adjusted_score -= 0.20

            # ====================================================
            # THIRD YEAR BOOST
            # ====================================================

            if is_third_year:

                if any(
                    term in document_lower
                    for term in [
                        "ty",
                        "third",
                        "third_year",
                        "third-year"
                    ]
                ):

                    adjusted_score += 0.20

                if any(
                    term in text_lower
                    for term in [
                        "third year",
                        "third-year",
                        "semester v",
                        "semester vi",
                        "semester-v",
                        "semester-vi"
                    ]
                ):

                    adjusted_score += 0.15

            # ====================================================
            # SYLLABUS BOOST
            # ====================================================

            if is_syllabus:

                if any(
                    term in document_lower
                    for term in [
                        "syllabus",
                        "structure",
                        "curriculum"
                    ]
                ):

                    adjusted_score += 0.10

                if any(
                    term in text_lower
                    for term in [
                        "course code",
                        "course title",
                        "course type",
                        "semester",
                        "subject"
                    ]
                ):

                    adjusted_score += 0.10

            formatted_results.append(
                {
                    "chunk_id": chunk_id,

                    "text": text,

                    "document_filename": metadata.get(
                        "document_filename",
                        "Unknown Document"
                    ),

                    "category": metadata.get(
                        "category",
                        "General"
                    ),

                    "filepath": metadata.get(
                        "filepath",
                        ""
                    ),

                    "page_number": int(
                        metadata.get(
                            "page_number",
                            1
                        )
                    ),

                    "chunk_index": int(
                        metadata.get(
                            "chunk_index",
                            0
                        )
                    ),

                    "distance": distance_value,

                    "similarity_score": round(
                        similarity,
                        4
                    ),

                    "adjusted_score": round(
                        adjusted_score,
                        4
                    )
                }
            )

        # Highest adjusted score first
        formatted_results.sort(
            key=lambda item: item[
                "adjusted_score"
            ],
            reverse=True
        )

        return formatted_results[:k]

    # ============================================================
    # DELETE DOCUMENT
    # ============================================================

    def delete_by_filename(
        self,
        filename: str
    ):

        collection = self._get_collection()

        try:

            collection.delete(
                where={
                    "document_filename": filename
                }
            )

        except Exception as error:

            error_text = str(
                error
            ).lower()

            if (
                "collection" in error_text
                or "not found" in error_text
                or "does not exist" in error_text
            ):

                collection = (
                    self._ensure_collection()
                )

                collection.delete(
                    where={
                        "document_filename": filename
                    }
                )

            else:

                raise

    # ============================================================
    # COUNT
    # ============================================================

    def count(self) -> int:

        collection = self._get_collection()

        return int(
            collection.count()
        )

    # ============================================================
    # STATISTICS
    # ============================================================

    def get_stats(
        self
    ) -> Dict[str, Any]:

        collection = self._get_collection()

        total_chunks = collection.count()

        if total_chunks == 0:

            return {
                "total_chunks": 0,
                "total_documents": 0,
                "categories": {},
                "document_names": []
            }

        sample = collection.get(
            limit=min(
                total_chunks,
                5000
            ),
            include=[
                "metadatas"
            ]
        )

        categories = {}
        documents = set()

        metadatas = (
            sample.get("metadatas")
            or []
        )

        for metadata in metadatas:

            metadata = metadata or {}

            category = metadata.get(
                "category",
                "Other"
            )

            document = metadata.get(
                "document_filename",
                "Unknown"
            )

            categories[category] = (
                categories.get(
                    category,
                    0
                ) + 1
            )

            documents.add(
                document
            )

        return {
            "total_chunks": total_chunks,
            "total_documents": len(
                documents
            ),
            "categories": categories,
            "document_names": sorted(
                documents
            )
        }

    # ============================================================
    # CLEAR COLLECTION
    # ============================================================

    def clear(self):

        try:

            self.client.delete_collection(
                name=settings.CHROMA_COLLECTION_NAME
            )

        except Exception as error:

            error_text = str(
                error
            ).lower()

            if (
                "not found" not in error_text
                and "does not exist" not in error_text
            ):

                raise

        self.collection = None

        self._ensure_collection()


vector_store = VectorStore()