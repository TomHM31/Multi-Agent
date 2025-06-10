# Phase 0: RAG Implementation Plan

## 1. Prepare Environment and Dependencies

### 1.1. Create and activate a new Python virtual environment

```bash
python -m venv rag_env && source rag_env/bin/activate
```

### 1.2. Install required Python packages

```bash
pip install \
  sentence-transformers \
  psycopg2-binary \
  mailparser \
  pdfplumber \
  python-docx \
  tiktoken \
  boto3 \
  requests \
  requests-aws4auth
```

### 1.3. Install Ollama

- Follow platform-specific instructions (e.g., `brew install ollama` for macOS)

### 1.4. Pull a local LLM with Ollama

```bash
ollama pull llama2
```

### 1.5. Configure AWS credentials

Ensure environment variables are set:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## 2. Export and Extract All Data Sources to Plain Text

### 2.1. SQL Tables → Plain Text

```python
# Example using psycopg2
{
  "source": "workflow_steps",
  "id": "workflow_42",
  "text": "Workflow InvoiceApproval – Step 1: Clerk submits invoice; Role: Clerk.",
  "metadata": { "workflow_name": "InvoiceApproval", "step_order": 1, "role": "Clerk" }
}
```

### 2.2. Outlook Emails → Plain Text

```python
# Using mailparser
{
  "source": "email",
  "id": "email_2025-06-06_1234.msg",
  "text": "From: finance@company.com\nDate: 2025-06-06\nSubject: New Expense Policy Update\n\nHello team, please note...",
  "metadata": { "subject": "New Expense Policy Update", "sender": "finance@company.com", "date": "2025-06-06" }
}
```

### 2.3. PDF Documents → Plain Text

```python
# Using pdfplumber
{
  "source": "pdf",
  "id": "policy_manual_page_3",
  "text": "<raw page text>",
  "metadata": { "filename": "policy_manual.pdf", "page": 3 }
}
```

### 2.4. DOCX Files → Plain Text

```python
# Using python-docx
{
  "source": "docx",
  "id": "onboarding_guide_docx_para_5",
  "text": "Employees must complete training before...",
  "metadata": { "filename": "onboarding_guide.docx", "para": 5 }
}
```

## 3. Chunk Plain-Text Records

```python
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
MAX_TOKENS = 2000

# Chunking logic
{
  "chunk_id": "<original_id>_chunk_1",
  "text": "<piece>",
  "metadata": {
    ...original metadata...,
    "source": "<original source>",
    "original_id": "<original_id>",
    "chunk_index": 1
  }
}
```

## 4. Create OpenSearch k-NN Index

```json
PUT /company_docs
{
  "settings": {
    "index.knn": true,
    "index.knn.space_type": "l2"
  },
  "mappings": {
    "properties": {
      "chunk_id":    { "type": "keyword" },
      "text":        { "type": "text" },
      "embedding":   { "type": "knn_vector", "dimension": 384 },
      "source":      { "type": "keyword" },
      "original_id": { "type": "keyword" },
      "chunk_index": { "type": "integer" }
    }
  }
}
```

## 5. Compute Embeddings and Index

```python
from sentence_transformers import SentenceTransformer
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# Embedding and indexing logic
{
  "chunk_id": "<chunk_id>",
  "text":     "<chunk_text>",
  "embedding":[<list_of_384_floats>],
  "source":   "<source>",
  "original_id":"<original_id>",
  "chunk_index": <chunk_index>
}
```

## 6. Configure Ollama for Local LLM

```bash
ollama serve
```

```python
import requests

OLLAMA_HOST  = "http://localhost:11434"
OLLAMA_MODEL = "llama2"

def call_llm_via_ollama(prompt, max_tokens=512, temperature=0.0, stop=None):
    payload = {
      "model": OLLAMA_MODEL,
      "prompt": prompt,
      "max_tokens": max_tokens,
      "temperature": temperature
    }
    if stop:
        payload["stop"] = stop
    resp = requests.post(f"{OLLAMA_HOST}/v1/completions", json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["text"]
```

## 7. Implement RAG Retrieval and LLM Prompting

### 7.1. Retrieve Top-k Chunks from OpenSearch

```python
q_vec = embed_model.encode([question], convert_to_numpy=True)[0].tolist()
```

### 7.2. Build LLM Prompt

```
Below are relevant excerpts from our company knowledge base:

--- Chunk 1 (id: workflow_42_chunk_1) ---
<text of chunk 1>

--- Chunk 2 (id: policy_17_chunk_1) ---
<text of chunk 2>

--- Chunk 3 (id: email_2025-06-06_1234) ---
<text of chunk 3>

--- Chunk 4 (id: pdf_policy_manual_page_3) ---
<text of chunk 4>

Question: What is our vendor-onboarding process?
Please answer using only the passages above.
```

### 7.3. Call Ollama

```python
answer = call_llm_via_ollama(prompt, max_tokens=512, temperature=0.0, stop=["\n\n"])
```

## 8. Verify Phase 0 End-to-End

```python
# Sample verification
question = "What is our standard invoice-approval process?"
answer = call_llm_with_rag(question)
print(answer)
```

---

**Next Steps**:

1. Execute each phase step in sequence
2. Validate outputs at each stage
3. Troubleshoot any integration issues
