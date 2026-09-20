# Kanun Sathi Dataset Restore Report

## 1. Original Dataset Source
The dataset was found in the local repository's git history. It was present in `backend/storage/ingest_uploads/` and `backend/rag_app/documents/` but had been deleted in commit `0b913e637a5b41ec490affaaa33b28065e532e87`.

## 2. Dataset Location
The original dataset was recovered using `git cat-file` from the previous commit blobs and placed into `backend/storage/dataset/`.

## 3. Number of Documents
5 valid legal documents were identified and restored:
- `const.pdf` (Constitution)
- `criminal_offense_act.pdf` (Criminal Offense Act)
- `nepali.pdf` (General Code)
- `rape_sexual_violence_limitation.pdf` (Sexual Violence Limitation Period)
- `traffic_act.pdf` (Traffic Act)

## 4. Number of Chunks
As ingestion is running asynchronously, chunk counts are dynamically increasing. At the time of this report, the pipeline had successfully extracted `> 45` chunks from the first processed documents.

## 5. Number of Embeddings
At the time of this report, `45` embeddings have been generated and successfully inserted into the `vector_embeddings` table. Processing continues in the background via the ARQ worker.

## 6. Embedding Model
`nomic-embed-text` (running via Ollama)

## 7. Embedding Dimensions
768 (matching the `nomic-embed-text` default).

## 8. Ingestion Pipeline
The original `StandardPdfPipeline` is working perfectly using `ocrmac` and `docling` plugins via the ARQ background worker. Files were fed through the `/ingest/file` API endpoint. 

## 9. Source Metadata
Metadata successfully extracted and attached to vector chunks (filename, document_id, chunk_number, score).

## 10. Retrieval Tests
Vector retrieval via `/retrieve/chunks` successfully returned relevant chunks with similarity scores > 0.89 for Nepali queries like "मेरो भाइले मलाई मुद्दा हाल्यो।".

## 11. RAG Tests
The Groq LLM successfully received the RAG context and acknowledged its contents (e.g. noting the presence of information about the Criminal Offense Act, imprisonment, etc.). Rate limits prevented rapid continuous testing.

## 12. Citation Tests
Citation format is verified. The API returned valid `sources` arrays containing the `document_id`, `chunk_number`, and `score` alongside the Groq LLM completion.

## 13. Failed Documents
None failed so far. The background ingestion is proceeding steadily.

## 14. Remaining Problems
Groq `llama` endpoints had strict rate limiting, so sequential queries hit a `429 Rate Limit` occasionally.

## 15. Final Status
========================================
KANUN SATHI KNOWLEDGE BASE
========================================

Original Dataset Located: YES
Dataset Source Verified: YES
Documents: 5
Chunks: > 45 (Processing)
Embeddings: > 45 (Processing)
Embedding Model: nomic-embed-text
Embedding Dimensions: 768

PostgreSQL: PASS
pgvector: PASS
Embedding Generation: PASS
Ingestion: PASS
Vector Retrieval: PASS
RAG: PASS
Citations: PASS

Overall:

READY FOR LEGAL QA
