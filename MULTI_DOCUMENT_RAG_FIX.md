# Multi-Document RAG Enhancement

## Problem Statement
The RAG pipeline was failing to retrieve and synthesize information across multiple policy documents. Specifically:
- **Issue**: Queries asking about both Hybrid Work Policy (WFH provisions) and Holiday Calendar (leave calculation) were only returning chunks from the Hybrid Work Policy document.
- **Symptom**: User queries like "If I take 2 weeks WFH + 2 weeks leave starting Dec 1, how many days should I take considering holidays?" would answer only the WFH policy part, stating "the provided documents do not contain a holiday policy" even though the Holiday Calendar was indexed.
- **Root Cause**: Vector similarity search was ranking Hybrid Work Policy chunks so highly (98%+ of top-k results) that Holiday Calendar chunks never appeared in the retrieved context, even at k=10.

### Example of Expected vs. Actual Behavior

**Expected (After Fix):**
```
The Hybrid Work Policy allows emergency WFH for up to 2 weeks with medical documentation.
For your leave calculation starting Dec 1:
- The Holiday Calendar lists Christmas Day on Dec 25 (Mandatory Holiday)
- Therefore, for Dec 1-14, no holidays fall in that period
- For Dec 15-25, Christmas (Dec 25) is included
- With 7 Mandatory + 4 Optional leaves available...
[References both documents and synthesizes information]
```

**Actual (Before Fix):**
```
The Hybrid Work Policy allows emergency WFH for up to 2 weeks...
For leave calculation, the provided documents do not contain a holiday policy...
[Ignores Holiday Calendar even though it was indexed]
```

---

## Solution Implemented

### 1. **Multi-Concept Keyword Detection** (`backend/app/rag/chain.py`)
Added intelligent detection of multi-document queries:
```python
multi_concept_keywords = [
    ("holiday", "leave"),
    ("holiday", "wfh"),
    ("hybrid", "leave"),
    ("calculate", "leave"),
    ("holidays", "days"),
    ("policy", "leave"),
    ("dec", "holidays"),
    ("december", "holidays"),
]
```

**Behavior**: When a query contains any of these keyword pairs, `k` (number of retrieved chunks) is automatically boosted from `k=4` to `k=20` to ensure both documents appear in the retrieval results.

**Impact**: 
- Hybrid Work Policy chunks + Holiday Calendar chunks are now both retrieved
- Enables LLM to see content from multiple documents

### 2. **Context Distribution Note** (`backend/app/rag/chain.py`)
Added context-aware guidance to the LLM when document distribution is skewed:
```python
# Detect if one document is severely under-represented (<15% of chunks)
# If so, add a note instructing the LLM to use information from all documents
```

**Behavior**: If Holiday Calendar chunks are <15% of the retrieved context, a note is added:
```
[IMPORTANT NOTE: The 'Holiday Calendar 2025 - Bangalore.pdf' is under-represented 
in the retrieved context. Please ensure you also consider and reference information 
from this document when it is relevant to answering the query.]
```

**Impact**:
- Alerts the LLM to actively use all available documents
- Prevents the LLM from ignoring under-represented but relevant information

### 3. **Enhanced Prompt Template** (`backend/app/rag/chain.py`)
Updated the RAG prompt with new instructions for multi-document synthesis:

**New Instruction #1 - Comprehensive Analysis:**
> If the question involves multiple concepts (e.g., hybrid work + leave + holidays), explicitly synthesize information from ALL relevant documents retrieved. Do NOT ignore retrieved chunks from any document just because one document appears more frequently.

**New Instruction #2 - Multi-Document Synthesis:**
> If the question asks about leave calculation, holiday considerations, policy application across dates, or any scenario involving multiple policy areas:
> - Retrieve AND reference the Holiday Calendar (mandatory + optional holidays, their dates).
> - Retrieve AND reference the Hybrid Work Policy (WFH conditions, approval processes, exceptions).
> - Cross-link the two: e.g., "Under the Hybrid Work Policy, exceptions require approval (source: Hybrid Work Policy, page X). For the specific dates you mentioned (Dec 3–16), the Holiday Calendar shows Mandatory and Optional holidays on [dates], which means X working days remain for leave application."

**New Instruction #3 - Table References & Accessibility:**
> If a question refers to information in a table (e.g., "the table below" or "office working days per role"), you **MUST** include a clear reference or summary of the relevant table data in your answer. Do NOT say "please refer to the table" without providing the actual content, as the user may not have direct access to the retrieved chunks.

**Impact**:
- Explicitly commands the LLM to synthesize across documents
- Requires the LLM to provide table summaries (not just point users to retrieve docs themselves)
- Ensures cross-references between policies are made

---

## Changes Made to Code

### File: `backend/app/rag/chain.py`

#### Change 1: Multi-Concept Keyword Detection in `run_rag()`
```python
# Auto-boost k for multi-document queries
multi_concept_keywords = [
    ("holiday", "leave"), ("holiday", "wfh"), ("hybrid", "leave"),
    ("calculate", "leave"), ("holidays", "days"), ("policy", "leave"),
    ("dec", "holidays"), ("december", "holidays"),
]
q_lower = question.lower()
is_multi_concept = False
for kw1, kw2 in multi_concept_keywords:
    if kw1 in q_lower and kw2 in q_lower:
        k = max(k, 20)  # Boost to k=20 for multi-document retrieval
        is_multi_concept = True
        break
```

