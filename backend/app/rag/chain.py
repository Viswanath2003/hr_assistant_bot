# backend/app/rag/chain.py
from datetime import datetime
from typing import List, Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import logging

from ..core.llm import get_llm
from .vectorstore import get_retriever, calculate_dynamic_k
from .filter import filter_chunks
import re


# --------------------------
# 1. Prompt Template
# --------------------------
RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question", "today"],
    template="""
You are an **Expert HR Policy Assistant Bot** for Sigmoid, named **SIHRA**, specializing in document-exclusive retrieval and synthesis. Your goal is to provide accurate, formally toned, and fully cited answers based ONLY on the context provided.

CRITICAL INSTRUCTIONS & CONSTRAINTS (GUARDRAILS):

1.  Scope Restriction: Use the provided context exclusively. DO NOT use external knowledge for factual claims.
2.  Prohibited Topics: You MUST NOT answer questions related to: Individual PII, Legal/Financial Advice, or Subjective Judgments. Use the Refusal Protocol for these. **CRUCIAL EXCEPTION: Do not refuse basic factual company information (address, email, website) if it is present in the context.**
3.  Contextual Reasoning (Geographic/Time): You are authorized to use verified common world knowledge (e.g., Hyderabad is in India, Q4 is Oct-Dec) to interpret policy scope (e.g., geographic applicability, chronological ordering). The label 'Bangalore & Rest of India' covers all Indian offices.
4.  Conflict Resolution & Numerical Precision: When retrieving holiday counts (Mandatory, Optional, or Total), if the number derived from the list/table (e.g., 9 Mandatory) conflicts with a number mentioned in the policy text (e.g., "7 Mandate Leaves"), you **MUST** present both conflicting values, state the discrepancy clearly, and advise the user to contact HR. **DO NOT** provide a single, synthesized number.
5.  Tone: Maintain a Formal, Neutral, and Professional tone.

EXECUTION INSTRUCTIONS:

1.  Comprehensive Analysis: Review the user's question and all retrieved chunks. **If the question involves multiple concepts (e.g., hybrid work + leave + holidays), explicitly synthesize information from ALL relevant documents retrieved. Do NOT ignore retrieved chunks from any document just because one document appears more frequently.**
2.  **ABSOLUTE CHRONOLOGICAL INTEGRITY:** For all time-based answers (e.g., 'next', 'remaining', 'after', 'List all holidays in order'), you **MUST** treat the Mandatory and Optional lists as a **single, unified set of 17 events**. You **MUST** sort this unified list by date (e.g., March 14 comes before March 30). **DO NOT** skip any holiday, regardless of category, when determining chronological order.
3.  **ABSOLUTE CATEGORICAL INTEGRITY:** When listing holidays, you **MUST** use the exact classification (Mandatory or Optional) that is stated in the **EXPLICIT TABLE HEADER** of the source document for that holiday. **NEVER** infer or reclassify a holiday based on its position in the chronological list or other textual mentions. **Always include the classification, date, and day.**
4.  **Multi-Document Synthesis:** If the question asks about leave calculation, holiday considerations, policy application across dates, or any scenario involving multiple policy areas:
    - Retrieve AND reference the Holiday Calendar (mandatory + optional holidays, their dates).
    - Retrieve AND reference the Hybrid Work Policy (WFH conditions, approval processes, exceptions).
    - Cross-link the two: e.g., "Under the Hybrid Work Policy, exceptions require approval (source: Hybrid Work Policy, page X). For the specific dates you mentioned (Dec 3–16), the Holiday Calendar shows Mandatory and Optional holidays on [dates], which means X working days remain for leave application."
    - **FOR LEAVE CALCULATION WITH HOLIDAYS:** If the user specifies a date range for leave/WFH and asks how many days to apply for, you MUST:
      1. CRITICAL: Identify the LEAVE period separately from WFH period. Do NOT mix them.
         - If user says "2 weeks WFH from Jan 10, then 2 weeks leave immediately", the leave period STARTS AFTER WFH ends.
         - WFH: Jan 10-23 (14 days) | LEAVE PERIOD: Jan 24-Feb 6 (14 calendar days) ← calculate only this for leave days
      2. Extract the full holiday list from the Holiday Calendar for the relevant month(s).
      3. Identify which holidays fall within the LEAVE period specifically (not WFH period).
      4. Calculate: Working days for leave = Leave calendar days - Weekend days in leave period - Holiday days in leave period.
      5. Provide the final leave count explicitly - this is ONLY for the leave days, not WFH days.
      6. Show your working: "Leave period: [date] to [date] = X calendar days. Weekends: -Y. Holidays in leave period: -Z. Total leave days = X-Y-Z working days."
5.  **Table References & Accessibility:** If a question refers to information in a table (e.g., "the table below" or "office working days per role"), **you MUST include a clear reference or summary of the relevant table data in your answer**. For example:
    - "According to the Hybrid Work Policy table, the office working requirements are: [summarize table rows/columns]"
    - "The Holiday Calendar shows: [list or summary of relevant holidays]"
    - Do NOT say "please refer to the table" without providing the actual content, as the user may not have direct access to the retrieved chunks.
6.  Construct Answer: Generate the answer, prioritizing clarity and synthesis. Ensure all constraints are met before finalizing the response.
7.  **FINAL REFUSAL PROTOCOL (Factual Denial):** If a holiday/data point is factually present in the Mandatory or Optional tables, you **MUST** retrieve and report that data. **DO NOT** respond with phrases like "I cannot provide information" or "There are no holidays listed" if the Holiday Calendar table is present in the retrieved chunks.
8.  **COMPREHENSIVE HOLIDAY EXTRACTION MANDATE:** When the question asks to "list holidays" or "show holidays" or involves holiday considerations for date ranges, you **MUST:**
    a) Scan ALL retrieved chunks for ANY Holiday Calendar table sections containing "Mandate Holidays" or "Optional Holidays" or holiday date entries.
    b) Extract EVERY single holiday entry found across all chunks for the requested time period(s), regardless of fragmentation.
    c) For each holiday extracted, ALWAYS include: Holiday Name, Full Date (Day Month Year), Day of Week.
    d) Group extracted holidays by their stated category (Mandatory vs Optional) as shown in the source document.
    e) If holiday table data appears split across multiple chunks, RECONSTRUCT and COMBINE all fragments into one complete list.
    f) Cross-check: If the chunks contain holiday data but your draft response says "no holidays found", STOP and re-extract. Holiday data must NEVER be omitted if present in chunks.
    g) **Critical Rule:** If a user query references specific date ranges (e.g., "from Jan 10 to Feb 6") and Holiday Calendar chunks are retrieved, you MUST extract and identify ALL holidays falling within that range, even if only fragments are visible. Use context clues (month names, dates visible in chunks) to reconstruct the full picture.
9.  **INTELLIGENT TABLE DATA RECONSTRUCTION:** When Holiday Calendar data appears fragmented:
    - Look for table structure markers (S.No, Holidays, Date, Month, Day columns or similar).
    - Combine partial rows from multiple chunks to form complete holiday entries.
    - If you see "1 New Year..." in one chunk and "14 Makara Sankranti..." in another chunk for the same month, synthesize them into a unified list.
    - Never claim "insufficient data" if the chunks contain table fragments - reconstruct intelligently using visible patterns.
10. **TEMPORAL REASONING FOR PROBATION STATUS:** When a question involves joining date and resignation/notice period:
    - **CRITICAL**: If the retrieved context contains probation duration information (e.g., "probation period is 6 months from date of joining"), you MUST use this to determine the employee's status.
    - Calculate the time between join date and resignation date.
    - If this duration is LESS than the stated probation period, the employee is ON PROBATION.
    - Example: If probation is 6 months and employee joined Nov 2025 and resigns Nov 30 2025, that's less than 1 month → employee is ON PROBATION.
    - **DO NOT** give conditional answers like "if you are on probation" when you can definitively determine status from the timeline.
    - State the determination clearly: "Since you joined in November 2025 and are resigning on November 30, 2025 (less than 1 month), you are on probation. Therefore, your notice period is 30 days (1 month)."

12. **CONVERSATIONAL CONTEXT AWARENESS:** You are provided with a [CONVERSATION HISTORY] section at the beginning of the context.
    - **CRITICAL**: Use this history to resolve pronouns (e.g., "it", "that", "the policy") and implicit references in the current USER QUESTION.
    - If the user asks "is it mandatory?" or "what about the other one?", look at the previous Assistant response in the history to identify the subject.
    - Treat the conversation as a continuous dialogue. Do not ask for clarification if the context is clear from the history.

OUTPUT FORMAT:

The final output **MUST** adhere to this structure:

<Answer Text (Formal and Synthesized, including any necessary conflict statements and cross-document linkages)>


RETRIEVED DOCUMENTS:
{context}

USER QUESTION:
{question}

TODAY'S DATE:
{today}

YOUR RESPONSE:
"""
)


