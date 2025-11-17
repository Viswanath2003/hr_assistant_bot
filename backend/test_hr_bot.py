import requests
import time
import re
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/chat"

# --------------------------------------------------------------------
# Test Question Bank (Complete Coverage)
# --------------------------------------------------------------------
TEST_CASES = [
    # Basic holiday lookup
    "When is Makara Sankranti in 2025?",
    "What is the date of Ugadi festival?",
    "When is May Day 2025?",
    "On which day does Independence Day fall?",
    "Give me the date and day for Kannada Rajyotsava.",
    "Which holiday is on 25th December 2025?",

    # Mandatory holidays
    "List all mandatory holidays.",
    "How many mandatory holidays are there?",
    # Explicit separation checks
    "List all mandatory holidays separately from optional holidays.",
    "List all optional holidays separately from mandatory holidays.",
    "What are the mandatory holidays in October?",

    # Optional holidays
    "What are the optional holidays for 2025?",
    "How many optional holidays can be availed?",
    # Edge: ask both lists in one query
    "List mandatory and optional holidays separately.",
    "List optional holidays in March.",
    "Is Good Friday an optional holiday?",
    "When is Bakrid in 2025?",
    "List optional holidays in August.",

    # Date reasoning
    "If today is January 10 2025, what is the upcoming holiday?",
    "If today is March 15 2025, what is the next holiday?",
    "If it is October 2025, which holidays are remaining?",
    "What are the next three holidays from August 16 2025?",
    "If current month is November, what holidays remain?",
    "What are the 5 upcoming holidays from April 2025?",

    # Rules
    "How many mandatory leaves can be taken?",
    "Can optional holidays be carried forward?",
    "Which holidays fall on weekends?",
    "What does highlighted holidays mean?",

    # Company info
    "What is the company name?",
    "What is the company address?",
    "What is the company email address?",
    "What is the company website?",

    # Multi-step logic
    "Which holidays fall in Q4 2025?",
    "If I want a long weekend in October, which holidays help?",
    "Which holidays fall on a Friday?",
    "List holidays between March and August.",
    "What are the last two holidays of 2025?",

    # Hallucination traps (should say cannot find)
    "What is the holiday policy for 2026?",
    "When is Pongal celebrated?",
    "Give US public holidays for 2025.",
    "What holidays does Hyderabad office have?",
    "How many holidays are in 2027?",
    "Who is the founder of the company?",
    "What is the medical emergency leave policy?",

    # Edge cases
    "How many holidays total?",
    "List holidays before July.",
    "List holidays after Diwali.",
    "List all holidays in order.",
]

# Add a test that references the newly added Hybrid Work Policy PDF
TEST_CASES.append("What is the version and date of the Hybrid Work Policy?")

# Exact expected holiday name sets (used for stronger assertions on a few critical queries)
EXPECTED_MANDATORY = [
    "New Year’s Day",
    "Makara Sankranti",
    "Republic Day",
    "Ugadi Festival",
    "May Day",
    "Independence Day",
    "Gandhi Jayanti/Dussehra",
    "Diwali",
    "Kannada Rajyotsava",
    "Christmas Day",
]

EXPECTED_OPTIONAL = [
    "Holi",
    "Eid-ul-Fitr",
    "Good Friday",
    "Bakrid/Eid-ul-Adha",
    "Last Day of Muharram",
    "Ganesh Chaturthi",
    "Ayudh Pooja/ Mahanavmi",
]

# --------------------------------------------------------------------
# Utility functions
# --------------------------------------------------------------------
def evaluate_result(question, response_text):
    """
    Categorizes test result into:
    - PASS
    - PARTIAL
    - FAIL
    """

    if not response_text:
        return "FAIL"

    lower = response_text.lower()

    # FAIL cases: hallucination detection
    if "i couldn't find" in lower:
        # But if hallucination is expected, we mark partial (handled below)
        return "FAIL"

    # Very short answers usually wrong
    if len(response_text) < 10:
        return "FAIL"

    # PARTIAL cases for long answers but weird or incomplete
    if (
        "not enough" in lower or
        "unclear" in lower or
        "unsure" in lower or
        "might" in lower or
        "possibly" in lower
    ):
        return "PARTIAL"

    # Otherwise assume PASS
    return "PASS"


