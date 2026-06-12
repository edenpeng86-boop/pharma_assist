"""Question decomposition."""

from __future__ import annotations

import json

from src.core.llm import LLMClient


DECOMPOSE_PROMPT = """请将复杂 GMP/SOP 问题拆成 2-4 个可检索子问题。
只输出 JSON 数组。

问题：{question}
"""


def decompose_question(llm: LLMClient, question: str) -> list[str]:
    raw = llm.invoke(DECOMPOSE_PROMPT.format(question=question))
    try:
        start = raw.index("[")
        end = raw.rindex("]") + 1
        parsed = json.loads(raw[start:end])
        return [str(item) for item in parsed if str(item).strip()] or [question]
    except (ValueError, json.JSONDecodeError):
        return [question]
