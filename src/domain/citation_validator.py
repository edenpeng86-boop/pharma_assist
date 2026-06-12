"""Validate that answers are grounded in retrieved evidence."""

from __future__ import annotations

import re

from src.core.models import CitationCheck, Evidence


def validate_citations(answer: str, evidence: list[Evidence]) -> CitationCheck:
    citation_ids = {int(match) for match in re.findall(r"\[(\d+)\]", answer)}
    has_citation = bool(citation_ids)
    valid_range = set(range(1, len(evidence) + 1))
    missing = sorted(citation_ids - valid_range)

    notes: list[str] = []
    if not evidence:
        notes.append("No evidence was retrieved.")
    if not has_citation:
        notes.append("Answer does not contain bracket citations.")
    if missing:
        notes.append("Answer references citations outside the evidence list.")

    return CitationCheck(
        has_citation=has_citation,
        grounded=bool(evidence) and has_citation and not missing,
        missing_sources=[str(item) for item in missing],
        notes=notes,
    )
