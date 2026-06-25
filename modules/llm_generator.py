def generate_response(prompt):
    prompt_lower = prompt.lower()

    if "ai ethics" in prompt_lower:
        return """AI ethics focuses on fairness, transparency, accountability, and bias reduction in AI systems.
Recent work has highlighted these concerns significantly (Jobin, 2019).

References:
1. Jobin, A. (2019). The global landscape of AI ethics guidelines. Nature Machine Intelligence.
2. Floridi, L. (2019). An ethical framework for a good AI society. Minds and Machines.
3. Bender, E. (2021). On the dangers of stochastic parrots. ACM FAccT Conference."""

    elif "machine learning" in prompt_lower:
        return """Machine learning enables systems to learn patterns from data and improve automatically.
Deep learning has revolutionized the field (LeCun, 2015), and transformers have become dominant (Vaswani, 2017).

References:
1. LeCun, Y. (2015). Deep learning. Nature.
2. Vaswani, A. (2017). Attention is all you need. NeurIPS.
3. Fakeauthor, X. (2099). Quantum neural networks for infinite learning. Nonexistent Journal."""

    elif "cybersecurity" in prompt_lower:
        return """Cybersecurity protects systems and networks from attacks and unauthorized access.
Intrusion detection using ML has shown strong results (Buczak, 2016).

References:
1. Buczak, A. (2016). A survey of data mining and machine learning methods for cybersecurity. IEEE Communications Surveys.
2. Sommer, R. (2010). Outside the closed world: On using machine learning for network intrusion detection. IEEE Symposium on Security and Privacy.
3. Ghostauthor, Z. (2087). AI-powered zero-day exploit prevention. Imaginary Security Review."""

    elif "prompt injection" in prompt_lower:
        return """Prompt injection attacks manipulate LLMs by embedding malicious instructions in user input.
Detection methods have improved significantly (Perez, 2022).

References:
1. Perez, F. (2022). Ignore previous prompt: Attack techniques for language models. NeurIPS Workshop.
2. Greshake, K. (2023). Not what you signed up for: Compromising real-world LLM-integrated applications. USENIX Security.
3. Fakeresearcher, Q. (2099). Perfect prompt injection defense using magic. Journal of Impossible Security."""

    elif "hallucination" in prompt_lower:
        return """LLM hallucination refers to the generation of factually incorrect or fabricated content.
Citation hallucination is a particularly serious problem in academic contexts (Ji, 2023).

References:
1. Ji, Z. (2023). Survey of hallucination in natural language generation. ACM Computing Surveys.
2. Maynez, J. (2020). On faithfulness and factuality in abstractive summarization. ACL.
3. Fakeauthor, B. (2099). Eliminating hallucinations with positive thinking. Nonexistent AI Journal."""

    elif "python" in prompt_lower:
        return """Python is a popular programming language widely used in AI and web development.
Its simplicity and rich ecosystem make it the dominant language for data science (Oliphant, 2007).

References:
1. Oliphant, T. (2007). Python for scientific computing. Computing in Science and Engineering.
2. Pedregosa, F. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research.
3. Fakedev, Y. (2099). Python runs faster than C with this one trick. Nonexistent Computing Journal."""

    else:
        return f"No specific response available for: {prompt}. Please try asking about AI ethics, machine learning, cybersecurity, prompt injection, hallucination, or Python."