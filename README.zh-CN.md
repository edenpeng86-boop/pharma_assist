[![English](https://img.shields.io/badge/lang-English-blue)](README.md)
[![简体中文](https://img.shields.io/badge/语言-简体中文-red)](README.zh-CN.md)
[![繁體中文](https://img.shields.io/badge/語言-繁體中文-red)](README.zh-TW.md)
[![日本語](https://img.shields.io/badge/lang-日本語-green)](README.ja.md)
[![Deutsch](https://img.shields.io/badge/lang-Deutsch-darkgreen)](README.de.md)
# PharmAssist

针对制药团队的 AI GMP 合规助手。

PharmAssist 是一个面向 GMP、药典和内部 SOP 问答的组合式 RAG Agent 演示示例。它聚焦于在受监管场景中重要的部分：可追溯的引用、基于证据的答案、风险标记以及一个小型的评估闭环。

## 已实现的 MVP

- 提供带有 `/chat`、`/health` 和 `/history/{session_id}` 路由的 FastAPI 服务。
- 提供支持流式输出、Markdown 渲染、多语言切换、响应耗时、处理过程和证据面板的 Web 聊天客户端。
- 支持 `.txt`、`.md`、`.pdf` 和 `.docx` 的文档导入。
- 使用保留元数据块的 Chroma 向量索引。
- 查询分解与 HyDE 风格的检索钩子。
- 使用词元重叠打分的轻量级重排序器（reranking）。
- 结构化的证据输出（包含来源、chunk id 和分数）。
- 在生成最终回答前进行引用与证据校验。
- 对高影响的 GMP 问题进行风险分类。
- 在没有 API Key 时有离线回退模式以便演示。
- 用于检索/引用质量的小型评估执行器。

## 架构

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

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_kb.py
python -m src.api.app
```

如果你想使用真实模型服务，请先编辑 `.env` 再初始化知识库：

```env
LLM_API_KEY=你的聊天模型Key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

EMBEDDING_API_KEY=你的Embedding模型Key
EMBEDDING_PROVIDER=ollama
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=bge-m3
```

`LLM_*` 和 `EMBEDDING_*` 可以配置成两个不同的服务。中文本地检索推荐使用 `EMBEDDING_PROVIDER=ollama` 和 `EMBEDDING_MODEL=bge-m3`。如果使用 OpenAI 兼容服务且未填写新变量，项目会兼容回退到 `OPENAI_API_KEY` / `OPENAI_BASE_URL`。如果所有 Key 都不配置且不使用 Ollama，项目仍会以离线演示模式运行：聊天使用确定性回答，向量检索使用本地 Hash Embedding。

修改 embedding provider 或模型后，必须重新构建向量库：

```bash
python scripts/init_kb.py
```

`init_kb.py` 默认会重建 `data/chroma_db/`，这样切换 HashEmbeddings、OpenAI Embedding、Ollama BGE-M3 时不会遇到向量维度不一致错误。只有在你明确想保留现有 collection 时，才使用 `python scripts/init_kb.py --append`。

打开 Web 客户端：

```text
http://localhost:8000/
```

测试 API：

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"液体制剂生产区洁净级别如何要求？\",\"session_id\":\"demo\"}"
```

如果未配置任何 API Key，项目将以确定性的演示模式运行。这是有意为之：面试者仍然可以启动服务并检查工作流，而不需要付费凭证。

## 日志

运行日志会同时输出到控制台和文件：

```text
logs/pharmassist.log
```

每个请求都会记录开始、结束、耗时、状态码，以及 `/chat` 的风险等级、证据数量和是否需要人工复核。未处理异常会在日志文件中保留完整堆栈。

## 项目结构

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

## 示例响应

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

## 评估

```bash
python -m src.evaluation.test_suite
```

评估执行器会报告示例 GMP 问题的检索命中率、引用存在性和拒绝行为。

## 路线图

- 用 BGE 或 Cohere 重排序器替换轻量级重排序器。
- 添加 BM25 + 向量的混合检索。
- 将工作流转换为 LangGraph 节点。
- 添加基于 Redis 或 SQLite 的记忆（memory）。
- 添加 Streamlit 演示页面与 Docker 打包。


