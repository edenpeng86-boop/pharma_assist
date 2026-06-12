# PharmAssist

AI GMP compliance assistant for pharmaceutical teams.

PharmAssist is a portfolio-grade RAG Agent demo for GMP, pharmacopeia, and internal SOP question answering. It focuses on the parts that matter in regulated scenarios: traceable citations, evidence-grounded answers, risk flags, and a small evaluation loop.

## Implemented MVP

- FastAPI service with `/chat`, `/health`, and `/history/{session_id}`.
- Document ingestion for `.txt`, `.md`, `.pdf`, and `.docx`.
- Chroma vector index with metadata-preserving chunks.
- Query decomposition and HyDE-style retrieval hooks.
- Lightweight reranking with token overlap scoring.
- Structured evidence output with source, chunk id, and score.
- Citation and evidence checks before final response.
- Risk classification for high-impact GMP questions.
- Offline fallback mode for demos without an API key.
- Tiny evaluation runner for retrieval/citation quality.

## Architecture

```text
User / API Client
      |
      v
FastAPI Routes
      |
      v
PharmAssistAgent
  |-- classify risk
  |-- choose retrieval strategy
  |-- retrieve evidence
  |-- rerank evidence
  |-- generate grounded answer
  |-- validate citations
      |
      v
RAGEngine -> Chroma -> Knowledge Base
```

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_kb.py
python -m src.api.app
```

Test the API:

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"液体制剂生产区洁净级别如何要求？\",\"session_id\":\"demo\"}"
```

If `OPENAI_API_KEY` is not configured, the project runs in deterministic demo mode. This is intentional: interviewers can still start the service and inspect the workflow without paid credentials.

## Project Structure

```text
pharmcodex/
├── config/
│   └── config.yaml
├── data/
│   ├── knowledge/
│   └── eval/
├── docs/
│   └── architecture.md
├── scripts/
│   └── init_kb.py
├── src/
│   ├── agent/
│   ├── api/
│   ├── core/
│   ├── domain/
│   ├── evaluation/
│   └── rag/
└── tests/
```

## Example Response

```json
{
  "answer": "根据已检索到的 GMP/SOP 证据，液体制剂生产区应结合污染风险、工艺暴露程度和产品特性确定洁净级别。涉及无菌或高污染风险步骤时，应采用更严格的洁净控制，并保留环境监测记录。[1]",
  "sources": [
    {
      "id": "gmp_demo.txt:0",
      "source": "gmp_demo.txt",
      "content": "药品生产应当建立防止污染和交叉污染的措施...",
      "score": 0.72
    }
  ],
  "risk_level": "medium",
  "citation_check": {
    "has_citation": true,
    "grounded": true
  }
}
```

## Evaluation

```bash
python -m src.evaluation.test_suite
```

The evaluation runner reports retrieval hit rate, citation presence, and refusal behavior for sample GMP questions.

## Roadmap

- Replace lightweight reranker with BGE or Cohere reranker.
- Add BM25 + vector hybrid retrieval.
- Convert the workflow to LangGraph nodes.
- Add Redis or SQLite-backed memory.
- Add Streamlit demo page and Docker packaging.
