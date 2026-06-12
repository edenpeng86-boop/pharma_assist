"""Initialize the local Chroma knowledge base."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.config import ROOT_DIR, config
from src.rag.base import RAGEngine
from src.rag.document_loader import load_knowledge_base


def main() -> None:
    docs_path = ROOT_DIR / config["knowledge_base"].get("docs_path", "data/knowledge")
    docs = load_knowledge_base(docs_path)
    if not docs:
        raise SystemExit(f"No supported documents found in {docs_path}")

    engine = RAGEngine()
    chunks = engine.build_index(docs)
    print(f"Loaded {len(docs)} document(s).")
    print(f"Built {chunks} chunk(s) in {engine.index_path}.")


if __name__ == "__main__":
    main()
