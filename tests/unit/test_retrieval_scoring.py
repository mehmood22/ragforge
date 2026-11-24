import pytest

from ragforge.retrieval.scoring import squared_l2_to_relevance


@pytest.mark.parametrize(
    ("distance", "expected"),
    [
        (0.0, 1.0),
        (0.5, 0.75),
        (1.0, 0.5),
        (1.5, 0.25),
        (2.0, 0.0),
        (3.0, 0.0),
        (4.0, 0.0),
    ],
)
def test_squared_l2_to_relevance(
    distance: float,
    expected: float,
) -> None:
    assert squared_l2_to_relevance(distance) == pytest.approx(expected)


@pytest.mark.parametrize(
    "distance",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        -0.1,
        4.1,
    ],
)
def test_invalid_distance_raises_error(
    distance: float,
) -> None:
    with pytest.raises(ValueError):
        squared_l2_to_relevance(distance)


@pytest.mark.parametrize(
    ("distance", "expected"),
    [
        (-1e-8, 1.0),
        (4.0 + 1e-8, 0.0),
    ],
)
def test_floating_point_tolerance(
    distance: float,
    expected: float,
) -> None:
    assert squared_l2_to_relevance(distance) == pytest.approx(expected)


def test_name_query_regression() -> None:
    distance = 1.316663

    score = squared_l2_to_relevance(distance)

    assert score == pytest.approx(0.3416685)
    assert score >= 0.30


def test_unrelated_query_regression() -> None:
    distance = 1.821618

    score = squared_l2_to_relevance(distance)

    assert score == pytest.approx(0.089191)
    assert score < 0.30


def test_relevance_decreases_as_distance_increases() -> None:
    distances = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]

    scores = [squared_l2_to_relevance(distance) for distance in distances]

    assert scores == sorted(scores, reverse=True)
