[![English](https://img.shields.io/badge/lang-English-blue)](README.md)
[![简体中文](https://img.shields.io/badge/语言-简体中文-red)](README.zh-CN.md)
[![繁體中文](https://img.shields.io/badge/語言-繁體中文-red)](README.zh-TW.md)
[![日本語](https://img.shields.io/badge/lang-日本語-green)](README.ja.md)
[![Deutsch](https://img.shields.io/badge/lang-Deutsch-darkgreen)](README.de.md)
# PharmAssist

AI GMP compliance assistant for pharmaceutical teams.

PharmAssist is a portfolio-grade RAG Agent demo for GMP, pharmacopeia, and internal SOP question answering. It focuses on the parts that matter in regulated scenarios: traceable citations, evidence-grounded answers, risk flags, and a small evaluation loop.

## Implemented MVP

- FastAPI service with `/chat`, `/health`, and `/history/{session_id}`.
- Web chat client with streaming responses, Markdown rendering, language switcher, timing metrics, process trace, and evidence panel.
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

Configure `.env` before building the knowledge base if you want to use real model services:

```env
LLM_API_KEY=your-chat-model-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

EMBEDDING_API_KEY=your-embedding-model-key
EMBEDDING_PROVIDER=ollama
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=bge-m3
```

`LLM_*` and `EMBEDDING_*` can point to different providers. For local Chinese retrieval, `EMBEDDING_PROVIDER=ollama` with `EMBEDDING_MODEL=bge-m3` is recommended. If the provider is OpenAI-compatible and the new variables are not set, the app falls back to `OPENAI_API_KEY` / `OPENAI_BASE_URL`. If no keys are configured and the provider is not Ollama, PharmAssist still runs in offline demo mode with deterministic chat responses and local hash embeddings.

After changing the embedding provider or model, rebuild the vector database:

```bash
python scripts/init_kb.py
```

`init_kb.py` rebuilds `data/chroma_db/` by default, which avoids dimension mismatch errors when switching between HashEmbeddings, OpenAI embeddings, and Ollama BGE-M3. Use `python scripts/init_kb.py --append` only when you intentionally want to keep the existing collection.

Open the web client:

```text
http://localhost:8000/
```

Test the API:

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"液体制剂生产区洁净级别如何要求？\",\"session_id\":\"demo\"}"
```

If no API key is configured, the project runs in deterministic demo mode. This is intentional: interviewers can still start the service and inspect the workflow without paid credentials.

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

## Logs

Runtime logs are printed to the console and written to:

```text
logs/pharmassist.log
```

Each request includes start/end lines, latency, status code, and chat-level risk/source metadata. Unhandled errors include stack traces in the log file.

## Roadmap

- Replace lightweight reranker with BGE or Cohere reranker.
- Add BM25 + vector hybrid retrieval.
- Convert the workflow to LangGraph nodes.
- Add Redis or SQLite-backed memory.
- Add Streamlit demo page and Docker packaging.
