"""Relevance scoring utilities for normalized document embeddings."""

import math


def squared_l2_to_relevance(distance: float) -> float:
    """Convert squared L2 distance into a non-negative cosine score.

    For unit-normalized embeddings:

        squared_l2 = 2 - 2 * cosine_similarity

    Negative cosine similarities are mapped to zero to maintain
    the application's relevance score contract of [0, 1].

    Args:
        distance: Squared Euclidean distance returned by ChromaDB.

    Returns:
        A relevance score between zero and one.

    Raises:
        ValueError: If the distance is invalid.
    """
    if not math.isfinite(distance):
        raise ValueError("Distance must be finite.")

    tolerance = 1e-6

    if distance < -tolerance or distance > 4.0 + tolerance:
        raise ValueError(
            "Squared L2 distance must be between 0 and 4 for normalized embeddings."
        )

    cosine_similarity = 1.0 - distance / 2.0

    return max(0.0, min(1.0, cosine_similarity))
