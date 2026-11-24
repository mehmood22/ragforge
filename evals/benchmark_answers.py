"""Evaluate RAGForge answer generation end to end."""

import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from time import perf_counter
from uuid import UUID

from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from evals.answer_metrics import evaluate_answer
from ragforge.ai.service import QAService, get_answer_generator
from ragforge.core.config import get_settings
from ragforge.models.document import Document, DocumentStatus
from ragforge.retrieval.service import (
    RetrievalService,
    get_vector_store,
)


async def benchmark(
    document_id: UUID,
    dataset_path: Path,
    split: str,
    output_path: Path,
) -> None:
    settings = get_settings()

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    cases = [case for case in dataset if split == "all" or case["split"] == split]

    if not cases:
        raise ValueError("No evaluation cases found.")

    if any(case["document"] != dataset_path.stem for case in cases):
        raise ValueError("Dataset document identifier mismatch.")

    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )

    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    results = []

    try:
        async with session_factory() as session:
            document = await session.get(
                Document,
                document_id,
            )

            if (
                document is None
                or document.status != DocumentStatus.INDEXED.value
                or document.indexed_generation is None
            ):
                raise ValueError("Document is not available for evaluation.")

            generation_id = str(document.indexed_generation)

            service = QAService(
                retriever=RetrievalService(
                    session=session,
                    vector_store=get_vector_store(),
                ),
                generator=get_answer_generator(),
                top_k=settings.retrieval_top_k,
                min_score=settings.retrieval_min_score,
                max_context_chars=settings.rag_max_context_chars,
            )

            print(f"Document: {document_id}")
            print(f"Generation: {generation_id}")
            print(f"Model: {settings.groq_model}")
            print(f"Top K: {settings.retrieval_top_k}")
            print(f"Threshold: {settings.retrieval_min_score}")
            print(f"Cases: {len(cases)}\n")

            for case in cases:
                started = perf_counter()

                response = await service.ask(
                    document_id=document_id,
                    question=case["question"],
                )

                latency_ms = (perf_counter() - started) * 1000

                payload = response.model_dump(mode="json")

                metrics = evaluate_answer(
                    expected_status=case["expected_status"],
                    actual_status=payload["status"],
                    answer=payload["answer"],
                    required_facts=case["required_facts"],
                    evidence=case["evidence"],
                    source_contents=[
                        source["content"] for source in payload["sources"]
                    ],
                )

                results.append(
                    {
                        "case_id": case["id"],
                        "question": case["question"],
                        "reference_answer": case["reference_answer"],
                        "expected_status": case["expected_status"],
                        "response": payload,
                        "metrics": asdict(metrics),
                        "latency_ms": latency_ms,
                    }
                )

                label = "PASS" if metrics.passed else "FAIL"

                print(
                    f"[{label}] {case['id']} | {payload['status']} | {latency_ms:.1f}ms"
                )

                print(f"Question: {case['question']}")
                print(f"Answer: {payload['answer']}\n")

        metric_names = (
            "status_correct",
            "required_facts_present",
            "evidence_coverage",
            "citation_contract_valid",
            "correct_abstention",
            "false_answer",
            "false_abstention",
            "passed",
        )

        summary = {}

        for name in metric_names:
            values = [
                float(row["metrics"][name])
                for row in results
                if row["metrics"][name] is not None
            ]

            summary[name] = mean(values) if values else None

        report = {
            "created_at": datetime.now(UTC).isoformat(),
            "document_id": str(document_id),
            "generation_id": generation_id,
            "dataset": dataset_path.name,
            "split": split,
            "embedding_model": settings.embedding_model,
            "llm_model": settings.groq_model,
            "top_k": settings.retrieval_top_k,
            "min_score": settings.retrieval_min_score,
            "case_count": len(results),
            "mean_latency_ms": mean(row["latency_ms"] for row in results),
            "summary": summary,
            "cases": results,
        }

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(report, indent=2),
            encoding="utf-8",
        )

        print("Evaluation summary:")

        for name, value in summary.items():
            formatted = f"{value:.2%}" if value is not None else "N/A"

            print(f"{name}: {formatted}")

        print(f"\nReport saved: {output_path}")

    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark RAGForge answer quality.")

    parser.add_argument(
        "--document-id",
        type=UUID,
        required=True,
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evals/datasets/synthetic_cv.json"),
    )

    parser.add_argument(
        "--split",
        choices=["tuning", "held_out", "all"],
        default="tuning",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evals/reports/answers.json"),
    )

    args = parser.parse_args()

    asyncio.run(
        benchmark(
            document_id=args.document_id,
            dataset_path=args.dataset,
            split=args.split,
            output_path=args.output,
        )
    )


if __name__ == "__main__":
    main()
