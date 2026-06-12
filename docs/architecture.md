# PharmAssist Architecture

PharmAssist is designed as a regulated-domain RAG Agent instead of a generic chatbot.

## Request Flow

1. API receives a user question.
2. Agent classifies risk and retrieval strategy.
3. RAG engine retrieves metadata-rich chunks.
4. Reranker selects stronger evidence.
5. LLM or offline generator creates an evidence-grounded answer.
6. Citation validator checks source references.
7. Response includes answer, evidence, risk level, and review flags.

## Why This Matters

GMP/SOP questions are high-stakes. A useful assistant must show where an answer came from, refuse unsupported answers, and flag risky decisions for human review.
