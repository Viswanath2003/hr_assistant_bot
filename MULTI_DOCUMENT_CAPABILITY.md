# Multi-Document RAG System - Capability & Future-Proofing

## ✅ Current Status: READY FOR MULTIPLE DOCUMENTS

Your HR Assistant Bot is **fully designed** to handle multiple documents without any code changes required.

---

## 📋 How the System Works

### 1. **Document Loading** (`backend/app/rag/loader.py`)
- **Function**: `load_all_pdfs()`
- **Behavior**: Automatically scans `data/raw_docs/` for **ALL PDF files**
- **No filtering**: Works with any document type (holidays, policies, bonds, compensation, etc.)
- **Metadata**: Each document is tagged with its filename

### 2. **Document Processing** (`backend/app/rag/ingest_pipeline.py`)
- **Function**: `ingest_documents()`
- **Behavior**: Processes ALL loaded documents in a single pipeline
- **Chunking**: Text is split using generic RecursiveCharacterTextSplitter (not domain-specific)
- **Metadata enrichment**: Each chunk tagged with `source_file`, `page_no`, `chunk_index`

### 3. **Vector Storage** (`backend/app/rag/vectorstore.py`)
- **Single Collection**: All documents stored in one ChromaDB collection named `"hr_docs"`
- **Unified Index**: Embeddings computed for all chunks regardless of source
- **Deduplication**: Generic normalized-text deduplication (works across documents)
- **Persistent**: Stored in `data/chroma/` and persists across restarts

### 4. **Retrieval** (`backend/app/rag/vectorstore.py`)
- **Function**: `get_retriever(k=4)`
- **Behavior**: Performs semantic similarity search across **ALL documents**
- **Result**: Top-k chunks from any/all documents ranked by relevance
- **Source Tracking**: Each result includes `source_file` metadata

### 5. **RAG Chain** (`backend/app/rag/chain.py`)
- **Generic Prompt**: Domain-agnostic instructions (no holiday-specific logic)
- **Multi-source Input**: Receives chunks from multiple documents in same call
- **Intelligent Reasoning**: LLM can reason across documents and cite sources
- **Fallback Responses**: Contextual, user-friendly messages for missing info

---

## 🚀 How to Add New Documents

### Step 1: Add Your Document
```bash
# Copy document to raw_docs folder
cp /path/to/Leave_Policy.pdf /home/sigmoid/Desktop/hr_assistant_bot/data/raw_docs/
cp /path/to/Compensation_Policy.pdf /home/sigmoid/Desktop/hr_assistant_bot/data/raw_docs/
```

### Step 2: Re-ingest (Optional - Auto-runs at startup)
```bash
PYTHONPATH=backend /home/sigmoid/Desktop/hr_assistant_bot/hrvenv/bin/python - <<'PY'
from app.rag.ingest_pipeline import ingest_documents
result = ingest_documents()
print(result)
PY
```

### Step 3: Query Automatically Uses All Documents
```bash
# No code changes needed - just ask questions
PYTHONPATH=backend /home/sigmoid/Desktop/hr_assistant_bot/hrvenv/bin/python - <<'PY'
from app.rag.chain import run_rag
r = run_rag("What is the maternity leave policy?", k=4)
print(r['answer'])
PY
```

---

## 📊 Supported Document Types (No Changes Required)

Your system automatically supports adding:

- ✅ **Holiday Policies** (current)
- ✅ **Leave Policies** (maternity, sick, casual, etc.)
- ✅ **Compensation Policies** (salary, bonuses, increments)
- ✅ **Bond Details** (lock-in periods, penalty clauses)
- ✅ **Working Policies** (remote work, office hours, dress code)
- ✅ **Benefits Policies** (health insurance, retirement, etc.)
- ✅ **Code of Conduct** (ethics, compliance, etc.)
- ✅ **Any other HR policy document** (no code modifications needed)

---

## 🔄 Cross-Document Query Examples

After adding Leave Policy document:

### Example 1: Multi-Doc Query
```
Q: "Can I take optional holidays as leave?"
A: [Cites Holiday Calendar + Leave Policy]
   "Based on Holiday Calendar, Optional Holidays are maximum 4 per year. 
    Per Leave Policy, these can be taken as personal leave. Please confirm 
    with your manager before scheduling."
```