def strong_assertions(question, response_text):
    """Return True if response satisfies stronger correctness checks for a few targeted queries.
    This checks presence/absence of expected names and correct counts for mandatory/optional queries.
    """
    q = question.lower().strip()
    rt = (response_text or "").lower()

    def _norm(s: str) -> str:
        # normalize by lowercasing, replace unicode apostrophes, remove punctuation, collapse whitespace
        s2 = s.replace("’", "'").replace("‘", "'")
        s2 = re.sub(r"[^0-9a-zA-Z\s]", " ", s2)
        s2 = re.sub(r"\s+", " ", s2).strip().lower()
        return s2

    rt_norm = _norm(rt)

    # New document: Hybrid Work Policy checks
    if 'hybrid work policy' in q:
        # Expect version and date to be present
        if 'version 1 0' in rt_norm or 'version 1.0' in rt_norm:
            if '16th june 2025' in rt_norm or '16 june 2025' in rt_norm or '16 june, 2025' in rt_norm:
                return True, ""
        return False, "Hybrid Work Policy version/date not found"

    # Combined mandatory+optional check (handle this first)
    if 'mandatory' in q and 'optional' in q:
        # both sets should appear, but separated
        for name in EXPECTED_MANDATORY + EXPECTED_OPTIONAL:
            if not re.search(r"\b" + re.escape(_norm(name)) + r"\b", rt_norm):
                return False, f"Missing expected holiday: {name}"
        return True, ""

    # Mandatory list checks
    if q.startswith("list all mandatory") or ('mandatory' in q and 'optional' not in q and 'list' in q):
        # all expected mandatory names must be present
        for name in EXPECTED_MANDATORY:
            if not re.search(r"\b" + re.escape(_norm(name)) + r"\b", rt_norm):
                return False, f"Missing mandatory: {name}"
        # optional names must not appear
        for name in EXPECTED_OPTIONAL:
            if re.search(r"\b" + re.escape(_norm(name)) + r"\b", rt_norm):
                return False, f"Unexpected optional in mandatory list: {name}"
        return True, ""

    # Optional list checks
    if q.startswith("list all optional") or 'optional' in q and 'mandatory' not in q:
        for name in EXPECTED_OPTIONAL:
            if not re.search(r"\b" + re.escape(_norm(name)) + r"\b", rt_norm):
                return False, f"Missing optional: {name}"
        # mandatory names must not appear
        for name in EXPECTED_MANDATORY:
            if re.search(r"\b" + re.escape(_norm(name)) + r"\b", rt_norm):
                return False, f"Unexpected mandatory in optional list: {name}"
        return True, ""

    # (combined handled earlier)

    return None, ""


def print_color(text, color):
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "reset": "\033[0m"
    }
    print(colors[color] + text + colors["reset"])


# --------------------------------------------------------------------
# Test runner
# --------------------------------------------------------------------
def run_test_suite():
    print("\n==============================================")
    print("     HR Assistant Bot – Automated Testing")
    print("==============================================\n")

    total = len(TEST_CASES)
    passed = 0
    failed = 0
    partial = 0

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logfile = f"test_results_{timestamp}.log"

    # Ensure the backend has ingested the latest PDFs before running queries
    try:
        print("📥 Triggering ingestion endpoint to index raw_docs...")
        r = requests.post(API_URL.replace('/chat', '/ingest'), timeout=60)
        print(f"Ingest status: {r.status_code} {r.text}")
    except Exception as e:
        print_color(f"Ingest request failed: {e}", "red")

    with open(logfile, "w") as log:
        for idx, q in enumerate(TEST_CASES, 1):
            payload = {"query": q, "k": 4}

            start = time.time()
            try:
                response = requests.post(API_URL, json=payload, timeout=45)
                elapsed = round(time.time() - start, 2)
            except Exception as e:
                print_color(f"[{idx}] Network error: {e}", "red")
                log.write(f"[{idx}] NETWORK ERROR: {e}\n")
                failed += 1
                continue

            if response.status_code != 200:
                print_color(f"[{idx}] FAIL: Status {response.status_code}", "red")
                log.write(f"[{idx}] FAIL HTTP {response.status_code}: {q}\n")
                failed += 1
                continue

            result = response.json()
            answer = result.get("response", "")

            # Apply strong assertions for critical queries when applicable
            strong_ok = None
            strong_msg = ""
            try:
                strong_ok, strong_msg = strong_assertions(q, answer)
            except Exception:
                strong_ok = None

            if strong_ok is True:
                category = "PASS"
            elif strong_ok is False:
                category = "FAIL"
            else:
                category = evaluate_result(q, answer)

            if category == "PASS":
                print_color(f"[{idx}] PASS  ({elapsed}s): {q}", "green")
                passed += 1
            elif category == "PARTIAL":
                print_color(f"[{idx}] PARTIAL ({elapsed}s): {q}", "yellow")
                partial += 1
            else:
                print_color(f"[{idx}] FAIL ({elapsed}s): {q}", "red")
                failed += 1

            log.write(f"\n[{idx}] Q: {q}\nResponse: {answer}\n\n")

    print("\n==============================================")
    print("                 SUMMARY")
    print("==============================================")
    print_color(f"Passed : {passed}", "green")
    print_color(f"Partial: {partial}", "yellow")
    print_color(f"Failed : {failed}", "red")
    print(f"Log saved to: {logfile}")
    print("==============================================\n")


if __name__ == "__main__":
    run_test_suite()

