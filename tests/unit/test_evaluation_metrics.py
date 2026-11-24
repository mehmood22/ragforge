import pytest

from evals.metrics import calculate_retrieval_metrics


def test_perfect_retrieval() -> None:
    result = calculate_retrieval_metrics(
        retrieved_ids=[1, 2, 3],
        relevant_ids=[1, 2, 3],
        k=3,
    )

    assert result.hit_rate == 1.0
    assert result.precision == 1.0
    assert result.recall == 1.0
    assert result.reciprocal_rank == 1.0


def test_partial_retrieval() -> None:
    result = calculate_retrieval_metrics(
        retrieved_ids=[0, 4, 2, 8, 1],
        relevant_ids=[2, 4, 5],
        k=5,
    )

    assert result.hit_rate == 1.0
    assert result.precision == pytest.approx(0.4)
    assert result.recall == pytest.approx(2 / 3)
    assert result.reciprocal_rank == pytest.approx(0.5)


def test_no_relevant_results() -> None:
    result = calculate_retrieval_metrics(
        retrieved_ids=[7, 8, 9],
        relevant_ids=[1, 2, 3],
        k=3,
    )

    assert result.hit_rate == 0.0
    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.reciprocal_rank == 0.0


def test_empty_retrieval_results() -> None:
    result = calculate_retrieval_metrics(
        retrieved_ids=[],
        relevant_ids=[1, 2],
        k=5,
    )

    assert result.hit_rate == 0.0
    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.reciprocal_rank == 0.0


def test_respects_top_k() -> None:
    result = calculate_retrieval_metrics(
        retrieved_ids=[8, 9, 1],
        relevant_ids=[1],
        k=2,
    )

    assert result.hit_rate == 0.0
    assert result.recall == 0.0


def test_fewer_results_than_requested() -> None:
    result = calculate_retrieval_metrics(
        retrieved_ids=[1, 2],
        relevant_ids=[1, 2],
        k=5,
    )

    assert result.precision == pytest.approx(0.4)
    assert result.recall == 1.0


@pytest.mark.parametrize("k", [0, -1])
def test_invalid_k(k: int) -> None:
    with pytest.raises(ValueError, match="k must be"):
        calculate_retrieval_metrics(
            retrieved_ids=[1],
            relevant_ids=[1],
            k=k,
        )


def test_empty_ground_truth() -> None:
    with pytest.raises(ValueError, match="relevant chunk"):
        calculate_retrieval_metrics(
            retrieved_ids=[1, 2],
            relevant_ids=[],
            k=2,
        )


def test_duplicate_retrieved_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        calculate_retrieval_metrics(
            retrieved_ids=[1, 1, 2],
            relevant_ids=[1, 2],
            k=3,
        )


def test_duplicate_ground_truth_ids() -> None:
    result = calculate_retrieval_metrics(
        retrieved_ids=[1, 2],
        relevant_ids=[1, 1, 2],
        k=2,
    )

    assert result.precision == 1.0
    assert result.recall == 1.0
