"""
safety_score.py

Combines prompt injection risk and citation verification results
into a single Safety Score (0-100) and a final verdict.

Score breakdown:
  - 40% based on prompt risk (from security.py)
  - 60% based on citation verification rate (from citation_verifier.py)

Final verdict:
  0  - 40  → HIGH RISK
  41 - 70  → MEDIUM RISK
  71 - 100 → LOW RISK (SAFE)
"""


def calculate_safety_score(risk_score, citation_summary):
    """
    Parameters:
        risk_score      : int 0-100 from detect_prompt_injection()
        citation_summary: dict from verify_citations()

    Returns:
        dict with score, verdict, breakdown
    """

    # Prompt component — invert risk (low risk = high safety)
    prompt_safety = 100 - risk_score
    prompt_component = prompt_safety * 0.4

    # Citation component
    verification_rate = citation_summary.get("verification_rate")
    total = citation_summary.get("total", 0)

    if total == 0 or verification_rate is None:
        # No citations found — neutral, don't penalise
        citation_component = 50 * 0.6
        citation_note = "No citations found in response."
    else:
        citation_component = verification_rate * 100 * 0.6
        verified = citation_summary.get("verified", 0)
        hallucinated = citation_summary.get("hallucinated", 0)
        citation_note = f"{verified} verified, {hallucinated} hallucinated out of {total} citations."

    # Final score
    final_score = round(prompt_component + citation_component, 1)

    # Verdict
    if final_score >= 71:
        verdict = "SAFE"
        color = "low"
    elif final_score >= 41:
        verdict = "MEDIUM RISK"
        color = "medium"
    else:
        verdict = "HIGH RISK"
        color = "high"

    return {
        "score": final_score,
        "verdict": verdict,
        "color": color,
        "prompt_component": round(prompt_component, 1),
        "citation_component": round(citation_component, 1),
        "citation_note": citation_note,
    }


if __name__ == "__main__":
    # Quick test
    test_summary = {
        "total": 3,
        "verified": 2,
        "hallucinated": 1,
        "unverifiable": 0,
        "verification_rate": 0.667,
    }
    result = calculate_safety_score(risk_score=25, citation_summary=test_summary)
    print(result)