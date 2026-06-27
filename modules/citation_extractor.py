"""
citation_extractor.py

Extracts candidate academic citations from an AI-generated response.

Two citation styles are handled:
  1. Inline author-year citations, e.g. (Smith, 2021) or (Smith & Lee, 2021)
  2. Reference-list style entries, e.g.
     "1. Smith, J. (2021). Deep learning for citation analysis. Journal of AI Research."

Each extracted citation is returned as a dict:
{
    "raw": str,            # original matched text
    "authors": str | None, # best-effort author string
    "year": str | None,
    "title": str | None,   # best-effort title guess (reference-list style only)
    "style": "inline" | "reference"
}

This is intentionally a heuristic, regex + spaCy NER based extractor (matches the
"Citation Extraction (Regex / NLP)" stage in the project's architecture diagram).
It is not meant to be a perfect bibliographic parser -- it just needs to produce
candidates good enough to hand off to citation_verifier.py.
"""

import re

try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None


# ---- Regex patterns -------------------------------------------------------

INLINE_PATTERN = re.compile(
    r"\(([A-Z][A-Za-z\-']+(?:\s(?:&|and)\s[A-Z][A-Za-z\-']+|\set al\.)?),\s*(\d{4}[a-z]?)\)"
)

REFERENCE_PATTERN = re.compile(
    r"""
    ^\s*(?:\d+[\.\)]\s*)?                     
    (?P<authors>[A-Z][A-Za-z\-'.,&\s]{2,80}?)  
    \s*\(\s*(?P<year>\d{4}[a-z]?)\s*\)         
    \.?\s*
    (?P<title>[^.]{5,200})\.                  
    """,
    re.VERBOSE | re.MULTILINE,
)


def _extract_inline(text):
    citations = []
    for match in INLINE_PATTERN.finditer(text):
        authors, year = match.group(1), match.group(2)
        citations.append({
            "raw": match.group(0),
            "authors": authors,
            "year": year,
            "title": None,
            "style": "inline",
        })
    return citations


def _extract_reference_list(text):
    citations = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        match = REFERENCE_PATTERN.match(line)
        if match:
            citations.append({
                "raw": line,
                "authors": match.group("authors").strip().rstrip(","),
                "year": match.group("year"),
                "title": match.group("title").strip(),
                "style": "reference",
            })
    return citations


def _extract_with_spacy(text):
    if _NLP is None:
        return []
    doc = _NLP(text)
    persons = [(ent.text, ent.start_char, ent.end_char) for ent in doc.ents if ent.label_ == "PERSON"]
    dates = [(ent.text, ent.start_char, ent.end_char) for ent in doc.ents if ent.label_ == "DATE"]

    found = []
    for p_text, p_start, p_end in persons:
        for d_text, d_start, d_end in dates:
            if abs(d_start - p_end) <= 40 or abs(p_start - d_end) <= 40:
                year_match = re.search(r"\b(19|20)\d{2}\b", d_text)
                if year_match:
                    found.append({
                        "raw": f"{p_text} ... {d_text}",
                        "authors": p_text,
                        "year": year_match.group(0),
                        "title": None,
                        "style": "spacy_ner",
                    })
    return found


def _normalize(text):
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def extract_citations(text, use_spacy_fallback=False):
    """
    Main entry point. Returns a deduplicated, cleaned list of citation candidates.
    """
    if not text:
        return []

    citations = []
    citations.extend(_extract_reference_list(text))
    citations.extend(_extract_inline(text))
    if use_spacy_fallback:
        citations.extend(_extract_with_spacy(text))

    style_priority = {"reference": 0, "inline": 1, "spacy_ner": 2}
    deduped = {}
    removed = []

    for c in citations:
        authors = _normalize(c.get("authors"))
        title = _normalize(c.get("title"))
        year = (c.get("year") or "").strip()

        # Noise filtering
        if not authors or not year:
            removed.append(c)
            continue
        if len(title) > 0 and len(title) < 5:
            removed.append(c)
            continue
        if year.isdigit() and (int(year) < 1800 or int(year) > 2100):
            removed.append(c)
            continue

        key = (authors, title, year)
        if key not in deduped or style_priority[c["style"]] < style_priority[deduped[key]["style"]]:
            deduped[key] = c
        else:
            removed.append(c)

    if removed:
        print(f"[LOG] Removed {len(removed)} duplicate/noisy citations")

    return list(deduped.values())


if __name__ == "__main__":
    sample = """
    Recent work has shown promising results (Xu, 2026) in this area.
    Several studies (Naser, 2026) and (Pan & Wong, 2025) support this claim.

    References:
    1. Xu, Z. (2026). GHOSTCITE: A large-scale analysis of citation validity. Journal of AI Safety.
    2. Naser, M. (2026). How LLMs cite and why it matters. AI Research Quarterly.
    3. Fakeauthor, Q. (2099). A completely made up paper about nothing. Nonexistent Journal.
    4. Xu, Z. (2026). GHOSTCITE: A large-scale analysis of citation validity. Journal of AI Safety.
    """
    for c in extract_citations(sample, use_spacy_fallback=True):
        print(c)
