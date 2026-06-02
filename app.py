from flask import *

from modules.llm_generator import generate_response
from modules.security import detect_prompt_injection

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():

    response = ""

    risk = ""

    if request.method == "POST":

        prompt = request.form["prompt"]

        # Get AI-based risk score
        risk_score = detect_prompt_injection(prompt)

        # Convert score into labels
        if risk_score < 30:

            risk = "LOW"

        elif risk_score < 70:

            risk = "MEDIUM"

        else:

            risk = "HIGH"

        # Risk-based response control
        if risk == "HIGH":

            response = "Unsafe prompt detected. Request fully blocked due to high-risk content."

        elif risk == "MEDIUM":

            response = "Caution: Potentially unsafe or manipulative prompt detected. Limited response mode activated."

        else:

            response = generate_response(prompt)

    return render_template(
        "index.html",
        response=response,
        risk=risk
    )

if __name__ == "__main__":

    app.run(debug=True)