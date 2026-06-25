from flask import *
from modules.llm_generator import generate_response
from modules.security import detect_prompt_injection
from modules.citation_extractor import extract_citations
from modules.citation_verifier import verify_citations
from modules.safety_score import calculate_safety_score

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    response = ""
    risk = ""
    citations = []
    citation_summary = {}
    safety = {}

    if request.method == "POST":
        prompt = request.form["prompt"]

        # Step 1: Prompt injection detection
        risk_score = detect_prompt_injection(prompt)
        if risk_score < 40:
            risk = "LOW"
        elif risk_score < 75:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        # Step 2: Generate response
        if risk == "HIGH":
            response = "Unsafe prompt detected. Request fully blocked due to high-risk content."
        elif risk == "MEDIUM":
            response = "Caution: Potentially unsafe prompt detected. Limited response mode activated."
        else:
            response = generate_response(prompt)
            # Step 3: Extract and verify citations
            extracted = extract_citations(response)
            citations, citation_summary = verify_citations(extracted)

        # Step 4: Calculate safety score
        safety = calculate_safety_score(risk_score, citation_summary)

    return render_template(
        "index.html",
        response=response,
        risk=risk,
        citations=citations,
        citation_summary=citation_summary,
        safety=safety
    )

if __name__ == "__main__":
    app.run(debug=True)