### Example 2: Policy Interaction Query
```
Q: "Do mandate holidays count against my leave balance?"
A: [Cites both documents]
   "According to Holiday Calendar, Mandate Holidays are company holidays 
    and do NOT count against leave balance. Leave Policy confirms that 
    mandatory holidays are company-paid non-working days."
```

### Example 3: Location + Multi-Doc Query
```
Q: "If I'm working from Hyderabad, what leave am I entitled to?"
A: [Uses location inference + cross-doc data]
   "The Holiday Calendar applies to 'Bangalore & Rest of India', so you're 
    covered. Based on Leave Policy for India offices: 7 Mandate Holidays + 
    4 Optional Holidays + [entitlements from Leave Policy]. Please contact 
    HR for region-specific variations."
```

---

## 🛠️ What Works Without Code Changes

| Feature | Status | Behavior |
|---------|--------|----------|
| Adding new documents | ✅ Ready | Just drop PDFs in `data/raw_docs/` |
| Multi-document queries | ✅ Ready | Automatically searches all docs |
| Cross-document reasoning | ✅ Ready | LLM reasons over chunks from multiple sources |
| Source tracking | ✅ Ready | Each answer cites which document it came from |
| Contextual fallback | ✅ Ready | Smart responses when info not found |
| Location inference | ✅ Ready | Works with any scope/region |
| Deduplication | ✅ Ready | Works across all documents |

---

## ⚙️ What Might Need Tuning (Optional)

| Item | When to Adjust | Example |
|------|----------------|---------|
| Retrieval k value | Too few/many results retrieved | Change `run_rag(q, k=6)` from k=4 |
| Chunk size | Documents have very long tables | Edit `CHUNK_SIZE` in `config.py` |
| Chunk overlap | Duplicate content across chunks | Edit `CHUNK_OVERLAP` in `config.py` |
| Prompt instructions | Different answer style needed | Edit `RAG_PROMPT` in `chain.py` |

---

## 📝 Architecture Diagram

```
┌─────────────────────────────────────┐
│   data/raw_docs/                    │
│   ├─ Holiday Calendar 2025.pdf      │
│   ├─ Leave Policy.pdf (future)      │
│   ├─ Compensation.pdf (future)      │
│   └─ ...more PDFs                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   loader.py (load_all_pdfs)         │
│   → Finds & loads ALL PDFs          │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   splitter.py (split_text)          │
│   → Chunks text (generic, no filter)│
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   vectorstore.py (add_to_chroma)    │
│   → Single "hr_docs" collection     │
│   → All chunks with metadata        │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   ChromaDB (data/chroma/)           │
│   → Unified embedding index         │
│   → All documents searchable        │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   retriever.invoke(question)        │
│   → Semantic search ALL docs        │
│   → Return top-k chunks + metadata  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   RAG_PROMPT + LLM                  │
│   → Generic, domain-agnostic        │
│   → Reasons across docs             │
│   → Cites sources                   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   User-friendly response with       │
│   source citations & reasoning      │
└─────────────────────────────────────┘
```

---

## ✅ Conclusion

**Your system is production-ready for multiple documents.**

- **No code changes** required to add new HR policy documents
- **Automatic retrieval** across all documents in the collection
- **Generic reasoning** that works for any HR topic
- **Transparent sourcing** showing which document each fact came from
- **Contextual fallback** for information not in documents

Simply add documents to `data/raw_docs/` and the system will start using them. ✅

---

## 📞 Quick Reference

```bash
# Add a new document
cp MyPolicy.pdf data/raw_docs/

# Re-ingest (if needed; auto-runs at startup)
PYTHONPATH=backend /home/sigmoid/Desktop/hr_assistant_bot/hrvenv/bin/python -c \
  "from app.rag.ingest_pipeline import ingest_documents; print(ingest_documents())"

# Test a query
PYTHONPATH=backend /home/sigmoid/Desktop/hr_assistant_bot/hrvenv/bin/python - <<'PY'
from app.rag.chain import run_rag
print(run_rag("Your question here", k=4)['answer'])
PY
```
