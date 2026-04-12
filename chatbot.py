import json
import os
import random

import requests
from dotenv import load_dotenv

# ==============================
# LOAD ENV VARIABLES
# ==============================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODELS = [
    model.strip()
    for model in os.getenv(
        "GEMINI_MODELS",
        "gemini-2.5-flash,gemini-2.0-flash,gemini-1.5-flash",
    ).split(",")
    if model.strip()
]

# Debug check
print("API KEY LOADED:", "YES" if GEMINI_API_KEY else "NO")

# ==============================
# LOAD DATA
# ==============================
with open("data.json", "r") as f:
    data = json.load(f)


# ==============================
# FIND EXPERIMENT
# ==============================
def find_experiment(user_input):
    user_input = user_input.lower().strip()

    best_match = None
    max_score = 0

    for key, exp in data.items():
        title = exp["title"].lower()
        score = 0

        if user_input in title:
            score += 5

        for word in user_input.split():
            if word in title:
                score += 2

        for keyword in exp.get("keywords", []):
            if keyword.lower() in user_input:
                score += 3

        if score > max_score:
            max_score = score
            best_match = key

    return best_match


# ==============================
# INTENT DETECTION
# ==============================
def detect_intent(user_input):
    user_input = user_input.lower()

    if "aim" in user_input:
        return "aim"
    elif "theory" in user_input or "explain" in user_input:
        return "theory"
    elif "procedure" in user_input or "steps" in user_input:
        return "procedure"
    elif "component" in user_input:
        return "components"
    elif "output" in user_input or "result" in user_input:
        return "output"
    elif "viva" in user_input:
        return "viva"
    elif "connect" in user_input or "connection" in user_input:
        return "connection"
    elif "diagram" in user_input or "circuit" in user_input:
        return "diagram"
    elif "graph" in user_input:
        return "graph"
    else:
        return "full"


# ==============================
# GEMINI API CALL
# ==============================
def get_gemini_response(user_input):
    if not GEMINI_API_KEY:
        return "API key not loaded. Check .env file."

    prompt = f"""
You are an Electronics Lab Assistant helping engineering students.

Rules:
- Answer clearly and simply
- Focus only on electronics experiments
- Use bullet points
- Keep answers short

Question:
{user_input}
"""

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    last_error = None

    try:
        for model_name in GEMINI_MODELS:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_name}:generateContent?key={GEMINI_API_KEY}"
            )
            response = requests.post(url, json=payload, timeout=30)

            print(f"\nMODEL: {model_name}")
            print("STATUS:", response.status_code)
            print("RESPONSE:", response.text)

            try:
                result = response.json()
            except ValueError:
                result = {}

            if response.status_code == 200 and "candidates" in result:
                return result["candidates"][0]["content"]["parts"][0]["text"]

            last_error = result.get("error", {}).get("message", response.text)

            if response.status_code == 404:
                continue

            return f"AI failed: {last_error}"

        return f"AI failed: {last_error or 'No working Gemini model found.'}"

    except Exception as e:
        return f"Exception: {str(e)}"


# ==============================
# MAIN CHATBOT
# ==============================
def chatbot(user_input):
    user_input = user_input.lower().strip()

    exp_key = find_experiment(user_input)

    if not exp_key:
        ai_response = get_gemini_response(user_input)

        return {
            "text": ai_response,
            "image": None,
            "graph": None,
            "pdf": None,
        }

    exp = data[exp_key]
    intent = detect_intent(user_input)

    if intent == "aim":
        return {"text": f"Aim: {exp['aim']}", "image": None, "graph": None, "pdf": None}

    elif intent == "theory":
        return {"text": f"Theory: {exp['theory']}", "image": None, "graph": None, "pdf": None}

    elif intent == "components":
        return {"text": "Components: " + ", ".join(exp["components"]), "image": None, "graph": None, "pdf": None}

    elif intent == "procedure":
        steps = "\n".join([f"{i+1}. {step}" for i, step in enumerate(exp["procedure"])])
        return {"text": f"Procedure:\n{steps}", "image": None, "graph": None, "pdf": None}

    elif intent == "output":
        return {"text": f"Output: {exp['result']}", "image": None, "graph": exp.get("graph"), "pdf": None}

    elif intent == "viva":
        if "viva" in exp:
            return {"text": "Viva Question: " + random.choice(exp["viva"]), "image": None, "graph": None, "pdf": None}
        else:
            return {"text": "No viva questions available.", "image": None, "graph": None, "pdf": None}

    elif intent == "connection":
        if "connections" in exp:
            for comp, desc in exp["connections"].items():
                if comp in user_input:
                    return {"text": desc, "image": None, "graph": None, "pdf": None}

        return {"text": "Specify component (resistor, diode, etc.)", "image": None, "graph": None, "pdf": None}

    elif intent == "diagram":
        return {"text": f"Circuit diagram for {exp['title']}", "image": exp.get("image"), "graph": None, "pdf": None}

    elif intent == "graph":
        return {"text": f"Graph for {exp['title']}", "image": None, "graph": exp.get("graph"), "pdf": None}

    else:
        full_text = f"""
Title: {exp['title']}

Aim: {exp['aim']}

Theory: {exp['theory']}

Components: {', '.join(exp['components'])}

Procedure:
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(exp['procedure'])])}

Result: {exp['result']}
"""
        return {
            "text": full_text,
            "image": exp.get("image"),
            "graph": exp.get("graph"),
            "pdf": exp.get("pdf"),
        }


# ==============================
# TEST MODE
# ==============================
if __name__ == "__main__":
    while True:
        user = input("\nYou: ")
        response = chatbot(user)
        print("\nBot:", response["text"])
