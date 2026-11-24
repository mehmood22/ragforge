"""Run RAGForge answer evaluations through LangSmith."""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from langsmith import Client, aevaluate
from langsmith.evaluation import EvaluationResult, EvaluationResults
from langsmith.schemas import Example, Run
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from evals.langsmith_evaluators import grounded_answer_evaluator
from ragforge.ai.service import QAService, get_answer_generator
from ragforge.core.config import get_settings
from ragforge.models.document import Document, DocumentStatus
from ragforge.retrieval.service import (
    RetrievalService,
    get_vector_store,
)


def load_cases(
    dataset_path: Path,
    split: str,
) -> list[dict[str, Any]]:
    """Load evaluation cases for the selected split."""

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    cases = [case for case in dataset if split == "all" or case["split"] == split]

    if not cases:
        raise ValueError("No evaluation cases found.")

    if any(case["document"] != dataset_path.stem for case in cases):
        raise ValueError("Dataset document identifier mismatch.")

    return cases


def build_dataset_name(
    dataset_path: Path,
    split: str,
    cases: list[dict[str, Any]],
) -> str:
    """Generate a content-versioned LangSmith dataset name."""

    canonical_data = json.dumps(
        cases,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    fingerprint = hashlib.sha256(canonical_data.encode("utf-8")).hexdigest()[:12]

    return f"ragforge-{dataset_path.stem}-{split}-{fingerprint}"


def _grounded_answer_evaluator(
    run: Run,
    example: Example | None,
) -> EvaluationResults:
    """Adapt grounded_answer_evaluator to LangSmith's EvaluationResults contract."""

    raw_results = grounded_answer_evaluator(run, example)
    return EvaluationResults(
        results=[
            EvaluationResult(
                key=str(item["key"]),
                score=item.get("score"),
                value=item.get("value"),
                comment=item.get("comment"),
            )
            for item in raw_results
        ]
    )


async def run_evaluation(
    document_id: UUID,
    dataset_path: Path,
    split: str,
) -> None:
    """Evaluate the application against a versioned dataset."""

    settings = get_settings()

    cases = load_cases(dataset_path, split)

    dataset_name = build_dataset_name(
        dataset_path,
        split,
        cases,
    )

    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )

    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

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

        vector_store = get_vector_store()
        generator = get_answer_generator()

        client = Client()

        if client.has_dataset(dataset_name=dataset_name):
            dataset = client.read_dataset(
                dataset_name=dataset_name,
            )

            existing_examples = list(client.list_examples(dataset_id=dataset.id))

            if len(existing_examples) != len(cases):
                raise RuntimeError("Remote dataset has an unexpected example count.")
        else:
            dataset = client.create_dataset(
                dataset_name=dataset_name,
                description=("Versioned RAGForge grounded answer evaluation."),
            )

            client.create_examples(
                dataset_id=dataset.id,
                inputs=[
                    {
                        "case_id": case["id"],
                        "question": case["question"],
                    }
                    for case in cases
                ],
                outputs=[
                    {
                        "expected_status": case["expected_status"],
                        "reference_answer": case["reference_answer"],
                        "required_facts": case["required_facts"],
                        "evidence": case["evidence"],
                    }
                    for case in cases
                ],
            )

        async def target(
            inputs: dict[str, Any],
        ) -> dict[str, Any]:
            """Execute the actual RAGForge QA pipeline."""

            async with session_factory() as session:
                service = QAService(
                    retriever=RetrievalService(
                        session=session,
                        vector_store=vector_store,
                    ),
                    generator=generator,
                    top_k=settings.retrieval_top_k,
                    min_score=settings.retrieval_min_score,
                    max_context_chars=settings.rag_max_context_chars,
                )

                result = await service.ask(
                    document_id=document_id,
                    question=inputs["question"],
                )

                return result.model_dump(mode="json")

        print(f"Dataset: {dataset_name}")
        print(f"Document: {document_id}")
        print(f"Cases: {len(cases)}")
        print(f"Split: {split}")

        await aevaluate(
            target,
            data=dataset.name,
            evaluators=[_grounded_answer_evaluator],
            experiment_prefix=(f"ragforge-{dataset_path.stem}-{split}"),
            metadata={
                "document_id": str(document_id),
                "generation_id": generation_id,
                "embedding_model": settings.embedding_model,
                "llm_model": settings.groq_model,
                "top_k": settings.retrieval_top_k,
                "min_score": settings.retrieval_min_score,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "max_context_chars": settings.rag_max_context_chars,
                "llm_temperature": settings.llm_temperature,
                "llm_max_tokens": settings.llm_max_tokens,
                "split": split,
            },
            max_concurrency=1,
            client=client,
        )

    finally:
        await engine.dispose()


def main() -> None:
    """Parse evaluation arguments."""

    parser = argparse.ArgumentParser(
        description="Run RAGForge LangSmith evaluation.",
    )

    parser.add_argument(
        "--document-id",
        type=UUID,
        default=os.getenv("EVAL_DOCUMENT_ID") or None,
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("evals/datasets/synthetic_telecom.json"),
    )

    parser.add_argument(
        "--split",
        choices=["tuning", "held_out", "all"],
        default="all",
    )

    args = parser.parse_args()

    if args.document_id is None:
        parser.error("Provide --document-id or set EVAL_DOCUMENT_ID.")

    asyncio.run(
        run_evaluation(
            document_id=args.document_id,
            dataset_path=args.dataset,
            split=args.split,
        )
    )


if __name__ == "__main__":
    main()
