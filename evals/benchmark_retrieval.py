"""Benchmark RAGForge retrieval against annotated evidence."""

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
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

from evals.evidence import (
    calculate_evidence_coverage,
    map_evidence_to_chunks,
)
from evals.metrics import calculate_retrieval_metrics
from ragforge.core.config import get_settings
from ragforge.infrastructure.chroma import get_chroma_client
from ragforge.models.document import Document, DocumentStatus
from ragforge.retrieval.service import (
    RetrievalService,
    get_vector_store,
)


@dataclass(frozen=True, slots=True)
class BenchmarkConfig:
    top_k: int
    min_score: float


CONFIGURATIONS = (
    BenchmarkConfig(1, 0.0),
    BenchmarkConfig(2, 0.0),
    BenchmarkConfig(3, 0.0),
    BenchmarkConfig(5, 0.0),
    BenchmarkConfig(7, 0.0),
    BenchmarkConfig(10, 0.0),
    BenchmarkConfig(7, 0.15),
    BenchmarkConfig(7, 0.20),
    BenchmarkConfig(7, 0.30),
)


async def benchmark(
    document_id: UUID,
    dataset_path: Path,
    split: str,
    output_path: Path,
) -> None:
    settings = get_settings()

    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    cases = [
        case
        for case in dataset
        if case["split"] == split and case["expected_status"] == "answered"
    ]

    if not cases:
        raise ValueError(f"No answerable cases found for split: {split}")

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

    try:
        async with session_factory() as session:
            document = await session.get(
                Document,
                document_id,
            )

            if document is None:
                raise ValueError("Document not found.")

            if (
                document.status != DocumentStatus.INDEXED.value
                or document.indexed_generation is None
            ):
                raise ValueError("Document is not indexed.")

            generation_id = str(document.indexed_generation)

            collection = get_chroma_client().get_collection(
                name=settings.chroma_collection,
            )

            indexed = await asyncio.to_thread(
                collection.get,
                where={
                    "$and": [
                        {"document_id": str(document_id)},
                        {"generation_id": generation_id},
                    ]
                },
                include=["documents", "metadatas"],
            )

            documents = indexed["documents"]
            metadatas = indexed["metadatas"]

            if documents is None or metadatas is None:
                raise ValueError("Indexed content is missing.")

            chunks: dict[int, str] = {}

            for content, metadata in zip(
                documents,
                metadatas,
                strict=True,
            ):
                if content is None or metadata is None:
                    raise ValueError("Invalid indexed chunk.")

                chunk_id = int(str(metadata["chunk_index"]))

                if chunk_id in chunks:
                    raise ValueError(f"Duplicate chunk index: {chunk_id}")

                chunks[chunk_id] = content

            if not chunks:
                raise ValueError("No indexed chunks found.")

            print(f"Document: {document_id}")
            print(f"Generation: {generation_id}")
            print(f"Indexed chunks: {len(chunks)}")
            print(f"Evaluation split: {split}")
            print(f"Answerable cases: {len(cases)}")

            ground_truth = {
                case["id"]: map_evidence_to_chunks(
                    case["evidence"],
                    chunks,
                )
                for case in cases
            }

            print("\nEvidence mapping:")

            for case_id, matches in ground_truth.items():
                relevant = set().union(*matches.values())

                print(f"{case_id}: relevant chunks {sorted(relevant)}")

            retriever = RetrievalService(
                session=session,
                vector_store=get_vector_store(),
            )

            # Warm up the embedding model before timing.
            await retriever.search(
                document_id=document_id,
                query=cases[0]["question"],
                top_k=1,
                min_score=0.0,
            )

            summaries = []

            for config in CONFIGURATIONS:
                results = []

                for case in cases:
                    matches = ground_truth[case["id"]]
                    relevant_ids = set().union(*matches.values())

                    started = perf_counter()

                    retrieved = await retriever.search(
                        document_id=document_id,
                        query=case["question"],
                        top_k=config.top_k,
                        min_score=config.min_score,
                    )

                    latency_ms = (perf_counter() - started) * 1000

                    retrieved_ids = [chunk.chunk_index for chunk in retrieved]

                    metrics = calculate_retrieval_metrics(
                        retrieved_ids=retrieved_ids,
                        relevant_ids=sorted(relevant_ids),
                        k=config.top_k,
                    )

                    coverage = calculate_evidence_coverage(
                        retrieved_ids,
                        matches,
                    )

                    results.append(
                        {
                            "case_id": case["id"],
                            "question": case["question"],
                            "retrieved_ids": retrieved_ids,
                            "relevant_ids": sorted(relevant_ids),
                            "scores": [chunk.score for chunk in retrieved],
                            **asdict(metrics),
                            "evidence_coverage": coverage,
                            "latency_ms": latency_ms,
                        }
                    )

                summary = {
                    **asdict(config),
                    "case_count": len(results),
                    "hit_rate": mean(row["hit_rate"] for row in results),
                    "precision": mean(row["precision"] for row in results),
                    "recall": mean(row["recall"] for row in results),
                    "mrr": mean(row["reciprocal_rank"] for row in results),
                    "evidence_coverage": mean(
                        row["evidence_coverage"] for row in results
                    ),
                    "mean_latency_ms": mean(row["latency_ms"] for row in results),
                    "cases": results,
                }

                summaries.append(summary)

                print(
                    f"K={config.top_k:2d} "
                    f"Threshold={config.min_score:.2f} "
                    f"Hit={summary['hit_rate']:.3f} "
                    f"Precision={summary['precision']:.3f} "
                    f"Recall={summary['recall']:.3f} "
                    f"MRR={summary['mrr']:.3f} "
                    f"Coverage={summary['evidence_coverage']:.3f} "
                    f"Latency={summary['mean_latency_ms']:.1f}ms"
                )

            report = {
                "created_at": datetime.now(UTC).isoformat(),
                "document_id": str(document_id),
                "generation_id": generation_id,
                "dataset": dataset_path.name,
                "split": split,
                "embedding_model": settings.embedding_model,
                "indexed_chunks": len(chunks),
                "configurations": summaries,
            }

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_path.write_text(
                json.dumps(report, indent=2),
                encoding="utf-8",
            )

            print(f"\nReport saved: {output_path}")

    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark RAGForge retrieval quality."
    )

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
        choices=["tuning", "held_out"],
        default="tuning",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evals/reports/retrieval.json"),
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
