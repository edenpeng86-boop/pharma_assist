[![English](https://img.shields.io/badge/lang-English-blue)](README.md)
[![简体中文](https://img.shields.io/badge/语言-简体中文-red)](README.zh-CN.md)
[![繁體中文](https://img.shields.io/badge/語言-繁體中文-red)](README.zh-TW.md)
[![日本語](https://img.shields.io/badge/lang-日本語-green)](README.ja.md)
[![Deutsch](https://img.shields.io/badge/lang-Deutsch-darkgreen)](README.de.md)
# PharmAssist

針對製藥團隊的 AI GMP 合規助理。

PharmAssist 是一個面向 GMP、藥典與內部 SOP 問答的組合式 RAG Agent 範例。它專注於受監管場景中重要的部分：可追溯的引用、以證據為基礎的答案、風險標記以及一個小型的評估迴路。

## 已實作的 MVP

- 提供含 `/chat`、`/health` 與 `/history/{session_id}` 的 FastAPI 服務。
- 支援 `.txt`、`.md`、`.pdf` 與 `.docx` 的文件匯入。
- 使用保留 metadata 的 Chroma 向量索引與分片。
- 查詢分解與 HyDE 風格的檢索鉤子。
- 使用詞元重疊計分的輕量級重排序（reranking）。
- 結構化的證據輸出（包含來源、chunk id 與分數）。
- 在生成最終回答前執行引用與證據檢查。
- 對高影響的 GMP 問題進行風險分類。
- 當沒有 API Key 時備有離線回退模式以供示範。
- 小型的評估執行器，用於檢索/引用品質評估。

## 架構

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

## 快速開始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_kb.py
python -m src.api.app
```

測試 API：

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"液體製劑生產區潔淨等級如何要求？\",\"session_id\":\"demo\"}"
```

若未設定 `OPENAI_API_KEY`，專案會以確定性的示範模式執行。這是刻意為之：面試者仍可啟動服務並檢視工作流程，而不需付費憑證。

## 專案結構

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

## 範例回應

```json
{
  "answer": "根據已檢索到的 GMP/SOP 證據，液體製劑生產區應結合污染風險、製程暴露程度與產品特性來決定潔淨等級。涉及無菌或高污染風險步驟時，應採用更嚴格的潔淨管控，並保留環境監測記錄。[1]",
  "sources": [
	{
	  "id": "gmp_demo.txt:0",
	  "source": "gmp_demo.txt",
	  "content": "藥品生產應當建立防止污染和交叉污染的措施...",
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

## 評估

```bash
python -m src.evaluation.test_suite
```

評估執行器會回報示例 GMP 問題的檢索命中率、引用存在性與拒絕行為。

## 路線圖

- 以 BGE 或 Cohere 重排序器替代輕量級重排序器。
- 新增 BM25 + 向量混合檢索。
- 將工作流程轉換為 LangGraph 節點。
- 新增基於 Redis 或 SQLite 的記憶機制。
- 新增 Streamlit 範例頁面與 Docker 打包。


