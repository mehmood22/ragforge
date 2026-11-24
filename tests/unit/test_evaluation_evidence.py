import pytest

from evals.evidence import (
    calculate_evidence_coverage,
    map_evidence_to_chunks,
    normalize_text,
)


def test_normalize_whitespace() -> None:
    assert (
        normalize_text("Dragoon\n\nPete   is an Engineer.")
        == "dragoon pete is an engineer."
    )


def test_normalize_html_entities() -> None:
    assert normalize_text("Dragoon&#x20;Pete") == "dragoon pete"


def test_normalize_hyphenated_line_break() -> None:
    assert normalize_text("event-\ndriven services") == "event-driven services"


def test_normalize_unicode_dash() -> None:
    assert normalize_text("2021 – 2024") == "2021 - 2024"


def test_map_single_evidence() -> None:
    result = map_evidence_to_chunks(
        evidence=["Apache Kafka"],
        chunks={
            0: "Professional summary",
            1: "Developed services using Apache Kafka.",
        },
    )

    assert result == {"Apache Kafka": {1}}


def test_map_overlapping_evidence() -> None:
    result = map_evidence_to_chunks(
        evidence=["RabbitMQ"],
        chunks={
            1: "Payment processing using RabbitMQ.",
            2: "RabbitMQ. Professional experience.",
        },
    )

    assert result == {"RabbitMQ": {1, 2}}


def test_missing_evidence() -> None:
    with pytest.raises(ValueError, match="Evidence not found"):
        map_evidence_to_chunks(
            evidence=["Rust"],
            chunks={0: "Python and Java"},
        )


def test_empty_evidence_passage() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        map_evidence_to_chunks(
            evidence=["   "],
            chunks={0: "Python"},
        )


def test_complete_evidence_coverage() -> None:
    result = calculate_evidence_coverage(
        retrieved_ids=[1, 2],
        evidence_matches={
            "Kafka": {1},
            "Education": {2},
        },
    )

    assert result == 1.0


def test_partial_evidence_coverage() -> None:
    result = calculate_evidence_coverage(
        retrieved_ids=[1],
        evidence_matches={
            "Kafka": {1},
            "Education": {2},
        },
    )

    assert result == 0.5


def test_duplicate_evidence_coverage() -> None:
    result = calculate_evidence_coverage(
        retrieved_ids=[2],
        evidence_matches={"RabbitMQ": {1, 2}},
    )

    assert result == 1.0


def test_no_evidence_coverage() -> None:
    result = calculate_evidence_coverage(
        retrieved_ids=[0],
        evidence_matches={"Kafka": {1}},
    )

    assert result == 0.0


def test_empty_ground_truth() -> None:
    with pytest.raises(ValueError, match="ground truth"):
        calculate_evidence_coverage(
            retrieved_ids=[1],
            evidence_matches={},
        )
