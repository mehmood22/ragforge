"""Reusable metrics for evaluating document retrieval quality."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    """Retrieval evaluation results for a single question."""

    hit_rate: float
    precision: float
    recall: float
    reciprocal_rank: float


def calculate_retrieval_metrics(
    retrieved_ids: Sequence[int],
    relevant_ids: Sequence[int],
    k: int,
) -> RetrievalMetrics:
    """Evaluate ranked retrieval results against known relevant chunks.

    Args:
        retrieved_ids: Chunk IDs ordered by retrieval rank.
        relevant_ids: Ground-truth relevant chunk IDs.
        k: Maximum number of ranked results to evaluate.

    Returns:
        Retrieval metrics for the supplied question.

    Raises:
        ValueError: If k is invalid, ground truth is empty,
            or retrieved chunk IDs contain duplicates.
    """
    if k <= 0:
        raise ValueError("k must be greater than zero.")

    relevant = set(relevant_ids)

    if not relevant:
        raise ValueError("Retrieval metrics require at least one relevant chunk.")

    ranked = list(retrieved_ids[:k])

    if len(ranked) != len(set(ranked)):
        raise ValueError("Retrieved chunk IDs must be unique.")

    matches = set(ranked).intersection(relevant)

    hit_rate = float(bool(matches))

    precision = len(matches) / k

    recall = len(matches) / len(relevant)

    reciprocal_rank = 0.0

    for rank, chunk_id in enumerate(ranked, start=1):
        if chunk_id in relevant:
            reciprocal_rank = 1.0 / rank
            break

    return RetrievalMetrics(
        hit_rate=hit_rate,
        precision=precision,
        recall=recall,
        reciprocal_rank=reciprocal_rank,
    )
