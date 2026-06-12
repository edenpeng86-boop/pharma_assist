"""LLM wrapper with deterministic offline fallback."""

from __future__ import annotations

from typing import Iterable

from langchain_openai import ChatOpenAI

from src.core.config import config


class LLMClient:
    """Small OpenAI-compatible chat client.

    When no API key is configured, this class returns deterministic demo answers so
    the project remains runnable in interviews and CI.
    """

    def __init__(self) -> None:
        cfg = config["llm"]
        self.offline = cfg.get("offline_fallback", True) and not cfg.get("api_key")
        self.model = None
        if not self.offline:
            self.model = ChatOpenAI(
                model=cfg.get("model", "gpt-4o-mini"),
                api_key=cfg.get("api_key"),
                base_url=cfg.get("base_url"),
                temperature=cfg.get("temperature", 0),
                max_tokens=cfg.get("max_tokens", 1200),
            )

    def invoke(self, prompt: str) -> str:
        if self.offline:
            return self._offline_answer(prompt)
        assert self.model is not None
        return self.model.invoke(prompt).content

    def stream(self, prompt: str) -> Iterable[str]:
        if self.offline:
            yield self._offline_answer(prompt)
            return
        assert self.model is not None
        for chunk in self.model.stream(prompt):
            yield chunk.content

    def _offline_answer(self, prompt: str) -> str:
        if "JSON 数组" in prompt:
            return '["相关 GMP 要求是什么？", "需要哪些记录或控制措施？"]'
        if "风险等级" in prompt:
            return "medium"
        return (
            "根据已检索到的 GMP/SOP 证据，相关操作应结合产品风险、工艺暴露程度、"
            "污染和交叉污染控制要求确定控制措施。关键决策应保留完整记录，涉及偏差、"
            "放行或无菌控制的问题应由质量负责人复核。[1]"
        )
