"""Metadata-preserving Chroma RAG engine."""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.config import ROOT_DIR, config
from src.core.models import Evidence
from src.rag.embeddings import get_embeddings


class RAGEngine:
    def __init__(self, collection_name: str | None = None) -> None:
        rag_cfg = config["rag"]
        kb_cfg = config["knowledge_base"]
        self.collection_name = collection_name or rag_cfg.get("collection_name", "pharmassist")
        self.chunk_size = int(rag_cfg.get("chunk_size", 600))
        self.chunk_overlap = int(rag_cfg.get("chunk_overlap", 80))
        self.top_k = int(rag_cfg.get("top_k", 8))
        self.persist_dir = ROOT_DIR / kb_cfg.get("persist_dir", "data/chroma_db")
        self.embeddings = get_embeddings()
        self._vector_store: Chroma | None = None

    def split_documents(self, docs: list[Document]) -> list[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        )
        chunks = splitter.split_documents(docs)
        for index, chunk in enumerate(chunks):
            source = chunk.metadata.get("source", "unknown")
            chunk.metadata["chunk_id"] = f"{source}:{index}"
        return chunks

    def build_index(self, docs: list[Document]) -> int:
        chunks = self.split_documents(docs)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            persist_directory=str(self.persist_dir),
        )
        return len(chunks)

    def load_index(self) -> None:
        self._vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_dir),
        )

    def retrieve(self, query: str, k: int | None = None) -> list[Evidence]:
        if self._vector_store is None:
            self.load_index()
        assert self._vector_store is not None
        limit = k or self.top_k
        docs_with_scores = self._vector_store.similarity_search_with_score(query, k=limit)
        evidence: list[Evidence] = []
        for doc, distance in docs_with_scores:
            metadata = dict(doc.metadata)
            score = 1.0 / (1.0 + max(float(distance), 0.0))
            evidence.append(
                Evidence(
                    id=metadata.get("chunk_id", metadata.get("source", "unknown")),
                    content=doc.page_content,
                    source=metadata.get("source", "unknown"),
                    score=round(float(score), 4),
                    metadata=metadata,
                )
            )
        return evidence

    @property
    def index_path(self) -> Path:
        return self.persist_dir
