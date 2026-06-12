"""Run a tiny deterministic evaluation set."""

from __future__ import annotations

import json
from pathlib import Path

from src.agent.workflow import PharmAssistAgent
from src.core.config import ROOT_DIR
from src.evaluation.metrics import keyword_hit, source_hit


def main() -> None:
    eval_path = ROOT_DIR / "data" / "eval" / "gmp_qa.jsonl"
    agent = PharmAssistAgent()
    rows = [json.loads(line) for line in eval_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    source_hits = 0
    keyword_scores: list[float] = []
    citation_hits = 0
    for row in rows:
        response = agent.run(row["question"], strategy="direct")
        source_hits += int(source_hit(response, row["expected_source"]))
        keyword_scores.append(keyword_hit(response, row["expected_keywords"]))
        citation_hits += int(response.citation_check.has_citation)

    total = len(rows) or 1
    print(f"cases={len(rows)}")
    print(f"source_hit_rate={source_hits / total:.2f}")
    print(f"keyword_hit_avg={sum(keyword_scores) / total:.2f}")
    print(f"citation_rate={citation_hits / total:.2f}")


if __name__ == "__main__":
    main()
