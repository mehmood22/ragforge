"""Adapters for publishing RAGForge evaluation metrics to LangSmith."""

from dataclasses import asdict
from typing import Any

from evals.answer_metrics import evaluate_answer


def _extract_mapping(obj: Any, attr_name: str) -> dict[str, Any]:
    """Safely extract a dictionary from a LangSmith Run/Example object or mapping."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        nested = obj.get(attr_name)
        if isinstance(nested, dict):
            return nested
        return obj
    value = getattr(obj, attr_name, None)
    return value if isinstance(value, dict) else {}


def grounded_answer_evaluator(
    run_or_outputs: Any,
    example_or_reference: Any = None,
) -> list[dict[str, Any]]:
    """Convert shared answer metrics into LangSmith feedback."""

    outputs = _extract_mapping(run_or_outputs, "outputs")
    reference_outputs = _extract_mapping(example_or_reference, "outputs")

    metrics = evaluate_answer(
        expected_status=reference_outputs.get("expected_status", ""),
        actual_status=outputs.get("status", ""),
        answer=outputs.get("answer") or "",
        required_facts=reference_outputs.get("required_facts") or [],
        evidence=reference_outputs.get("evidence") or [],
        source_contents=[
            source["content"]
            for source in (outputs.get("sources") or [])
            if isinstance(source, dict) and "content" in source
        ],
    )

    return [
        {
            "key": name,
            "score": float(value),
        }
        for name, value in asdict(metrics).items()
        if value is not None
    ]
