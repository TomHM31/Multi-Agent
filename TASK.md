<!-- TASK.md -->

# Phase 0 Task List (Detailed)

---

## A. Setup & Environment (Team 4)

### 1. Repo & Version Control

- [ ] **Initialize Git repository**
  - Define branch strategy: `main`, `develop`, `feature/<task-name>`
  - Add `.gitignore` (virtual envs, IDE files, local data)
- [ ] **Requirements & Documentation**
  - Create `requirements.txt` pinning versions for:
    - `sentence-transformers`
    - `pdfplumber` / `PyMuPDF`
    - `python-docx`
    - `tiktoken`
    - `boto3`, `requests-aws4auth`
    - `flask` or `fastapi`
  - Draft `README.md` with:
    - Project overview
    - Setup instructions
    - Phase 0 workflow summary

### 2. Containerization & CI

- [ ] **Dockerfile**
  - Multi-stage build:
    1. Install Python dependencies
    2. Copy in code & assets
    3. Configure entrypoints for each service
- [ ] **docker-compose.yml**

  - Define services:
    - `ingestion_service`: runs SQL / S3 / email extractors
    - `preprocessing_service`: runs PDF/DOCX parsers & OCR
    - `indexing_service`: runs chunking & embedding indexers
    - `retrieval_api`: exposes RAG client via HTTP
  - Set up environment variables for:
    - AWS credentials (access key, secret, region)
    - S3 bucket names (`RAW_BUCKET`, `ARCHIVE_BUCKET`)
    - OpenSearch endpoint & auth

- [ ] **CI Pipeline** (e.g. GitHub Actions)
  - Linting & formatting (Black, Flake8)
  - Build & smoke-test Docker images
  - Run unit tests on extraction and chunking scripts

### 3. Infrastructure Provisioning (AWS)

- [ ] **S3 Buckets**

  - `invoices-raw` (ingestion)
  - `invoices-archive` (long-term storage)
  - Document bucket names in `config.yaml`

- [ ] **OpenSearch Domain**

  - Enable k-NN plugin
  - Define instance type & storage (e.g. `t3.large.search`, 100 GB)
  - Capture domain endpoint & ARN

- [ ] **IAM Roles & Policies**
  - Role for ingestion/preprocessing with S3 GetObject permissions
  - Role for indexing with OpenSearch write permissions
  - Store ARNs & role names in `infra/roles.md`

---

## B. Ingestion & Preprocessing (Agents 1–2)

### Agent 1: Invoice Ingestion Agent

- [ ] **ingest_from_s3.py**
  - Monitor S3 `invoices-raw` via SNS/SQS or cron
  - Download new files + metadata (key, size, timestamp)
  - Log ingestion events to CloudWatch or local log
  - Push file path & metadata to preprocessing queue (e.g. Redis)

### Agent 2: Preprocessing Agent

- [ ] **File Validation**

  - Verify extension ∈ {`.pdf`, `.docx`, `.csv`, `.xlsx`}
  - Flag unsupported types for manual review

- [ ] **PDF Text Extraction**

  - `extract_pdf.py` using PyMuPDF/pdfplumber
    - Extract text + basic layout (page, block, line)
    - Detect scanned pages (no text) → route to OCR

- [ ] **OCR for Scanned PDFs**

  - Integrate Tesseract or AWS Textract fallback
  - Configure image preprocessing (deskew, denoise)

- [ ] **DOCX Extraction**

  - `extract_docx.py` using `python-docx`
  - Flatten tables: translate rows → “Cell 1: …; Cell 2: …”

- [ ] **Text Normalization**

  - `normalize_text.py` utility:
    - Remove extra whitespace, fix encoding
    - Strip common headers/footers via regex rules
  - Output: JSON file `{ source, filename, text, metadata }`

- [ ] **Output Management**
  - Save normalized JSON to S3 `preprocessed/` or local store
  - Emit completion event to next queue

---

## C. Chunking & Indexing

### Chunking (chunk_text.py)

- [ ] **Tokenize & Split**
  - Use `tiktoken` to split text into ≤ 500 tokens with 50-token overlap
  - Preserve metadata: `source`, `vendor` (if known), `chunk_id`
- [ ] **Persistence**
  - Write chunk files to local folder or S3 `chunks/`

### Embedding & OpenSearch Indexing (index_chunks.py)

- [ ] **Load Embedding Model**
  - `all-MiniLM-L6-v2` via `sentence-transformers`
- [ ] **Define Index Mapping**
  - `vector.dimensions: 384`, `knn.space_type: l2`
  - Metadata fields: `source`, `vendor`, `chunk_id`
- [ ] **Bulk Index**
  - Batch-synchronous embedding → bulk-put to OpenSearch
  - Implement retry/backoff for failures
  - Log success/failure counts

---

## D. Retrieval Prototype (Tool for Agent 3)

### RAG Client Script (run_rag.py)

- [ ] **Embed Question**

  - Function `embed_question(text) → vector`

- [ ] **k-NN Search**

  - Connect to OpenSearch, query top-k chunks

- [ ] **Assemble Context**

  - Concatenate chunk texts in rank order, annotate with sources

- [ ] **Prompt Formatter**

  - Wrap context + original question into a structured prompt:
    ```
    System: You are an invoice-extraction assistant…
    Context: <chunk1>…<chunkN>
    Question: <user question>
    Response format: JSON { … }
    ```

- [ ] **CLI & HTTP Interface**
  - Expose `run_rag.py` CLI for local testing
  - Integrate into `retrieval_api` as `/rag` endpoint

---

## E. LLM Setup & Initial Test (Team 1)

### Local LLM Hosting with Ollama

- [ ] **Install Ollama** (Homebrew/Linux/WSL)
- [ ] **Pull Base Model**
  - `ollama pull mistral:7b` (or chosen variant)
- [ ] **Configuration**
  - Document model name, version, and pull command in `models.md`

### Smoke Test

- [ ] **End-to-End Check**
  1. Run `run_rag.py --question "What is the invoice number?"`
  2. Pipe output to Ollama:
     ```bash
     run_rag.py … | ollama run mistral:7b --prompt "$(cat -)"
     ```
  3. Verify JSON response contains correct fields

---

## F. QA, Metrics & Reporting

### Golden-Set Evaluation

- [ ] **Prepare Golden Set**
  - 20 invoices with ground-truth JSON in `golden/`
- [ ] **Automated Tests**
  - Script `evaluate_golden.py` to compute precision/recall for each field
  - Generate summary report (`metrics_phase0.csv`)

### Logging & Monitoring

- [ ] **Centralized Logging**
  - Ingestion/preprocessing/indexing/retrieval each log to stdout and CloudWatch
- [ ] **Health Checks**
  - Docker health endpoints for each service
  - Alert if any service is `unhealthy` for > 5 min

---

## G. Phase 0 Report & Handoff

- [ ] **Draft Report** (`phase0_report.md`)

  - Executive summary, architecture diagram, scripts overview
  - Initial metrics & observations
  - Issues encountered & mitigations

- [ ] **Demo Script** (`demo_phase0.sh`)

  - Automate: ingest → preprocess → chunk → index → RAG → LLM
  - Print stage-by-stage status & final JSON

- [ ] **Stakeholder Review**

  - Schedule demo session
  - Incorporate feedback into final docs

- [ ] **Finalize & Commit**
  - Merge all changes, tag `phase0-complete`
  - Share link to docs and repo with team Slack/Email
