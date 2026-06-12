"""PharmAssist Agent workflow."""

from __future__ import annotations

from src.core.config import config
from src.core.llm import LLMClient
from src.core.models import ChatResponse, CitationCheck, Evidence, RetrievalStrategy
from src.domain.citation_validator import validate_citations
from src.domain.compliance_checker import requires_human_review
from src.domain.risk import classify_risk
from src.rag import RAGEngine, SimpleReranker, decompose_question, hyde_rewrite


class PharmAssistAgent:
    """End-to-end GMP compliance assistant."""

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.rag = RAGEngine()
        self.reranker = SimpleReranker()
        self.default_strategy: RetrievalStrategy = config.get("agent", {}).get("default_strategy", "decompose")

    def run(self, question: str, strategy: RetrievalStrategy | None = None) -> ChatResponse:
        selected_strategy = strategy or self.default_strategy
        risk_level = classify_risk(question)
        evidence, sub_questions = self._retrieve(question, selected_strategy)

        rerank_top_k = int(config.get("rag", {}).get("rerank_top_k", 4))
        ranked_evidence = self.reranker.rerank(question, evidence, top_k=rerank_top_k)
        answer = self._generate_answer(question, ranked_evidence)
        citation_check = validate_citations(answer, ranked_evidence)
        review = requires_human_review(risk_level, citation_check)

        if not ranked_evidence:
            citation_check = CitationCheck(
                has_citation=False,
                grounded=False,
                notes=["No evidence found. The assistant refused to answer directly."],
            )
            answer = "当前知识库没有检索到足够证据支持回答。建议补充相关 GMP、药典或 SOP 文档后再判断。"
            review = True

        return ChatResponse(
            answer=answer,
            sources=ranked_evidence,
            sub_questions=sub_questions,
            strategy=selected_strategy,
            risk_level=risk_level,
            requires_human_review=review,
            citation_check=citation_check,
        )

    def _retrieve(self, question: str, strategy: RetrievalStrategy) -> tuple[list[Evidence], list[str]]:
        if strategy == "direct":
            return self.rag.retrieve(question), []
        if strategy == "hyde":
            rewritten = hyde_rewrite(self.llm, question)
            return self.rag.retrieve(rewritten), []
        if strategy == "decompose":
            sub_questions = decompose_question(self.llm, question)
            return self._retrieve_many(sub_questions), sub_questions
        if strategy == "hybrid":
            sub_questions = decompose_question(self.llm, question)
            queries = sub_questions + [hyde_rewrite(self.llm, item) for item in sub_questions]
            return self._retrieve_many(queries), sub_questions
        return self.rag.retrieve(question), []

    def _retrieve_many(self, queries: list[str]) -> list[Evidence]:
        seen: set[str] = set()
        combined: list[Evidence] = []
        per_query_k = max(2, int(config.get("rag", {}).get("top_k", 8)) // max(len(queries), 1))
        for query in queries:
            for item in self.rag.retrieve(query, k=per_query_k):
                if item.id not in seen:
                    seen.add(item.id)
                    combined.append(item)
        return combined

    def _generate_answer(self, question: str, evidence: list[Evidence]) -> str:
        if not evidence:
            return "当前知识库没有检索到足够证据支持回答。"

        evidence_text = "\n\n".join(
            f"[{index}] 来源：{item.source}\n{item.content}" for index, item in enumerate(evidence, start=1)
        )
        prompt = f"""你是制药企业 GMP 合规助手。请严格基于证据回答，不要编造法规编号。

问题：
{question}

证据：
{evidence_text}

要求：
- 用中文回答
- 每个关键判断都给出 [1] 这样的证据引用
- 如果证据不足，请明确说明需要人工复核
"""
        return self.llm.invoke(prompt).strip()
