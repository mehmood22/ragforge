import pytest

from ragforge.infrastructure.collection import (
    CollectionCompatibilityError,
    validate_collection,
)

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def test_compatible_collection() -> None:
    validate_collection(
        metadata={"embedding_model": MODEL},
        configuration={"hnsw": {"space": "l2"}},
        expected_embedding_model=MODEL,
    )


def test_incompatible_embedding_model() -> None:
    with pytest.raises(
        CollectionCompatibilityError,
        match="embedding model",
    ):
        validate_collection(
            metadata={"embedding_model": "different-model"},
            configuration={"hnsw": {"space": "l2"}},
            expected_embedding_model=MODEL,
        )


@pytest.mark.parametrize("metadata", [None, {}])
def test_missing_embedding_metadata(
    metadata: dict[str, object] | None,
) -> None:
    with pytest.raises(
        CollectionCompatibilityError,
        match="embedding model",
    ):
        validate_collection(
            metadata=metadata,
            configuration={"hnsw": {"space": "l2"}},
            expected_embedding_model=MODEL,
        )


@pytest.mark.parametrize("metric", ["cosine", "ip"])
def test_unsupported_distance_metric(metric: str) -> None:
    with pytest.raises(
        CollectionCompatibilityError,
        match="distance metric",
    ):
        validate_collection(
            metadata={"embedding_model": MODEL},
            configuration={"hnsw": {"space": metric}},
            expected_embedding_model=MODEL,
        )


@pytest.mark.parametrize(
    "configuration",
    [
        {},
        {"hnsw": None},
        {"hnsw": "invalid"},
    ],
)
def test_invalid_hnsw_configuration(
    configuration: dict[str, object],
) -> None:
    with pytest.raises(
        CollectionCompatibilityError,
        match="HNSW configuration",
    ):
        validate_collection(
            metadata={"embedding_model": MODEL},
            configuration=configuration,
            expected_embedding_model=MODEL,
        )


def test_missing_distance_metric() -> None:
    with pytest.raises(
        CollectionCompatibilityError,
        match="distance metric",
    ):
        validate_collection(
            metadata={"embedding_model": MODEL},
            configuration={"hnsw": {}},
            expected_embedding_model=MODEL,
        )
