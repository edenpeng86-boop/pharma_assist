"""HyDE query rewriting."""

from __future__ import annotations

from src.core.llm import LLMClient


HYDE_PROMPT = """你是 GMP 合规专家。请针对问题生成一段可能出现在规范或 SOP 中的假设性文本。
要求：正式、简洁、适合用于检索，不要编造具体法规编号。

问题：{question}
"""


def hyde_rewrite(llm: LLMClient, question: str) -> str:
    return llm.invoke(HYDE_PROMPT.format(question=question))