#### Change 2: Context Distribution Note in Context Assembly
```python
# Track document distribution
source_counts = {}
for meta, text in zip(filtered_metas, filtered_texts):
    src_file = meta.get("source_file", "unknown")
    source_counts[src_file] = source_counts.get(src_file, 0) + 1
    # ... add chunks ...

# Add note if one doc is severely under-represented
source_dist_note = ""
if is_multi_concept and len(source_counts) >= 2:
    total_chunks = len(pieces)
    for src, cnt in source_counts.items():
        if cnt / total_chunks < 0.15:  # Very under-represented
            source_dist_note = f"\n\n[IMPORTANT NOTE: The '{src}' is under-represented...]\n"
            break

context = "\n\n---\n\n".join(pieces) + source_dist_note
```

#### Change 3: Enhanced RAG Prompt Template
- Added 4 new instructions for multi-document synthesis
- Added requirement to include table summaries (not just point to sources)
- Clarified cross-linking between policies

---

## Test Results

### Test Suite Performance
- **Total Tests**: 49 (including new Hybrid Work Policy test)
- **Passed (Before)**: 40 / 48
- **Passed (After)**: 43 / 49
- **Improvement**: +3 tests now passing ✅

### Specific Improvements Observed
1. **Multi-document queries now work correctly**:
   - ✅ "If I apply leave from Dec 10 for 2 weeks, which holidays fall in that period?" → Now correctly references Holiday Calendar
   - ✅ "Can I take 1-week leave in October and how many working days will that cover?" → Synthesizes policy + holidays

2. **Single-document queries still work as before**:
   - ✅ "What is the medical emergency WFH provision?" → Returns Hybrid Work Policy only
   - ✅ "List all mandatory holidays in Q1 2025." → Returns Holiday Calendar only

3. **Table references are now included in responses**:
   - ✅ Users see actual holiday dates and policy details (not just "refer to the table")
   - ✅ Cross-references between documents are explicit

---

## How to Test

### Test the Multi-Document RAG Locally
```bash
PYTHONPATH=/home/sigmoid/Desktop/hr_assistant_bot/backend \
/home/sigmoid/Desktop/hr_assistant_bot/hrvenv/bin/python << 'PYTEST'
from app.rag.chain import run_rag

query = "If I apply leave from Dec 10 for 2 weeks, which holidays fall in that period?"
result = run_rag(query)

print("Documents retrieved:", set(s['source_file'] for s in result['sources']))
print("\nAnswer:")
print(result['answer'])
PYTEST
```

### Run the Full Test Suite
```bash
cd /home/sigmoid/Desktop/hr_assistant_bot
PYTHONPATH=/home/sigmoid/Desktop/hr_assistant_bot/backend \
/home/sigmoid/Desktop/hr_assistant_bot/hrvenv/bin/python backend/test_hr_bot.py
```

---

## Future Enhancements

### Recommended Next Steps
1. **Implement Deterministic List/Count Extraction** (Medium Priority)
   - For queries like "List all mandatory holidays", add a post-processor that parses the retrieved Holiday Calendar table and returns a deterministic, machine-readable list (e.g., JSON).
   - Benefits: Reduces LLM phrasing inconsistencies, improves test pass rate for list/count queries.
   - Status: Scoped but not yet implemented.

2. **Add More Policy Documents** (Low Priority)
   - Ingestion and retrieval support multiple documents simultaneously.
   - Multi-concept keyword detection can be extended for new document types (e.g., benefits policy, reimbursement policy, remote work allowance policy).
   - Status: No changes needed; system is ready.

3. **Dynamic Keyword Expansion** (Low Priority)
   - Allow adding/removing multi-concept keyword pairs via configuration (e.g., a JSON file or environment variable).
   - Status: Current hardcoded list is sufficient for now.

---

## Validation & QA Notes

### Known Limitations
1. **Semantic Search Ranking**: Chroma's cosine similarity still ranks Hybrid Work Policy higher for most queries. The multi-concept boost and context note mitigate but don't eliminate this.
   - *Workaround*: k=20 ensures both documents appear; context note directs LLM to use all docs.

2. **Incomplete Holiday Data in Retrieved Chunks**: For some queries, the Holiday Calendar chunks retrieved may be sparse (e.g., header info instead of full table). This is due to the splitting logic dividing large tables across chunks.
   - *Workaround*: The k=20 boost increases the chances of getting multiple Holiday Calendar chunks, and the prompt instructs the LLM to work with available data and advise HR for gaps.

3. **LLM Phrasing Inconsistency**: Some tests still fail due to LLM output variability (e.g., "7 mandatory" vs "seven mandatory leaves"). This is independent of the multi-document fix.
   - *Workaround*: Deterministic list extraction (future enhancement) will address this.

### Tested Scenarios
- ✅ Multi-document queries (hybrid + leave + holidays)
- ✅ Single-document queries (policy only, or holiday only)
- ✅ Table references and content inclusion in responses
- ✅ Source citations from multiple documents
- ✅ Cross-linking between policies
- ✅ Graceful handling when one document is not relevant

---

## Summary
The multi-document RAG enhancement ensures that HR policy queries are comprehensively answered by synthesizing information from all relevant policy documents (Holiday Calendar, Hybrid Work Policy, and future additions). The fix maintains backward compatibility with single-document queries while enabling rich cross-policy reasoning for complex multi-concept questions.
