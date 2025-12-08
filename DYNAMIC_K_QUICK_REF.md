# Dynamic K Scaling - Quick Reference

## What Changed?
**Before**: Hardcoded `k=20` for multi-document queries  
**After**: Dynamic calculation based on document count in vectorstore

## The Formula
```
k = max(base_k * 5, num_documents * 3)
k = max(20, num_documents * 3)
```

## Key Values
```python
# Current state (2 documents)
get_unique_documents_count()  # → 2
calculate_dynamic_k()          # → 20

# Add 2 more documents (total 4)
get_unique_documents_count()  # → 4
calculate_dynamic_k()          # → 20

# Add 8 more documents (total 12)
get_unique_documents_count()  # → 12
calculate_dynamic_k()          # → 36
```

## How to Use

### Test the Calculation
```bash
cd /home/sigmoid/Desktop/hr_assistant_bot
PYTHONPATH=backend python << 'EOF'
from app.rag.vectorstore import calculate_dynamic_k, get_unique_documents_count

docs = get_unique_documents_count()
k = calculate_dynamic_k()
print(f"Documents: {docs}, k: {k}")
EOF
```

### Add a New Document
1. Place PDF in `data/raw_docs/`
2. Run: `curl http://127.0.0.1:8000/api/ingest`
3. **Done!** Next query uses updated k automatically

### Query the System
```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "If I take leave in December, which holidays fall in that period?",
    "k": 4
  }'
```

Multi-concept queries (containing keywords like "holiday+leave") will automatically use dynamic k.

## Files Modified
- `backend/app/rag/vectorstore.py`: Added `get_unique_documents_count()` and `calculate_dynamic_k()`
- `backend/app/rag/chain.py`: Updated `run_rag()` to use dynamic k

## Scaling Examples

### Scenario 1: Start with 2 documents
```
Documents: Holiday Calendar, Hybrid Work Policy
k = max(20, 2*3) = 20
Coverage: 10 chunks per document
```

### Scenario 2: Add Benefits Policy + Reimbursement Policy (4 total)
```
Documents: +2 new policies
k = max(20, 4*3) = 20
Coverage: 5 chunks per document
(No code change needed!)
```

### Scenario 3: Enterprise Scale (15 documents)
```
Documents: Many HR policies
k = max(20, 15*3) = 45
Coverage: 3 chunks per document
(No code change needed!)
```

## Benefits Summary
✅ No hardcoding  
✅ Scales automatically  
✅ Works with any document count  
✅ Maintains ~3 chunks per document  
✅ Future-proof  

## Next Steps
- Add more HR policy PDFs as needed
- System will handle retrieval automatically
- Monitor test results for any issues
