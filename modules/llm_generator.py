def generate_response(prompt):

    prompt = prompt.lower()

    if "ai ethics" in prompt:
        return "AI ethics focuses on fairness, transparency, accountability, and reducing bias in AI systems."

    elif "machine learning" in prompt:
        return "Machine learning enables systems to learn patterns from data and improve automatically."

    elif "cybersecurity" in prompt:
        return "Cybersecurity protects systems and networks from attacks and unauthorized access."

    elif "python" in prompt:
        return "Python is a popular programming language widely used in AI and web development."

    elif "flask" in prompt:
        return "Flask is a lightweight Python web framework used for backend development."

    else:
        return f"Generated response for: {prompt}"