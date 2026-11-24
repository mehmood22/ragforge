"""Tests for the LangSmith evaluation adapter."""

from evals.langsmith_evaluators import grounded_answer_evaluator


def test_correct_grounded_answer() -> None:
    outputs = {
        "status": "answered",
        "answer": "Autopay occurs after 14 days.",
        "sources": [
            {
                "content": (
                    "Autopay customers are charged 14 days after invoice generation."
                ),
            }
        ],
    }

    reference_outputs = {
        "expected_status": "answered",
        "required_facts": ["14 days"],
        "evidence": ["14 days after invoice generation."],
    }

    feedback = grounded_answer_evaluator(
        outputs,
        reference_outputs,
    )

    scores = {item["key"]: item["score"] for item in feedback}

    assert scores["passed"] == 1.0
    assert scores["status_correct"] == 1.0
    assert scores["required_facts_present"] == 1.0
    assert scores["evidence_coverage"] == 1.0
    assert scores["citation_contract_valid"] == 1.0
    assert scores["false_abstention"] == 0.0

    assert "correct_abstention" not in scores
    assert "false_answer" not in scores


def test_correct_abstention() -> None:
    outputs = {
        "status": "insufficient_context",
        "answer": "Insufficient information.",
        "sources": [],
    }

    reference_outputs = {
        "expected_status": "insufficient_context",
        "required_facts": [],
        "evidence": [],
    }

    feedback = grounded_answer_evaluator(
        outputs,
        reference_outputs,
    )

    scores = {item["key"]: item["score"] for item in feedback}

    assert scores["passed"] == 1.0
    assert scores["correct_abstention"] == 1.0
    assert scores["false_answer"] == 0.0

    assert "required_facts_present" not in scores
    assert "evidence_coverage" not in scores
    assert "false_abstention" not in scores


def test_unsupported_answer_fails() -> None:
    outputs = {
        "status": "answered",
        "answer": "The company earns one billion dollars.",
        "sources": [{"content": "Unrelated information."}],
    }

    reference_outputs = {
        "expected_status": "insufficient_context",
        "required_facts": [],
        "evidence": [],
    }

    feedback = grounded_answer_evaluator(
        outputs,
        reference_outputs,
    )

    scores = {item["key"]: item["score"] for item in feedback}

    assert scores["passed"] == 0.0
    assert scores["false_answer"] == 1.0
    assert scores["correct_abstention"] == 0.0


def test_missing_output_fails() -> None:
    reference_outputs = {
        "expected_status": "answered",
        "required_facts": ["14 days"],
        "evidence": ["14 days after invoice generation."],
    }

    feedback = grounded_answer_evaluator(
        {},
        reference_outputs,
    )

    scores = {item["key"]: item["score"] for item in feedback}

    assert scores["passed"] == 0.0
    assert scores["status_correct"] == 0.0
    assert scores["evidence_coverage"] == 0.0
    assert scores["citation_contract_valid"] == 0.0
