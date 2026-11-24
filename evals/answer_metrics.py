"""Deterministic metrics for grounded answer evaluation."""

from collections.abc import Sequence
from dataclasses import dataclass

from evals.evidence import normalize_text


@dataclass(frozen=True, slots=True)
class AnswerMetrics:
    """Evaluation results for a generated answer."""

    status_correct: bool
    required_facts_present: bool | None
    evidence_coverage: float | None
    citation_contract_valid: bool
    correct_abstention: bool | None
    false_answer: bool | None
    false_abstention: bool | None
    passed: bool


def evaluate_answer(
    *,
    expected_status: str,
    actual_status: str,
    answer: str,
    required_facts: Sequence[str],
    evidence: Sequence[str],
    source_contents: Sequence[str],
) -> AnswerMetrics:
    """Evaluate an answer against annotated expectations."""
    valid_statuses = {
        "answered",
        "insufficient_context",
    }

    if expected_status not in valid_statuses:
        raise ValueError("Invalid expected status.")

    expected_answerable = expected_status == "answered"
    actual_answered = actual_status == "answered"

    status_correct = expected_status == actual_status

    normalized_answer = normalize_text(answer)

    facts_present: bool | None = None
    evidence_coverage: float | None = None

    if expected_answerable:
        if not required_facts or not evidence:
            raise ValueError("Answerable cases require facts and evidence.")

        facts_present = actual_answered and all(
            normalize_text(fact) in normalized_answer for fact in required_facts
        )

        normalized_sources = [normalize_text(content) for content in source_contents]

        covered = sum(
            any(normalize_text(passage) in source for source in normalized_sources)
            for passage in evidence
        )

        evidence_coverage = covered / len(evidence)

    citation_contract_valid = (
        actual_answered
        and bool(normalized_answer)
        and bool(source_contents)
        and all(bool(normalize_text(content)) for content in source_contents)
    ) or (actual_status == "insufficient_context" and not source_contents)

    correct_abstention = status_correct if not expected_answerable else None

    false_answer = actual_answered if not expected_answerable else None

    false_abstention = (
        actual_status == "insufficient_context" if expected_answerable else None
    )

    passed = status_correct and citation_contract_valid

    if expected_answerable:
        passed = passed and facts_present is True and evidence_coverage == 1.0

    return AnswerMetrics(
        status_correct=status_correct,
        required_facts_present=facts_present,
        evidence_coverage=evidence_coverage,
        citation_contract_valid=citation_contract_valid,
        correct_abstention=correct_abstention,
        false_answer=false_answer,
        false_abstention=false_abstention,
        passed=passed,
    )
