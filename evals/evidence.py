"""Map reference evidence to indexed document chunks."""

import html
import re
import unicodedata
from collections.abc import Mapping, Sequence


def normalize_text(text: str) -> str:
    """Normalize text for evaluation evidence matching."""
    text = html.unescape(text)

    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\u00ad", "")

    text = re.sub(
        r"(?<=\w)-\s*\n\s*(?=\w)",
        "-",
        text,
    )

    text = re.sub(r"[\u2010-\u2015]", "-", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip().casefold()


def map_evidence_to_chunks(
    evidence: Sequence[str],
    chunks: Mapping[int, str],
) -> dict[str, set[int]]:
    """Find indexed chunks containing each evidence passage.

    Raises:
        ValueError: If an evidence passage is empty or cannot
            be found in any indexed chunk.
    """
    normalized_chunks = {
        chunk_id: normalize_text(content) for chunk_id, content in chunks.items()
    }

    matches: dict[str, set[int]] = {}

    for passage in evidence:
        normalized_passage = normalize_text(passage)

        if not normalized_passage:
            raise ValueError("Evidence passage cannot be empty.")

        matching_ids = {
            chunk_id
            for chunk_id, content in normalized_chunks.items()
            if normalized_passage in content
        }

        if not matching_ids:
            raise ValueError(f"Evidence not found in indexed chunks: {passage!r}")

        matches[passage] = matching_ids

    return matches


def calculate_evidence_coverage(
    retrieved_ids: Sequence[int],
    evidence_matches: Mapping[str, set[int]],
) -> float:
    """Calculate the proportion of evidence passages retrieved."""
    if not evidence_matches:
        raise ValueError("Evidence coverage requires ground truth.")

    retrieved = set(retrieved_ids)

    covered = sum(
        bool(retrieved.intersection(chunk_ids))
        for chunk_ids in evidence_matches.values()
    )

    return covered / len(evidence_matches)