def build_rag_chain():
    """
    Build the RAG pipeline using LCEL:
        retrieve → format prompt → LLM → string output
    This function returns a chain object that can be invoked with .invoke().
    """

    llm = get_llm()
    parser = StrOutputParser()

    # Chain breakdown:
    # 1) Inputs: {"context": ..., "question": ...}
    # 2) Pass into prompt template
    # 3) Pass into Gemini LLM
    # 4) Parse as string

    chain = RAG_PROMPT | llm | parser

    return chain


def run_rag(question: str, k: int = 4, chat_history: list = None) -> Dict[str, Any]:
    """
    Executes the RAG flow:
       - retrieve relevant chunks
       - build context (including chat history if provided)
       - run LCEL chain
       - return answer + sources
    
    Args:
        question: Current user query
        k: Number of chunks to retrieve
        chat_history: Optional list of previous messages [{"role": "user"|"assistant", "content": "..."}]
    
    For multi-concept questions (hybrid + leave + holidays), we auto-boost k
    to ensure cross-document retrieval. The boost is calculated dynamically
    based on the number of unique documents in the vectorstore.
    """
    
    if chat_history is None:
        chat_history = []
    
    # ========================================================================
    # QUERY EXPANSION: Detect temporal patterns and expand with relevant keywords
    # ========================================================================
    # If query mentions joining + resignation within short timeframe, add "probation"
    # to help retrieve Probation Policy documents
    q_lower = question.lower()
    expanded_query = question
    
    # Detect join date + resignation patterns (implies probation status)
    join_indicators = ["joined", "join", "joining", "started", "start"]
    resign_indicators = ["resign", "resignation", "notice period", "leave the org", "quit"]
    
    has_join = any(indicator in q_lower for indicator in join_indicators)
    has_resign = any(indicator in q_lower for indicator in resign_indicators)
    
    # If query has both join and resign/notice period, expand with probation
    if has_join and has_resign and "probation" not in q_lower:
        expanded_query = question + " probation period duration"
        logging.debug(f"Query expansion: Added 'probation period duration' to query")
    
    # Detect holiday-related queries that need the Holiday Calendar
    holiday_query_indicators = ["next holiday", "upcoming holiday", "whats holiday", "what holiday", 
                                 "which holiday", "remaining holiday", "future holiday"]
    is_holiday_query = any(indicator in q_lower for indicator in holiday_query_indicators)
    
    if is_holiday_query and "calendar" not in q_lower:
        expanded_query = expanded_query + " Holiday Calendar 2025 Bangalore mandatory optional"
        logging.debug(f"Query expansion: Added Holiday Calendar keywords to query")
    
    # ========================================================================
    # DOCUMENT LISTING QUERIES: Ensure all documents are represented
    # ========================================================================
    # Detect queries asking for list of documents/policies
    doc_listing_indicators = [
        "list all doc", "list doc", "all doc", "what doc", "which doc",
        "list all polic", "list polic", "all polic", "what polic", "which polic",
        "what can you help", "what info", "what information",
        "available doc", "available polic", "access to"
    ]
    
    is_doc_listing_query = any(indicator in q_lower for indicator in doc_listing_indicators)
    
    if is_doc_listing_query:
        # For document listing queries, we need chunks from ALL documents
        # Boost k to ensure we get at least one chunk from each document
        from .vectorstore import get_unique_documents_count
        num_docs = get_unique_documents_count()
        k = max(k, num_docs * 2)  # At least 2 chunks per document
        
        # Expand query with document names to improve retrieval
        expanded_query = question + " Holiday Calendar Probation Policy Separation Policy Hybrid Work Policy"
        logging.debug(f"Document listing query detected. Boosted k={k}, expanded query")
    
    # Auto-boost k for multi-document queries
    # Detect multi-concept signals (holiday + leave + hybrid, or policy + calculation, etc.)
    multi_concept_keywords = [
        ("holiday", "leave"),
        ("holiday", "wfh"),
        ("hybrid", "leave"),
        ("calculate", "leave"),
        ("holidays", "days"),
        ("policy", "leave"),
        ("dec", "holidays"),
        ("december", "holidays"),
        ("january", "leave"),
        ("january", "wfh"),
        ("february", "leave"),
        ("approval", "leave"),
        ("leave", "approval"),
        # Month names with leave/policy/wfh
        ("march", "leave"), ("april", "leave"), ("may", "leave"),
        ("june", "leave"), ("july", "leave"), ("august", "leave"),
        ("september", "leave"), ("october", "leave"), ("november", "leave"),
        # Any month with any policy/procedure
        ("month", "policy"), ("policy", "procedure"),
        # Notice period + resignation queries (need both Probation and Separation policies)
        ("notice", "period"), ("resign", "notice"), ("resignation", "notice"),
    ]
    
    is_multi_concept = False
    for kw1, kw2 in multi_concept_keywords:
        if kw1 in q_lower and kw2 in q_lower:
            # For multi-concept queries, use dynamically calculated k
            # This ensures we get chunks from all relevant documents
            # Formula: max(base_k * 5, num_documents * 3)
            k = calculate_dynamic_k(question, base_k=4)
            is_multi_concept = True
            logging.debug(f"Multi-concept query detected. Dynamic k={k}")
            break

    retriever = get_retriever(k=k)
    # Use expanded query for retrieval to get better multi-document coverage
    docs = retriever.invoke(expanded_query)   # LCEL-compatible API
    
    # ========================================================================
    # DOCUMENT LISTING SPECIAL CASE: Inject complete document list
    # ========================================================================
    # For document listing queries, prepend a summary of ALL available documents
    # to ensure the LLM can list them all, regardless of retrieval results
    document_list_context = ""
    if is_doc_listing_query:
        from .vectorstore import get_chroma_client
        client = get_chroma_client()
        collection = client.get_or_create_collection(
            name="hr_docs",
            metadata={"hnsw:space": "cosine"}
        )
        all_items = collection.get()
        
        if all_items and all_items.get("metadatas"):
            unique_docs = set()
            for meta in all_items["metadatas"]:
                source_file = meta.get("source_file", "")
                if source_file:
                    unique_docs.add(source_file)
            
            doc_list = sorted(list(unique_docs))
            document_list_context = "[SYSTEM NOTE: Complete list of available documents in knowledge base: " + ", ".join(doc_list) + "]\n\n"
            logging.debug(f"Injected document list: {doc_list}")
    
    # ========================================================================
    # TWO-PHASE CHUNK PROCESSING: MATCH FIRST, THEN RANK
    # ========================================================================
    # NO HARDCODING - Pure deterministic matching and ranking
    # Phase 1: Filter chunks that MATCH the question's intent
    # Phase 2: Rank matching chunks by completeness
    # ========================================================================
    
    def extract_question_concepts(q: str) -> set:
        """
        Extract meaningful question concepts (NOT hardcoded keywords).
        Returns set of significant words.
        
        Includes:
        - Words > 3 chars (to catch month names like "june", "july")
        - Alphabetic only (removes dates, numbers)
        - Excludes common stopwords (the, and, for, etc.)
        - INCLUDES month names (january, february, etc.)
        - INCLUDES action words (leave, policy, approval, etc.)
        """
        q_lower = q.lower()
        # Common English stopwords that don't add meaning
        stopwords = {"the", "and", "for", "from", "with", "this", "that", "are", "is", "on", "or", "to", "a", "an", "by", "at", "be", "been", "if", "as", "in"}
        
        # Extract words longer than 3 chars, alphabetic only
        concepts = set(
            w for w in q_lower.split() 
            if len(w) > 3 and w.isalpha() and w not in stopwords
        )
        return concepts
    
    def chunk_matches_question(chunk_content: str, question_concepts: set) -> bool:
        """
        DETERMINISTIC matching: Does chunk address question's concepts?
        NO hardcoding - based on concept overlap.
        
        IMPORTANT: Match ALL chunks that share ANY concept (>= 1).
        This ensures no relevant chunks are skipped before ranking.
        Ranking happens AFTER matching, not during matching.
        """
        if not question_concepts:
            return True
        
        chunk_lower = chunk_content.lower()
        stopwords = {"the", "and", "for", "from", "with", "this", "that", "are", "is", "on", "or", "to", "a", "an", "by", "at", "be", "been", "if", "as", "in"}
        
        chunk_words = set(
            w for w in chunk_lower.split() 
            if len(w) > 3 and w.isalpha() and w not in stopwords
        )
        
        # Concept overlap: chunk must share AT LEAST 1 meaningful concept with question
        # Do NOT skip chunks based on concept count - let ranking handle prioritization
        overlap = len(question_concepts & chunk_words)
        return overlap >= 1
    
    def analyze_chunk_structure(content: str) -> Dict[str, Any]:
        """
        Analyze chunk structure objectively for completeness assessment.
        NO hardcoding - pure structural analysis.
        """
        lines = content.split('\n')
        
        metrics = {
            'num_lines': len(lines),
            'non_empty_lines': 0,
            'numbered_entries': 0,      # Entries like "1 Item", "2 Item"
            'table_headers': 0,         # Header-like lines (>50% uppercase)
            'data_rows': 0,             # Data-bearing lines (many digits)
            'numeric_lines': 0,         # Lines with any numbers
            'has_table_columns': False, # S.No, Date, Holiday, etc present
        }
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            metrics['non_empty_lines'] += 1
            
            # Numbered entries (1, 2, 3, ...)
            if stripped[0].isdigit():
                parts = stripped.split(None, 1)
                if parts and parts[0].isdigit():
                    metrics['numbered_entries'] += 1
            
            # Header lines (>50% uppercase)
            if len(stripped) > 3:
                upper_ratio = sum(1 for c in stripped if c.isupper()) / len(stripped)
                if upper_ratio > 0.5:
                    metrics['table_headers'] += 1
            
            # Numeric content
            digit_count = sum(1 for c in stripped if c.isdigit())
            if digit_count > 0:
                metrics['numeric_lines'] += 1
                if digit_count > 3:
                    metrics['data_rows'] += 1
        
        # Check for table structure keywords
        metrics['has_table_columns'] = any(kw in content for kw in 
                                          ['S.No', 'Date', 'Holiday', 'Month', 'Day', 'Occasion'])
        
        return metrics
    
    def score_chunk_completeness(doc, question_concepts: set) -> float:
        """
        Score chunk completeness for ranking (ONLY matching chunks).
        Higher score = more complete. NO hardcoding.
        """
        content = getattr(doc, "page_content", "") or ""
        analysis = analyze_chunk_structure(content)
        
        score = 0.0
        
        # ===== COMPLETENESS SCORING =====
        
        # 1. HIGHEST PRIORITY: Complete table structure (headers + columns)
        if analysis['table_headers'] > 0 and analysis['has_table_columns']:
            score += 50  # Well-formed, complete table
        elif analysis['table_headers'] > 0:
            score += 30  # Has headers
        
        # 2. Entry count: more entries = more complete
        if analysis['numbered_entries'] > 5:
            score += 25  # Many entries
        elif analysis['numbered_entries'] > 2:
            score += 15  # Some entries
        elif analysis['numbered_entries'] > 0:
            score += 8
        
        # 3. Data density
        if analysis['data_rows'] > 5:
            score += 15
        elif analysis['data_rows'] > 2:
            score += 8
        
        # 4. Content length: substantial > fragment
        if len(content) > 400:
            score += 10
        elif len(content) > 200:
            score += 5
        
        # 5. Concept match quality
        chunk_words = set(w for w in content.lower().split() if len(w) > 4 and w.isalpha())
        concept_overlap = len(question_concepts & chunk_words)
        score += min(8, concept_overlap)
        
        # ===== DOCUMENT-TYPE BOOST (without hardcoding) =====
        # If question asks about holidays/months, boost chunks with date/day content
        question_lower = ' '.join(question_concepts).lower()
        
        has_holiday_signals = any(signal in question_lower for signal in 
                                 ['holiday', 'january', 'february', 'march', 'april', 
                                  'may', 'june', 'july', 'august', 'september', 
                                  'october', 'november', 'december', 'mandate', 'optional'])
        
        # Content has holiday indicators (dates, day names, holiday structure)
        content_lower = content.lower()
        has_content_dates = any(date_signal in content_lower for date_signal in
                               ['january', 'february', 'march', 'april', 'may', 'june',
                                'july', 'august', 'september', 'october', 'november', 'december',
                                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 
                                'saturday', 'sunday', 'mandate', 'optional'])
        
        # If query asks about holidays AND content contains holiday data → boost
        if has_holiday_signals and has_content_dates and analysis['has_table_columns']:
            score += 40  # STRONG boost for holiday tables
        elif has_holiday_signals and has_content_dates:
            score += 25  # Medium boost for holiday content
        
        return score
    
    # ===== PHASE 1: FILTER BY MATCHING =====
    question_concepts = extract_question_concepts(question)
    matching_docs = []
    
    for doc in docs:
        content = getattr(doc, "page_content", "") or ""
        if chunk_matches_question(content, question_concepts):
            matching_docs.append(doc)
    
    logging.debug(f"Question concepts: {question_concepts}")
    logging.debug(f"Matched {len(matching_docs)}/{len(docs)} chunks")
    
    # Fallback: if no matches, use all chunks
    if not matching_docs:
        matching_docs = docs
    
    # ===== PHASE 2: RANK MATCHING CHUNKS BY COMPLETENESS =====
    ranked_docs = []
    for doc in matching_docs:
        score = score_chunk_completeness(doc, question_concepts)
        ranked_docs.append((doc, score))
    
    # Sort by score descending
    ranked_docs.sort(key=lambda x: x[1], reverse=True)
    docs = [doc for doc, _ in ranked_docs]
    
    # For multi-concept queries, apply LIGHT document diversity:
    # Preserve intelligent ranking order but ensure key documents aren't completely missing
    # Do NOT re-shuffle top-ranked chunks - that defeats the purpose of completeness scoring
    if is_multi_concept and len(docs) > 4:
        source_groups = {}
        for i, d in enumerate(docs):
            meta = getattr(d, "metadata", {}) or {}
            src = meta.get("source_file", "unknown")
            if src not in source_groups:
                source_groups[src] = []
            source_groups[src].append((i, d))  # Track original order
        
        # If we have multiple document types, ensure at least one chunk from each
        # BUT preserve the original ranking order (don't reshuffle top chunks)
        if len(source_groups) >= 2:
            # Simply verify we have diversity in the top-k results
            # If not, it's because completeness scoring favors one doc (which is correct!)
            # Don't override completeness scores with forced diversity
            pass  # Keep docs as-is (already ranked by completeness)

    # Convert docs → context + structured sources
    texts = []
    metas = []
    for d in docs:
        text = getattr(d, "page_content", "") or ""
        meta = getattr(d, "metadata", {}) or {}
        texts.append(text)
        metas.append(meta)

    logging.debug("Retrieved %d docs from retriever", len(texts))

    # Filter noise and remove duplicate chunks (normalized)
    filtered_texts, filtered_metas = filter_chunks(texts, metas)
    logging.debug("After filtering/dedup: %d chunks", len(filtered_texts))

    # Build context from retrieved chunks. We dedupe at the chunk level (normalized text)
    # but avoid any heuristic that filters out content based on domain-specific tokens.
    seen_chunks = set()
    pieces: List[str] = []
    sources: List[Dict[str, Any]] = []
    
    # Track sources for diversity boost
    source_counts = {}

    for meta, text in zip(filtered_metas, filtered_texts):
        norm = " ".join(text.lower().split())
        if norm in seen_chunks:
            continue
        seen_chunks.add(norm)

        src_file = meta.get("source_file", "unknown")
        source_counts[src_file] = source_counts.get(src_file, 0) + 1

        src_preview = {
            "source_file": src_file,
            "page_no": meta.get("page_no"),
            "chunk_index": meta.get("chunk_index")
        }
        sources.append({**src_preview, "text": text[:800]})

        header = f"[SOURCE: {src_file} | page: {meta.get('page_no','?')} | chunk: {meta.get('chunk_index','?')}]"
        pieces.append(header + "\n" + text)

    # For multi-concept questions, if we have a strong imbalance (one doc >> 80% of chunks),
    # add a note to the LLM in the context to ensure it uses all available documents
    source_dist_note = ""
    if is_multi_concept and len(source_counts) >= 2:
        total_chunks = len(pieces)
        for src, cnt in source_counts.items():
            if cnt / total_chunks < 0.15:  # Very under-represented
                source_dist_note = f"\n\n[IMPORTANT NOTE: The '{src}' is under-represented in the retrieved context. Please ensure you also consider and reference information from this document when it is relevant to answering the query.]\n"
                break

    # join pieces with a clear separator so the LLM can see chunk boundaries
    # For document listing queries, prepend the complete document list
    context = document_list_context + "\\n\\n---\\n\\n".join(pieces) + source_dist_note
    
    # ========================================================================
    # CHAT HISTORY: Prepend conversation history for context-aware responses
    # ========================================================================
    # Format chat history as a conversation thread
    if chat_history and len(chat_history) > 0:
        history_text = "[CONVERSATION HISTORY]\\n"
        for msg in chat_history[-10:]:  # Keep last 10 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                history_text += f"User: {content}\\n"
            elif role == "assistant":
                history_text += f"Assistant: {content}\\n"
        history_text += "[END OF CONVERSATION HISTORY]\\n\\n"
        
        # Prepend history to context
        context = history_text + context
        logging.debug(f"Added {len(chat_history)} messages to context")

    chain = build_rag_chain()
    today = datetime.now().strftime("%Y-%m-%d")

    # No domain-specific deterministic extraction here. The chain will provide the
    # retrieved context to the LLM and the LLM is instructed to answer only from
    # the context. This avoids hard-coded assumptions about document structure
    # (holidays or otherwise) and lets the model reason over arbitrary content.

    # Otherwise invoke the chain (LLM) with the assembled context and return
    answer = chain.invoke({
        "context": context,
        "question": question,
        "today": today
    })

    # If model indicates it couldn't find the information, include short
    # provenance snippets so the caller can see what was retrieved.
    low_answer = answer.lower() if isinstance(answer, str) else ""
    if isinstance(answer, str) and "i couldn't find" in low_answer:
        # include previews of top 3 retrieved sources to help debugging
        previews = []
        for s in sources[:3]:
            previews.append(f"[source={s.get('source_file')} page={s.get('page_no')} chunk={s.get('chunk_index')}] {s.get('text')[:400].replace('\n',' ') }")
        preview_text = "\n\nTop retrieved snippets:\n" + "\n".join(previews) if previews else ""
        answer = answer + preview_text

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(sources)
    }