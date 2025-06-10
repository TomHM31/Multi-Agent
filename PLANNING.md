<!-- PLANNING.md -->

# Phase 0 Planning

## 1. Project Overview

- **Goal:** Prepare and validate all data sources so that our Local LLM (hosted via Ollama on the NVIDIA RTX 6000) can support Retrieval-Augmented Generation (RAG) for invoice processing.
- **Scope:**
  - **Agents 1–2:** Ingestion (SQL tables, emails, DOCX, PDF) → Preprocessing (text extraction via PyMuPDF/pdfplumber + optional OCR) :contentReference[oaicite:0]{index=0}
  - **Agents 3–4:** Vendor Routing & Core Extraction powered by RAG over OpenSearch and local LLM.

## 2. Data Inventory & Sources

- **SQL Tables (e.g. `workflow_steps`, `policy_table`)**
- **Outlook Emails** (`.eml`/`.msg`)
- **PDF Documents** (policy manuals, SOPs, freight invoices)
- **DOCX Files** (guides, mapping templates)
- **“Golden Set”** – 20 representative freight invoices with manually validated JSON :contentReference[oaicite:1]{index=1}

## 3. Phase 0 Deliverables

1. **Curated Text Corpus:**
   - Each record: `{ source, id, text, metadata }` for SQL, email, PDF, DOCX.
   - Chunks of ~2000 tokens (≤ LLM context window). :contentReference[oaicite:2]{index=2}
2. **Vector Index in OpenSearch:**
   - k-NN index (`dimension: 384`, `knn.space_type: l2`) hosting embeddings for every chunk. :contentReference[oaicite:3]{index=3}
3. **Retrieval Client:**
   - Python script to embed queries, fetch top-k chunks, and assemble RAG prompt. :contentReference[oaicite:4]{index=4}
4. **LLM Setup & Initial Testing:**
   - Ollama installed and configured; chosen base model pulled (e.g. `llama2` or `mistral:7b`).
   - Sample RAG prompt validated end-to-end. :contentReference[oaicite:5]{index=5}
5. **Phase 0 Report:**
   - Methodology, scripts, configuration files, evaluation on golden set, and recommendations for fine-tuning :contentReference[oaicite:6]{index=6}

## 4. Timeline & Milestones

| Week | Milestone                                                       |
| ---- | --------------------------------------------------------------- |
| 1    | **Data Inventory & Ingestion** (Agents 1–2 ready)               |
| 2    | **Text Extraction & Chunking** validated on 100+ docs           |
| 3    | **Embeddings & Indexing** complete; basic k-NN retrieval tested |
| 4    | **RAG Prompt Spec** drafted; end-to-end run on golden set       |
| 5    | **Phase 0 Report** finalized; handoff to Agent 4 preparation    |

## 5. Roles & Responsibilities

- **Team 1: LLM & Core AI Services**
  - Install Ollama, pull base model, run initial completion tests.
  - Collaborate on RAG prompt design for Agent 4. :contentReference[oaicite:7]{index=7}
- **Team 2: Agent Orchestration (LangGraph)**
  - Define Agents 1–4 workflows; wire up retrieval → LLM calls. :contentReference[oaicite:8]{index=8}
- **Team 4: Data & Infra Engineering**
  - Provision OpenSearch, S3 buckets, SQL access; Dockerize Phase 0 pipeline. :contentReference[oaicite:9]{index=9}
- **QA:**
  - Annotate golden-set; measure Recall@k, precision & recall on header fields.

## 6. Success Criteria

- **Data Coverage:** ≥ 95 % of records properly extracted & chunked.
- **Retrieval Quality:** Recall@4 ≥ 0.90 on golden set.
- **End-to-End Latency:** < 1 s per query (excluding network overhead).
- **Documentation:** Fully reproducible via Docker on any dev machine.

## 7. Risks & Mitigations

| Risk                                 | Mitigation                                            |
| ------------------------------------ | ----------------------------------------------------- |
| OCR/text parser misreads key fields  | Fallback to pdfplumber; pre-clean images; regex QA    |
| Index provisioning fails at scale    | Increase OpenSearch replicas; batch parallel indexing |
| RAG prompt yields low‐quality output | Prompt tweaks; human-in-loop review for early tests   |
