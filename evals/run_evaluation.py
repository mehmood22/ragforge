import asyncio
import json
import os
from pathlib import Path
from uuid import UUID

from langsmith import Client, aevaluate
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from ragforge.ai.service import QAService, get_answer_generator
from ragforge.core.config import get_settings
from ragforge.retrieval.service import RetrievalService, get_vector_store


DATASET_NAME = "ragforge-rag-quality-v1"


async def main() -> None:
    settings = get_settings()
    client = Client()
    document_id = UUID(os.environ["EVAL_DOCUMENT_ID"])

    dataset_path = Path(__file__).with_name("dataset.json")
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))

    if client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Synthetic grounded RAG evaluation cases",
        )
        client.create_examples(
            dataset_id=dataset.id,
            inputs=[{"question": case["question"]} for case in cases],
            outputs=[
                {
                    "expected_status": case["expected_status"],
                    "required_facts": case["required_facts"],
                }
                for case in cases
            ],
        )

    eval_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )
    EvalSessionFactory = async_sessionmaker(
        bind=eval_engine,
        expire_on_commit=False,
    )
    vector_store = get_vector_store()
    generator = get_answer_generator()

    async def target(inputs: dict) -> dict:
        async with EvalSessionFactory() as session:
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
            result = await service.ask(document_id, inputs["question"])
            return result.model_dump(mode="json")

    def abstention_evaluator(run, example) -> dict:
        outputs = run.outputs or {}
        return {
            "key": "correct_abstention",
            "score": int(outputs.get("status") == example.outputs["expected_status"]),
        }

    def required_facts_evaluator(run, example) -> dict:
        facts = example.outputs["required_facts"]
        if not facts:
            return {"key": "required_facts_present", "score": 1}
        outputs = run.outputs or {}
        answer = (outputs.get("answer") or "").casefold()
        return {
            "key": "required_facts_present",
            "score": int(all(fact.casefold() in answer for fact in facts)),
        }

    try:
        await aevaluate(
            target,
            data=dataset.name,
            evaluators=[abstention_evaluator, required_facts_evaluator],
            experiment_prefix="ragforge",
            max_concurrency=1,
        )
    finally:
        await eval_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())