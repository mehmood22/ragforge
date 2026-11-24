import pytest

from evals.answer_metrics import evaluate_answer


def test_correct_grounded_answer() -> None:
    result = evaluate_answer(
        expected_status="answered",
        actual_status="answered",
        answer="Dragoon used Apache Kafka.",
        required_facts=["Apache Kafka"],
        evidence=["Developed services using Apache Kafka."],
        source_contents=["Developed services using Apache Kafka."],
    )

    assert result.passed
    assert result.status_correct
    assert result.required_facts_present is True
    assert result.evidence_coverage == 1.0
    assert result.citation_contract_valid
    assert result.false_abstention is False


def test_missing_required_fact() -> None:
    result = evaluate_answer(
        expected_status="answered",
        actual_status="answered",
        answer="Dragoon used RabbitMQ.",
        required_facts=["Apache Kafka"],
        evidence=["Developed services using Apache Kafka."],
        source_contents=["Developed services using Apache Kafka."],
    )

    assert not result.passed
    assert result.required_facts_present is False


def test_missing_cited_evidence() -> None:
    result = evaluate_answer(
        expected_status="answered",
        actual_status="answered",
        answer="Dragoon used Apache Kafka.",
        required_facts=["Apache Kafka"],
        evidence=["Developed services using Apache Kafka."],
        source_contents=["Dragoon studied computer science."],
    )

    assert not result.passed
    assert result.evidence_coverage == 0.0


def test_partial_evidence_coverage() -> None:
    result = evaluate_answer(
        expected_status="answered",
        actual_status="answered",
        answer="Dragoon used Kafka and Redis.",
        required_facts=["Kafka", "Redis"],
        evidence=[
            "Developed services using Kafka.",
            "Implemented caching using Redis.",
        ],
        source_contents=["Developed services using Kafka."],
    )

    assert result.evidence_coverage == 0.5
    assert not result.passed


def test_answer_without_citations() -> None:
    result = evaluate_answer(
        expected_status="answered",
        actual_status="answered",
        answer="Dragoon used Kafka.",
        required_facts=["Kafka"],
        evidence=["Kafka"],
        source_contents=[],
    )

    assert not result.citation_contract_valid
    assert not result.passed


def test_correct_abstention() -> None:
    result = evaluate_answer(
        expected_status="insufficient_context",
        actual_status="insufficient_context",
        answer="The document does not contain this information.",
        required_facts=[],
        evidence=[],
        source_contents=[],
    )

    assert result.passed
    assert result.correct_abstention is True
    assert result.false_answer is False
    assert result.required_facts_present is None
    assert result.evidence_coverage is None


def test_false_answer() -> None:
    result = evaluate_answer(
        expected_status="insufficient_context",
        actual_status="answered",
        answer="Dragoon earns 100,000 euros annually.",
        required_facts=[],
        evidence=[],
        source_contents=["Professional summary"],
    )

    assert not result.passed
    assert result.false_answer is True
    assert result.correct_abstention is False


def test_false_abstention() -> None:
    result = evaluate_answer(
        expected_status="answered",
        actual_status="insufficient_context",
        answer="Insufficient information.",
        required_facts=["Kafka"],
        evidence=["Kafka"],
        source_contents=[],
    )

    assert not result.passed
    assert result.false_abstention is True


def test_abstention_with_sources() -> None:
    result = evaluate_answer(
        expected_status="insufficient_context",
        actual_status="insufficient_context",
        answer="Insufficient information.",
        required_facts=[],
        evidence=[],
        source_contents=["Unrelated content"],
    )

    assert not result.citation_contract_valid
    assert not result.passed


def test_invalid_ground_truth() -> None:
    with pytest.raises(ValueError, match="facts and evidence"):
        evaluate_answer(
            expected_status="answered",
            actual_status="answered",
            answer="Some answer",
            required_facts=[],
            evidence=[],
            source_contents=[],
        )
