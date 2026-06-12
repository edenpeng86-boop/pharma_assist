"""PharmAssist Agent workflow."""

from __future__ import annotations

import time

from src.core.config import config
from src.core.llm import LLMClient
from src.core.models import ChatResponse, CitationCheck, Evidence, LanguageCode, RetrievalStrategy, TimingMetrics, TraceStep
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

    def run(
        self,
        question: str,
        strategy: RetrievalStrategy | None = None,
        language: LanguageCode = "zh-CN",
    ) -> ChatResponse:
        total_start = time.perf_counter()
        trace_steps: list[TraceStep] = []
        timing = TimingMetrics()
        copy = _trace_copy(language)

        selected_strategy = strategy or self.default_strategy
        risk_level = classify_risk(question)
        trace_steps.append(
            TraceStep(
                title=copy["risk_title"],
                detail=copy["risk_detail"].format(risk=risk_level),
                status="warning" if risk_level == "high" else "done",
            )
        )

        retrieval_start = time.perf_counter()
        evidence, sub_questions = self._retrieve(question, selected_strategy)
        timing.retrieval_ms = _elapsed_ms(retrieval_start)
        trace_steps.append(
            TraceStep(
                title=copy["strategy_title"],
                detail=copy["strategy_detail"].format(strategy=selected_strategy, count=len(sub_questions)),
            )
        )
        trace_steps.append(
            TraceStep(
                title=copy["retrieval_title"],
                detail=copy["retrieval_detail"].format(count=len(evidence)),
                status="done" if evidence else "warning",
            )
        )

        rerank_start = time.perf_counter()
        rerank_top_k = int(config.get("rag", {}).get("rerank_top_k", 4))
        ranked_evidence = self.reranker.rerank(question, evidence, top_k=rerank_top_k)
        timing.rerank_ms = _elapsed_ms(rerank_start)
        trace_steps.append(
            TraceStep(
                title=copy["rerank_title"],
                detail=copy["rerank_detail"].format(count=len(ranked_evidence)),
                status="done" if ranked_evidence else "warning",
            )
        )

        generation_start = time.perf_counter()
        answer = self._generate_answer(question, ranked_evidence, language)
        timing.generation_ms = _elapsed_ms(generation_start)

        validation_start = time.perf_counter()
        citation_check = validate_citations(answer, ranked_evidence)
        review = requires_human_review(risk_level, citation_check)
        timing.validation_ms = _elapsed_ms(validation_start)
        trace_steps.append(
            TraceStep(
                title=copy["citation_title"],
                detail=copy["citation_ok"] if citation_check.grounded else copy["citation_warning"],
                status="done" if citation_check.grounded else "warning",
            )
        )
        trace_steps.append(
            TraceStep(
                title=copy["review_title"],
                detail=copy["review_yes"] if review else copy["review_no"],
                status="warning" if review else "done",
            )
        )

        if not ranked_evidence:
            citation_check = CitationCheck(
                has_citation=False,
                grounded=False,
                notes=["No evidence found. The assistant refused to answer directly."],
            )
            answer = copy["no_evidence_answer"]
            review = True
            trace_steps.append(
                TraceStep(
                    title=copy["no_evidence_title"],
                    detail=copy["no_evidence_detail"],
                    status="warning",
                )
            )

        timing.total_ms = _elapsed_ms(total_start)

        return ChatResponse(
            answer=answer,
            sources=ranked_evidence,
            sub_questions=sub_questions,
            strategy=selected_strategy,
            risk_level=risk_level,
            requires_human_review=review,
            citation_check=citation_check,
            trace_steps=trace_steps,
            timing=timing,
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

    def _generate_answer(self, question: str, evidence: list[Evidence], language: LanguageCode) -> str:
        if not evidence:
            return _trace_copy(language)["no_evidence_answer"]

        evidence_text = "\n\n".join(
            f"[{index}] 来源：{item.source}\n{item.content}" for index, item in enumerate(evidence, start=1)
        )
        language_name = {
            "zh-CN": "Simplified Chinese",
            "zh-TW": "Traditional Chinese",
            "en": "English",
            "ja": "Japanese",
            "de": "German",
        }.get(language, "Simplified Chinese")
        prompt = f"""你是制药企业 GMP 合规助手。请严格基于证据回答，不要编造法规编号。

问题：
{question}

证据：
{evidence_text}

要求：
- 用 {language_name} 回答
- 每个关键判断都给出 [1] 这样的证据引用
- 如果证据不足，请明确说明需要人工复核
"""
        return self.llm.invoke(prompt).strip()


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


TRACE_COPY = {
    "zh-CN": {
        "risk_title": "识别合规风险",
        "risk_detail": "问题被标记为 {risk} 风险。",
        "strategy_title": "选择检索策略",
        "strategy_detail": "使用 {strategy} 策略，拆解出 {count} 个子问题。",
        "retrieval_title": "检索知识库证据",
        "retrieval_detail": "从知识库召回 {count} 条候选证据。",
        "rerank_title": "证据重排序",
        "rerank_detail": "保留最相关的 {count} 条证据用于回答生成。",
        "citation_title": "引用与证据校验",
        "citation_ok": "回答包含有效证据引用。",
        "citation_warning": "回答缺少有效证据引用，建议复核。",
        "review_title": "人工复核判断",
        "review_yes": "建议人工复核。",
        "review_no": "当前回答未触发强制人工复核。",
        "no_evidence_title": "证据不足处理",
        "no_evidence_detail": "未检索到可用证据，系统拒绝直接给出合规判断。",
        "no_evidence_answer": "当前知识库没有检索到足够证据支持回答。建议补充相关 GMP、药典或 SOP 文档后再判断。",
    },
    "en": {
        "risk_title": "Classify compliance risk",
        "risk_detail": "The question is marked as {risk} risk.",
        "strategy_title": "Select retrieval strategy",
        "strategy_detail": "Used {strategy} strategy and produced {count} sub-questions.",
        "retrieval_title": "Retrieve knowledge evidence",
        "retrieval_detail": "Retrieved {count} candidate evidence chunks.",
        "rerank_title": "Rerank evidence",
        "rerank_detail": "Kept the top {count} evidence chunks for answer generation.",
        "citation_title": "Validate citations",
        "citation_ok": "The answer contains valid evidence citations.",
        "citation_warning": "The answer lacks valid evidence citations and should be reviewed.",
        "review_title": "Human review decision",
        "review_yes": "Human review is recommended.",
        "review_no": "No mandatory human review was triggered.",
        "no_evidence_title": "Insufficient evidence handling",
        "no_evidence_detail": "No usable evidence was retrieved, so the system refused a direct compliance judgment.",
        "no_evidence_answer": "The knowledge base did not provide enough evidence to answer. Please add relevant GMP, pharmacopeia, or SOP documents before making a judgment.",
    },
    "zh-TW": {
        "risk_title": "識別合規風險",
        "risk_detail": "問題被標記為 {risk} 風險。",
        "strategy_title": "選擇檢索策略",
        "strategy_detail": "使用 {strategy} 策略，拆解出 {count} 個子問題。",
        "retrieval_title": "檢索知識庫證據",
        "retrieval_detail": "從知識庫召回 {count} 條候選證據。",
        "rerank_title": "證據重排序",
        "rerank_detail": "保留最相關的 {count} 條證據用於回答生成。",
        "citation_title": "引用與證據校驗",
        "citation_ok": "回答包含有效證據引用。",
        "citation_warning": "回答缺少有效證據引用，建議覆核。",
        "review_title": "人工覆核判斷",
        "review_yes": "建議人工覆核。",
        "review_no": "目前回答未觸發強制人工覆核。",
        "no_evidence_title": "證據不足處理",
        "no_evidence_detail": "未檢索到可用證據，系統拒絕直接給出合規判斷。",
        "no_evidence_answer": "目前知識庫沒有檢索到足夠證據支持回答。建議補充相關 GMP、藥典或 SOP 文件後再判斷。",
    },
    "ja": {
        "risk_title": "コンプライアンスリスク分類",
        "risk_detail": "質問は {risk} リスクとして分類されました。",
        "strategy_title": "検索戦略の選択",
        "strategy_detail": "{strategy} 戦略を使用し、{count} 個のサブ質問を作成しました。",
        "retrieval_title": "知識ベース証拠の検索",
        "retrieval_detail": "{count} 件の候補証拠を取得しました。",
        "rerank_title": "証拠の再ランキング",
        "rerank_detail": "回答生成用に上位 {count} 件の証拠を保持しました。",
        "citation_title": "引用と証拠の検証",
        "citation_ok": "回答には有効な証拠引用があります。",
        "citation_warning": "回答に有効な証拠引用が不足しているためレビューが推奨されます。",
        "review_title": "人手レビュー判断",
        "review_yes": "人手レビューを推奨します。",
        "review_no": "強制的な人手レビューは triggered されていません。",
        "no_evidence_title": "証拠不足への対応",
        "no_evidence_detail": "利用可能な証拠が検索されなかったため、直接的なコンプライアンス判断を拒否しました。",
        "no_evidence_answer": "知識ベースには回答を支える十分な証拠がありません。関連する GMP、薬局方、SOP 文書を追加してから判断してください。",
    },
    "de": {
        "risk_title": "Compliance-Risiko klassifizieren",
        "risk_detail": "Die Frage wurde als {risk}-Risiko markiert.",
        "strategy_title": "Retrieval-Strategie wählen",
        "strategy_detail": "Strategie {strategy} verwendet und {count} Teilfragen erstellt.",
        "retrieval_title": "Evidenz aus Wissensbasis abrufen",
        "retrieval_detail": "{count} Kandidaten-Evidenzen wurden abgerufen.",
        "rerank_title": "Evidenz neu sortieren",
        "rerank_detail": "Die relevantesten {count} Evidenzen wurden für die Antwort behalten.",
        "citation_title": "Zitationen und Evidenz prüfen",
        "citation_ok": "Die Antwort enthält gültige Evidenzzitationen.",
        "citation_warning": "Der Antwort fehlen gültige Evidenzzitationen; Review empfohlen.",
        "review_title": "Human-Review-Entscheidung",
        "review_yes": "Human Review wird empfohlen.",
        "review_no": "Kein verpflichtender Human Review ausgelöst.",
        "no_evidence_title": "Umgang mit unzureichender Evidenz",
        "no_evidence_detail": "Keine nutzbare Evidenz gefunden; das System verweigert eine direkte Compliance-Bewertung.",
        "no_evidence_answer": "Die Wissensbasis enthält nicht genügend Evidenz für eine Antwort. Bitte relevante GMP-, Pharmakopöe- oder SOP-Dokumente ergänzen.",
    },
}


def _trace_copy(language: LanguageCode) -> dict[str, str]:
    return TRACE_COPY.get(language, TRACE_COPY["zh-CN"])
