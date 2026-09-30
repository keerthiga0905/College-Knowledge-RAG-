from typing import List
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Local embedding service.

    Uses Chroma's DefaultEmbeddingFunction,
    which provides local ONNX embeddings.

    This avoids Gemini embedding quota problems.
    """

    def __init__(self):

        self._local_embedder = None

        self._load_local_embedder()

    # ============================================================
    # LOAD LOCAL MODEL
    # ============================================================

    def _load_local_embedder(self):

        if self._local_embedder is not None:
            return self._local_embedder

        try:

            from chromadb.utils import embedding_functions

            self._local_embedder = (
                embedding_functions.DefaultEmbeddingFunction()
            )

            logger.info(
                "Local embedding model loaded successfully."
            )

        except Exception as error:

            logger.error(
                f"Could not load local embedding model: {error}"
            )

            self._local_embedder = None

    # ============================================================
    # STATUS
    # ============================================================

    def is_ready(self) -> bool:

        return self._local_embedder is not None

    def is_gemini_ready(self) -> bool:

        # Embeddings intentionally do not use Gemini.
        return False

    def get_embedding_provider_name(self) -> str:

        if self.is_ready():

            return (
                "Local ONNX Embeddings "
                "(all-MiniLM-L6-v2)"
            )

        return "Unavailable"

    # ============================================================
    # CONVERT VALUES
    # ============================================================

    @staticmethod
    def _convert_to_python_floats(
        embedding
    ) -> List[float]:

        return [
            float(value)
            for value in embedding
        ]

    # ============================================================
    # SINGLE EMBEDDING
    # ============================================================

    def get_embedding(
        self,
        text: str
    ) -> List[float]:

        if not text or not text.strip():

            raise ValueError(
                "Cannot create an embedding for empty text."
            )

        if not self.is_ready():

            self._load_local_embedder()

        if self._local_embedder is None:

            raise RuntimeError(
                "Local embedding model is not available."
            )

        try:

            embeddings = self._local_embedder(
                [text]
            )

            if not embeddings:

                raise RuntimeError(
                    "Embedding model returned no result."
                )

            return self._convert_to_python_floats(
                embeddings[0]
            )

        except Exception as error:

            logger.error(
                f"Embedding generation failed: {error}"
            )

            raise RuntimeError(
                f"Failed to generate embedding: {error}"
            ) from error

    # ============================================================
    # QUERY EMBEDDING
    # ============================================================

    def get_query_embedding(
        self,
        query: str
    ) -> List[float]:

        return self.get_embedding(query)

    # ============================================================
    # BATCH EMBEDDINGS
    # ============================================================

    def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:

        if not texts:
            return []

        if not self.is_ready():
            self._load_local_embedder()

        if self._local_embedder is None:

            raise RuntimeError(
                "Local embedding model is not available."
            )

        cleaned_texts = []

        for text in texts:

            if text is None:
                cleaned_texts.append("")
            else:
                cleaned_texts.append(
                    str(text)
                )

        all_embeddings = []

        try:

            for start in range(
                0,
                len(cleaned_texts),
                batch_size
            ):

                batch = cleaned_texts[
                    start:start + batch_size
                ]

                embeddings = (
                    self._local_embedder(batch)
                )

                if len(embeddings) != len(batch):

                    raise RuntimeError(
                        "Embedding count does not match "
                        "the input text count."
                    )

                for embedding in embeddings:

                    all_embeddings.append(
                        self._convert_to_python_floats(
                            embedding
                        )
                    )

        except Exception as error:

            logger.error(
                f"Batch embedding generation failed: {error}"
            )

            raise RuntimeError(
                f"Failed to generate batch embeddings: {error}"
            ) from error

        return all_embeddings


embedding_service = EmbeddingService()