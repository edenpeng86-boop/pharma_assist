[![English](https://img.shields.io/badge/lang-English-blue)](README.md)
[![简体中文](https://img.shields.io/badge/语言-简体中文-red)](README.zh-CN.md)
[![繁體中文](https://img.shields.io/badge/語言-繁體中文-red)](README.zh-TW.md)
[![日本語](https://img.shields.io/badge/lang-日本語-green)](README.ja.md)
[![Deutsch](https://img.shields.io/badge/lang-Deutsch-darkgreen)](README.de.md)
# PharmAssist

製薬チーム向けの AI ベースの GMP コンプライアンス支援ツール。

PharmAssist は、GMP、薬局方、および社内 SOP に関する質問応答のためのポートフォリオ品質の RAG エージェントのデモです。規制対応が必要な場面で重要となる点、すなわち参照の追跡可能性、証拠に基づく回答、リスクフラグ、および小規模な評価ループに重点を置いています。

## 実装済みの MVP

- `/chat`、`/health`、`/history/{session_id}` エンドポイントを持つ FastAPI サービス。
- `.txt`、`.md`、`.pdf`、`.docx` のドキュメント取り込み。
- メタデータを保持するチャンクを用いた Chroma ベクトルインデックス。
- クエリ分解と HyDE 風の検索フック。
- トークン重複を用いた軽量ランカー（リランキング）。
- ソース、チャンク ID、スコアを含む構造化された証拠出力。
- 最終応答前の引用および証拠のチェック。
- 重要度の高い GMP 質問に対するリスク分類。
- API キーがない場合のデターミニスティックなフォールバックモード（デモ用）。
- 検索／引用品質のための小さな評価ランナー。

## アーキテクチャ

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

## クイックスタート

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_kb.py
python -m src.api.app
```

API のテスト：

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"液体製剤の製造エリアの清浄度要件はどうなっていますか？\",\"session_id\":\"demo\"}"
```

`OPENAI_API_KEY` が設定されていない場合、プロジェクトはデターミニスティックなデモモードで動作します。これは意図的な動作で、面接者は有料の認証情報がなくてもサービスを起動してワークフローを確認できます。

## プロジェクト構成

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

## 例示レスポンス

```json
{
  "answer": "取得した GMP/SOP の証拠に基づき、液体製剤の製造エリアは汚染リスク、プロセスの暴露度、および製品特性を考慮して清浄度を決定する必要があります。無菌または高汚染リスクの工程が含まれる場合は、より厳格な清浄管理を実施し、環境モニタリング記録を保持するべきです。[1]",
  "sources": [
	{
	  "id": "gmp_demo.txt:0",
	  "source": "gmp_demo.txt",
	  "content": "薬品の製造は汚染および交差汚染を防止する対策を確立するべきである...",
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

## 評価

```bash
python -m src.evaluation.test_suite
```

評価ランナーはサンプル GMP 質問に対する検索ヒット率、引用の有無、および拒否動作を報告します。

## ロードマップ

- 軽量リランカーを BGE または Cohere のリランカーに置き換える。
- BM25 とベクトルのハイブリッド検索を追加する。
- ワークフローを LangGraph のノードに変換する。
- Redis または SQLite ベースのメモリを追加する。
- Streamlit デモページと Docker パッケージを追加する。


