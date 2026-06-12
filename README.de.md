[![English](https://img.shields.io/badge/lang-English-blue)](README.md)
[![简体中文](https://img.shields.io/badge/语言-简体中文-red)](README.zh-CN.md)
[![繁體中文](https://img.shields.io/badge/語言-繁體中文-red)](README.zh-TW.md)
[![日本語](https://img.shields.io/badge/lang-日本語-green)](README.ja.md)
[![Deutsch](https://img.shields.io/badge/lang-Deutsch-darkgreen)](README.de.md)
# PharmAssist

KI-gestützte GMP-Compliance-Hilfe für Pharma-Teams.

PharmAssist ist eine RAG-Agent-Demo in Portfolio-Qualität für Fragen zu GMP, Pharmakopöe und internen SOPs. Der Fokus liegt auf den in regulierten Szenarien wichtigen Punkten: nachvollziehbare Zitationen, evidenzbasierte Antworten, Risikohinweise und eine kleine Evaluationsschleife.

## Implementiertes MVP

- FastAPI-Service mit den Endpunkten `/chat`, `/health` und `/history/{session_id}`.
- Web-Chat-Client mit Streaming-Antworten, Markdown-Rendering, Sprachumschaltung, Antwortzeit, Prozessablauf und Evidenzpanel.
- Dokumenteneinlese-Funktion für `.txt`, `.md`, `.pdf` und `.docx`.
- Chroma-Vektorindex mit metadaten-erhaltenden Chunks.
- Query-Decomposition und HyDE-ähnliche Retrieval-Hooks.
- Leichtgewichtige Re-Rankung basierend auf Token-Overlap-Scoring.
- Strukturierte Evidenzausgabe mit Quelle, Chunk-ID und Score.
- Zitations- und Evidenzprüfungen vor der finalen Antwort.
- Risikoklassifikation für GMP-Fragen mit hoher Auswirkung.
- Offline-Fallback-Modus für Demos ohne API-Key.
- Kleiner Evaluations-Runner zur Bewertung von Retrieval/Zitation.

## Architektur

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

## Schnellstart

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_kb.py
python -m src.api.app
```

Wenn du echte Modelldienste verwenden möchtest, bearbeite `.env`, bevor du die Knowledge Base initialisierst:

```env
LLM_API_KEY=your-chat-model-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

EMBEDDING_API_KEY=your-embedding-model-key
EMBEDDING_PROVIDER=ollama
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=bge-m3
```

`LLM_*` und `EMBEDDING_*` können auf unterschiedliche Anbieter zeigen. Für lokale chinesische Retrieval-Qualität wird `EMBEDDING_PROVIDER=ollama` mit `EMBEDDING_MODEL=bge-m3` empfohlen. Bei OpenAI-kompatiblen Anbietern fällt die App aus Kompatibilitätsgründen auf `OPENAI_API_KEY` / `OPENAI_BASE_URL` zurück, wenn die neuen Variablen nicht gesetzt sind. Ohne konfigurierte Keys und ohne Ollama läuft PharmAssist weiterhin im Offline-Demo-Modus mit deterministischen Chat-Antworten und lokalen Hash Embeddings.

Nach Änderung des Embedding-Providers oder Modells muss die Vektordatenbank neu aufgebaut werden:

```bash
python scripts/init_kb.py
```

`init_kb.py` baut `data/chroma_db/` standardmäßig neu auf. Dadurch werden Dimensionsfehler vermieden, wenn zwischen HashEmbeddings, OpenAI Embeddings und Ollama BGE-M3 gewechselt wird. Verwende `python scripts/init_kb.py --append` nur, wenn die bestehende Collection bewusst erhalten bleiben soll.

Web-Client öffnen:

```text
http://localhost:8000/
```

API testen:

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"液体制剂生产区洁净级别如何要求？\",\"session_id\":\"demo\"}"
```

Wenn kein API-Key konfiguriert ist, läuft das Projekt im deterministischen Demo-Modus. Das ist beabsichtigt: Interviewer können den Dienst starten und den Workflow prüfen, auch ohne bezahlte Zugangsdaten.

## Logs

Laufzeitlogs werden in der Konsole und in folgender Datei ausgegeben:

```text
logs/pharmassist.log
```

Jede Anfrage protokolliert Start, Ende, Latenz, Statuscode sowie Risiko-Level, Anzahl der Evidenzen und Human-Review-Status für `/chat`. Unbehandelte Fehler enthalten Stacktraces in der Logdatei.

## Projektstruktur

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

## Beispielantwort

```json
{
  "answer": "Basierend auf den gefundenen GMP/SOP-Evidenzen sollte die Reinraumklasse für die Herstellung flüssiger Darreichungsformen unter Berücksichtigung des Kontaminationsrisikos, des Expositionsgrades im Prozess und der Produkteigenschaften festgelegt werden. Bei aseptischen oder hoch kontaminationsgefährdeten Schritten sollten strengere Reinigungs- und Kontrollmaßnahmen angewendet und Umgebungsüberwachungsaufzeichnungen geführt werden.[1]",
  "sources": [
	{
	  "id": "gmp_demo.txt:0",
	  "source": "gmp_demo.txt",
	  "content": "Die Arzneimittelherstellung sollte Maßnahmen zur Verhinderung von Kontamination und Kreuzkontamination etablieren...",
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

Der Evaluations-Runner berichtet Trefferquote beim Retrieval, Vorhandensein von Zitaten und Verweigerungsverhalten für Beispiel-GMP-Fragen.

## Roadmap

- Ersetze den leichtgewichtigen Re-Ranker durch BGE- oder Cohere-Re-Ranker.
- Füge BM25 + Vektor-Hybrid-Retrieval hinzu.
- Konvertiere den Workflow in LangGraph-Nodes.
- Füge Redis- oder SQLite-basierten Speicher hinzu.
- Füge eine Streamlit-Demo-Seite und Docker-Pakete hinzu.


