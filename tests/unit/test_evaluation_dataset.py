"""Tests for evaluation dataset versioning."""

from pathlib import Path

from evals.run_evaluation import build_dataset_name


def test_identical_cases_have_identical_names() -> None:
    path = Path("synthetic_cv.json")

    cases = [{"id": "cv-001", "question": "Who is Dragoon?"}]

    first = build_dataset_name(path, "all", cases)
    second = build_dataset_name(path, "all", cases)

    assert first == second


def test_changed_cases_have_different_names() -> None:
    path = Path("synthetic_cv.json")

    original = [{"id": "cv-001", "question": "Who is Dragoon?"}]

    updated = [{"id": "cv-001", "question": "Where does Dragoon work?"}]

    assert build_dataset_name(path, "all", original) != build_dataset_name(
        path, "all", updated
    )


def test_different_splits_have_different_names() -> None:
    path = Path("synthetic_cv.json")

    cases = [{"id": "cv-001", "question": "Who is Dragoon?"}]

    assert build_dataset_name(path, "tuning", cases) != build_dataset_name(
        path, "held_out", cases
    )


def test_dictionary_key_order_does_not_change_name() -> None:
    path = Path("synthetic_cv.json")

    first = [{"id": "cv-001", "question": "Who is Dragoon?"}]
    second = [{"question": "Who is Dragoon?", "id": "cv-001"}]

    assert build_dataset_name(path, "all", first) == build_dataset_name(
        path, "all", second
    )
