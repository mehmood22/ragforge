"""Validate vector collection compatibility."""

from collections.abc import Mapping


class CollectionCompatibilityError(RuntimeError):
    """Raised when a collection is incompatible with retrieval settings."""


def validate_collection(
    metadata: Mapping[str, object] | None,
    configuration: Mapping[str, object],
    expected_embedding_model: str,
) -> None:
    """Validate the embedding model and distance metric.

    RAGForge currently requires normalized embeddings stored
    in a collection using squared L2 distance.
    """
    collection_metadata = metadata or {}

    actual_model = collection_metadata.get("embedding_model")

    if actual_model != expected_embedding_model:
        raise CollectionCompatibilityError(
            "Collection embedding model does not match "
            "the configured embedding model. "
            f"Expected: {expected_embedding_model}. "
            f"Found: {actual_model}."
        )

    hnsw = configuration.get("hnsw")

    if not isinstance(hnsw, Mapping):
        raise CollectionCompatibilityError(
            "Collection does not have a supported HNSW configuration."
        )

    distance_metric = hnsw.get("space")

    if distance_metric != "l2":
        raise CollectionCompatibilityError(
            f"Collection distance metric must be 'l2'. Found: {distance_metric}."
        )
