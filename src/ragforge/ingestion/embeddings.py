from functools import lru_cache

from sentence_transformers import SentenceTransformer

from ragforge.core.config import get_settings


class EmbeddingService:
    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=32,
        )

        return vectors.tolist()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(settings.embedding_model)
