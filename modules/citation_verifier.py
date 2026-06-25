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
    # Fallback if rapidfuzz isn't installed: pip install rapidfuzz --break-system-packages
    from difflib import SequenceMatcher
    def _similarity(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100


SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_URL = "https://api.crossref.org/works"

VERIFICATION_THRESHOLD = 70   # title similarity % required to count as a match
REQUEST_TIMEOUT = 6           # seconds, keep short so one slow API doesn't stall the pipeline


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
        # small bonus if the candidate author surname appears in the result's author list
        if candidate_author:
            surname = candidate_author.split()[-1].lower().rstrip(",")
            if any(surname in a.lower() for a in authors):
                score = min(100, score + 5)
        if score > best["score"]:
            best = {"score": round(score, 1), "matched_title": title, "source": source_name}
    return best


def verify_citation(citation, delay=0.0):
    """
    Verify a single citation dict (as produced by citation_extractor.extract_citations).
    Returns the citation dict augmented with verification results.
    """
    query_text = citation.get("title") or citation.get("raw") or ""
    if not query_text.strip():
        citation.update({"status": "unverifiable", "confidence": 0, "matched_title": None, "source": None})
        return citation

    if delay:
        time.sleep(delay)  # be polite to free-tier APIs if verifying many citations in a loop

    ss_results = _query_semantic_scholar(query_text)
    cr_results = _query_crossref(query_text)

    if not ss_results and not cr_results:
        # Both APIs unreachable/timed out -- don't count this as a confirmed hallucination
        citation.update({"status": "unverifiable", "confidence": 0, "matched_title": None, "source": None})
        return citation

    candidates = [
        _best_match(citation.get("title"), citation.get("authors"), ss_results, "Semantic Scholar"),
        _best_match(citation.get("title"), citation.get("authors"), cr_results, "CrossRef"),
    ]
    best = max(candidates, key=lambda c: c["score"])

    citation.update({
        "status": "verified" if best["score"] >= VERIFICATION_THRESHOLD else "hallucinated",
        "confidence": best["score"],
        "matched_title": best["matched_title"],
        "source": best["source"] if best["score"] >= VERIFICATION_THRESHOLD else None,
    })
    return citation


def verify_citations(citations, delay_between_calls=0.2):
    """
    Verify a list of citation dicts. Returns (results, summary).

    summary = {
        "total": int,
        "verified": int,
        "hallucinated": int,
        "unverifiable": int,
        "verification_rate": float  # verified / (verified + hallucinated), ignores unverifiable
    }
    """
    results = [verify_citation(c, delay=delay_between_calls) for c in citations]

    total = len(results)
    verified = sum(1 for r in results if r["status"] == "verified")
    hallucinated = sum(1 for r in results if r["status"] == "hallucinated")
    unverifiable = sum(1 for r in results if r["status"] == "unverifiable")

    decidable = verified + hallucinated
    verification_rate = round(verified / decidable, 3) if decidable else None

    summary = {
        "total": total,
        "verified": verified,
        "hallucinated": hallucinated,
        "unverifiable": unverifiable,
        "verification_rate": verification_rate,
    }
    return results, summary


if __name__ == "__main__":
    from citation_extractor import extract_citations

    sample = """
    References:
    1. Vaswani, A. (2017). Attention is all you need. NeurIPS.
    2. Fakeauthor, Q. (2099). A completely made up paper about nothing. Nonexistent Journal.
    """
    citations = extract_citations(sample)
    results, summary = verify_citations(citations)
    for r in results:
        print(r)
    print("Summary:", summary)
