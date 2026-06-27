"""
citation_verifier.py

Takes citation candidates from citation_extractor.py and checks whether they
correspond to real academic publications, using:
  - Semantic Scholar API (https://api.semanticscholar.org)
  - CrossRef API (https://api.crossref.org)

A citation is marked "verified" if either API returns a result whose title
and first-author surname are a close fuzzy match to the candidate. Anything
that doesn't clear the threshold is marked "hallucinated" (or "unverifiable"
if both APIs failed/timed out, which is reported separately so it doesn't
get counted as a confirmed hallucination).

Usage:
    from modules.citation_extractor import extract_citations
    from modules.citation_verifier import verify_citations

    citations = extract_citations(llm_response_text)
    results = verify_citations(citations)
"""

import time
import requests

try:
    from rapidfuzz import fuzz
    def _similarity(a, b):
        return fuzz.token_sort_ratio(a, b)
except ImportError:
    # Fallback if rapidfuzz isn't installed
    from difflib import SequenceMatcher
    def _similarity(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100


SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_URL = "https://api.crossref.org/works"

VERIFICATION_THRESHOLD = 78   # threshold to reduce false positives
PARTIAL_THRESHOLD = 50        # threshold for partially valid
REQUEST_TIMEOUT = 6           # seconds


def _query_semantic_scholar(query_text):
    """Returns list of (title, authors_list) from Semantic Scholar, or [] on failure."""
    try:
        resp = requests.get(
            SEMANTIC_SCHOLAR_URL,
            params={"query": query_text, "limit": 3, "fields": "title,authors,year"},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [
            (item.get("title", ""), [a.get("name", "") for a in item.get("authors", [])])
            for item in data.get("data", [])
        ]
    except requests.RequestException:
        return []


def _query_crossref(query_text):
    """Returns list of (title, authors_list) from CrossRef, or [] on failure."""
    try:
        resp = requests.get(
            CROSSREF_URL,
            params={"query.bibliographic": query_text, "rows": 3},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        items = data.get("message", {}).get("items", [])
        results = []
        for item in items:
            title = (item.get("title") or [""])[0]
            authors = [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in item.get("author", [])
            ] if item.get("author") else []
            results.append((title, authors))
        return results
    except requests.RequestException:
        return []


def _best_match(candidate_title, candidate_author, results, source_name):
    """Given a list of (title, authors) results from one API, find the best fuzzy match."""
    best = {"score": 0, "matched_title": None, "source": source_name}
    for title, authors in results:
        if not title:
            continue
        score = _similarity(candidate_title or "", title)

        # bonus if author matches
        if candidate_author:
            for a in authors:
                if _similarity(candidate_author, a) > 70:
                    score = min(100, score + 10)

        if score > best["score"]:
            best = {"score": round(score, 1), "matched_title": title, "source": source_name}
    return best


def verify_citation(citation, delay=0.0):
    """
    Verify a single citation dict.
    Returns the citation dict augmented with verification results.
    """
    query_text = citation.get("title") or citation.get("raw") or ""
    if not query_text.strip():
        citation.update({"status": "unverifiable", "confidence": 0, "matched_title": None, "source": None})
        print(f"[LOG] Citation unverifiable (empty query): {citation}")
        return citation

    if delay:
        time.sleep(delay)

    ss_results = _query_semantic_scholar(query_text)
    cr_results = _query_crossref(query_text)

    if not ss_results and not cr_results:
        citation.update({"status": "unverifiable", "confidence": 0, "matched_title": None, "source": None})
        print(f"[LOG] Citation unverifiable (API failure): {citation}")
        return citation

    candidates = [
        _best_match(citation.get("title"), citation.get("authors"), ss_results, "Semantic Scholar"),
        _best_match(citation.get("title"), citation.get("authors"), cr_results, "CrossRef"),
    ]
    best = max(candidates, key=lambda c: c["score"])

    # Three-way classification
    if best["score"] >= VERIFICATION_THRESHOLD:
        status = "valid"
    elif best["score"] >= PARTIAL_THRESHOLD:
        status = "partially_valid"
    else:
        status = "hallucinated"

    citation.update({
        "status": status,
        "confidence": best["score"],
        "matched_title": best["matched_title"],
        "source": best["source"] if status != "hallucinated" else None,
    })

    print(f"[LOG] Citation checked: title='{citation.get('title')}', "
          f"status={citation['status']}, confidence={citation['confidence']}, "
          f"source={citation['source']}")
    return citation


def verify_citations(citations, delay_between_calls=0.2):
    """
    Verify a list of citation dicts. Returns (results, summary).
    """
    results = [verify_citation(c, delay=delay_between_calls) for c in citations]

    total = len(results)
    valid = sum(1 for r in results if r["status"] == "valid")
    partial = sum(1 for r in results if r["status"] == "partially_valid")
    hallucinated = sum(1 for r in results if r["status"] == "hallucinated")
    unverifiable = sum(1 for r in results if r["status"] == "unverifiable")

    summary = {
        "total": total,
        "valid": valid,
        "partially_valid": partial,
        "hallucinated": hallucinated,
        "unverifiable": unverifiable,
    }
    print(f"[LOG] Verification summary: {summary}")
    return results, summary


if __name__ == "__main__":
    from citation_extractor import extract_citations

    sample = """
    References:
    1. Vaswani, A. (2017). Attention is all you need. NeurIPS.
    2. Fakeauthor, Q. (2099). A completely made up paper about nothing. Nonexistent Journal.
    3. Title mismatch example.
    """
    citations = extract_citations(sample)
    results, summary = verify_citations(citations)
    for r in results:
        print(r)
    print("Summary:", summary)
