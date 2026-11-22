from functools import lru_cache
from typing import Protocol
from uuid import UUID

from langchain_groq import ChatGroq
from pydantic import SecretStr

from ragforge.ai.prompts import RAG_PROMPT
from ragforge.core.config import get_settings
from ragforge.retrieval.service import RetrievalService
from ragforge.schemas.qa import (
    AnswerSource,
    AnswerStatus,
    AskResponse,
    GeneratedAnswer,
)
from ragforge.schemas.retrieval import RetrievedChunk

INSUFFICIENT_ANSWER = (
    "The provided documents do not contain enough information to answer this question."
)


class AnswerGenerator(Protocol):
    async def ainvoke(self, input: object) -> GeneratedAnswer: ...


@lru_cache(maxsize=1)
def get_answer_generator():
    settings = get_settings()

    if settings.groq_api_key is None:
        raise RuntimeError("GROQ_API_KEY is not configured")

    model = ChatGroq(
        model=settings.groq_model,
        api_key=SecretStr(settings.groq_api_key.get_secret_value()),
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        max_retries=2,
        timeout=30,
    )

    return model.with_structured_output(
        GeneratedAnswer,
        method="function_calling",
    )


class QAService:
    def __init__(
        self,
        retriever: RetrievalService,
        generator: AnswerGenerator,
        *,
        top_k: int,
        min_score: float,
        max_context_chars: int,
    ) -> None:
        self.retriever = retriever
        self.generator = generator
        self.top_k = top_k
        self.min_score = min_score
        self.max_context_chars = max_context_chars

    async def ask(
        self,
        document_id: UUID,
        question: str,
    ) -> AskResponse:
        chunks = await self.retriever.search(
            document_id=document_id,
            query=question,
            top_k=self.top_k,
            min_score=self.min_score,
        )

        return await self.answer_from_chunks(
            question=question,
            chunks=chunks,
        )

    async def answer_from_chunks(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> AskResponse:
        if not chunks:
            return self._insufficient()

        context_parts: list[str] = []
        available_sources: dict[int, AnswerSource] = {}
        used_chars = 0

        for chunk in chunks:
            citation_id = len(available_sources) + 1

            excerpt = (
                f"[Source {citation_id} | Page {chunk.page_number}]\n{chunk.content}"
            )

            if used_chars + len(excerpt) > self.max_context_chars:
                break

            context_parts.append(excerpt)
            used_chars += len(excerpt)

            available_sources[citation_id] = AnswerSource(
                citation=citation_id,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
            )

        if not context_parts:
            return self._insufficient()

        prompt = RAG_PROMPT.invoke(
            {
                "context": "\n\n".join(context_parts),
                "question": question,
            }
        )

        result = await self.generator.ainvoke(prompt)

        if (
            result.status != "answered"
            or not result.answer.strip()
            or not result.citations
        ):
            return self._insufficient()

        valid_citations = list(dict.fromkeys(result.citations))

        if any(citation not in available_sources for citation in valid_citations):
            return self._insufficient()

        sources = [available_sources[citation] for citation in valid_citations]

        return AskResponse(
            answer=result.answer.strip(),
            status=AnswerStatus.ANSWERED,
            sources=sources,
        )

    @staticmethod
    def _insufficient() -> AskResponse:
        return AskResponse(
            answer=INSUFFICIENT_ANSWER,
            status=AnswerStatus.INSUFFICIENT_CONTEXT,
            sources=[],
        )
