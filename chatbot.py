import json
import os
import re
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


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

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "for", "from",
    "how", "if", "in", "is", "it", "of", "on", "or", "the", "to", "what",
    "when", "where", "which", "why", "with", "you", "your", "can", "does",
    "this", "that", "explain", "tell", "me", "about", "show", "give",
}


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def keyword_tokens(text: str) -> List[str]:
    return [
        token for token in normalize_text(text).split()
        if len(token) > 2 and token not in STOP_WORDS
    ]


def experiment_aliases(exp_key: str, exp: Dict[str, Any]) -> List[str]:
    aliases = [exp_key, exp.get("title", "")]
    aliases.extend(exp.get("keywords", []))
    return [normalize_text(item) for item in aliases if item]


def find_experiment(user_input: str = "", selected_experiment: Optional[str] = None) -> Optional[str]:
    preferred = normalize_text(selected_experiment or "")
    query = normalize_text(user_input)

    if preferred:
        for key, exp in data.items():
            if preferred in experiment_aliases(key, exp):
                return key

        for key, exp in data.items():
            title = normalize_text(exp.get("title", ""))
            if preferred == title or preferred == normalize_text(key):
                return key

    if not query:
        return None

    best_match = None
    best_score = 0

    for key, exp in data.items():
        score = 0
        aliases = experiment_aliases(key, exp)

        if query in aliases:
            return key

        for alias in aliases:
            if alias and alias in query:
                score += 6

        title_tokens = set(keyword_tokens(exp.get("title", "")))
        query_tokens = set(keyword_tokens(query))
        score += len(title_tokens & query_tokens) * 2

        if score > best_score:
            best_score = score
            best_match = key

    return best_match if best_score >= 3 else None


def is_experiment_lookup(user_input: str, exp: Dict[str, Any]) -> bool:
    normalized_input = normalize_text(user_input)
    title = normalize_text(exp.get("title", ""))

    direct_lookup_phrases = {
        "show experiment",
        "show details",
        "show full details",
        "full details",
        "experiment details",
        "details",
    }

    if normalized_input == title:
        return True

    if normalized_input in direct_lookup_phrases:
        return True

    if normalized_input in {f"show {title}", f"details of {title}", f"show {title} details"}:
        return True

    return False


def detect_intent(user_input: str, mode: Optional[str] = None) -> str:
    if mode:
        return mode

    normalized = normalize_text(user_input)

    if "viva" in normalized:
        return "viva"
    if "aim" in normalized:
        return "aim"
    if "theory" in normalized:
        return "theory"
    if "procedure" in normalized or "steps" in normalized:
        return "procedure"
    if "apparatus" in normalized or "component" in normalized:
        return "apparatus"
    if (
        "result" in normalized
        or normalized.startswith("show output")
        or normalized.startswith("show result")
        or normalized.startswith("output of")
        or normalized.startswith("result of")
    ):
        return "result"
    if "diagram" in normalized or "circuit" in normalized:
        return "diagram"
    if "graph" in normalized:
        return "graph"
    return "doubt"


def build_experiment_context(exp: Dict[str, Any]) -> str:
    apparatus = ", ".join(exp.get("components", []))
    procedure = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(exp.get("procedure", []))
    )
    return (
        f"Experiment Title: {exp.get('title', '')}\n"
        f"Aim: {exp.get('aim', '')}\n"
        f"Apparatus: {apparatus}\n"
        f"Theory: {exp.get('theory', '')}\n"
        f"Procedure:\n{procedure}\n"
        f"Result: {exp.get('result', '')}"
    )


def format_experiment_details(exp: Dict[str, Any]) -> Dict[str, Any]:
    apparatus = ", ".join(exp.get("components", []))
    procedure = "\n".join(
        f"{index + 1}. {step}" for index, step in enumerate(exp.get("procedure", []))
    )
    text = (
        f"Title: {exp.get('title', '')}\n\n"
        f"Aim: {exp.get('aim', '')}\n\n"
        f"Apparatus: {apparatus}\n\n"
        f"Theory: {exp.get('theory', '')}\n\n"
        f"Procedure:\n{procedure}\n\n"
        f"Result: {exp.get('result', '')}"
    )
    return {
        "text": text,
        "image": exp.get("image"),
        "graph": exp.get("graph"),
        "pdf": exp.get("pdf"),
    }


def call_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "AI service is unavailable right now."

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    last_error = None

    try:
        for model_name in GEMINI_MODELS:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model_name}:generateContent?key={GEMINI_API_KEY}"
            )
            response = requests.post(url, json=payload, timeout=30)

            try:
                result = response.json()
            except ValueError:
                result = {}

            if response.status_code == 200 and "candidates" in result:
                return result["candidates"][0]["content"]["parts"][0]["text"]

            last_error = result.get("error", {}).get("message", response.text)
            if response.status_code == 404:
                continue

            return f"AI service is unavailable right now. {last_error}"

        return f"AI service is unavailable right now. {last_error or 'No working Gemini model found.'}"
    except Exception:
        return "AI service is unavailable right now."


def get_ai_doubt_response(user_input: str, exp: Optional[Dict[str, Any]] = None) -> str:
    context_block = ""
    if exp:
        context_block = (
            "Use the experiment context below to answer the student's doubt. "
            "If the doubt is outside the experiment, answer briefly but stay relevant.\n\n"
            f"{build_experiment_context(exp)}\n\n"
        )

    prompt = f"""
You are an Electronics Lab Assistant.

Rules:
- Answer the student's doubt clearly and briefly.
- Prefer 3 to 5 lines or bullet points.
- If experiment context is provided, use it.
- Do not repeat the full experiment record.

{context_block}Student doubt:
{user_input}
"""
    return call_gemini(prompt)


def clean_question(text: str) -> str:
    text = re.sub(r"^[\-\*\d\.\)\s]+", "", (text or "").strip())
    text = re.sub(r"\s+", " ", text)
    if text and not text.endswith("?"):
        text += "?"
    return text


def generate_viva_questions(exp: Dict[str, Any]) -> List[str]:
    title = normalize_text(exp.get("title", ""))
    theory = exp.get("theory", "")
    procedure = exp.get("procedure", [])
    questions: List[str] = []

    questions.append(f"What is the aim of the experiment {exp.get('title', '')}?")

    if "inverting" in title and "non inverting" in title:
        questions.append("What is the main difference between inverting and non-inverting amplifier configurations?")
        questions.append("Why is the output inverted in the inverting amplifier?")
        questions.append("What are the gain formulas of inverting and non-inverting amplifiers?")
    elif "inverting amplifier" in title:
        questions.append("Why is the output of an inverting amplifier 180 degrees out of phase with the input?")
        questions.append("What is the gain formula of an inverting amplifier?")
    elif "non inverting amplifier" in title:
        questions.append("Why is the output of a non-inverting amplifier in phase with the input?")
        questions.append("What is the gain formula of a non-inverting amplifier?")

    if theory:
        theory_tokens = keyword_tokens(theory)
        if "op" in theory_tokens or "amp" in theory_tokens or "amplifier" in theory_tokens:
            questions.append("Why is an op-amp suitable for this experiment?")
        elif "frequency" in theory_tokens:
            questions.append("Why is frequency response important in this experiment?")
        elif "oscillator" in theory_tokens:
            questions.append("What condition is required for sustained oscillations in this experiment?")

    if procedure:
        questions.append(f"Why is the step '{procedure[0]}' important in this experiment?")
        if len(procedure) > 1:
            questions.append(f"What observation should you make after the step '{procedure[-1]}'?")

    deduplicated: List[str] = []
    seen = set()
    for question in questions:
        question = clean_question(question)
        key = normalize_text(question)
        if question and key not in seen:
            seen.add(key)
            deduplicated.append(question)

    return deduplicated[:4]


def infer_expected_answer(exp: Dict[str, Any], question: str) -> str:
    normalized_question = normalize_text(question)
    title = normalize_text(exp.get("title", ""))

    if "aim" in normalized_question:
        return exp.get("aim", "")
    if "gain formula" in normalized_question or ("gain" in normalized_question and "formula" in normalized_question):
        if "inverting" in title and "non inverting" in title:
            return (
                "The gain of an inverting amplifier is Av = -Rf/Rin and the gain of a "
                "non-inverting amplifier is Av = 1 + Rf/R1."
            )
        if "inverting amplifier" in title:
            return "The gain of an inverting amplifier is Av = -Rf/Rin."
        if "non inverting amplifier" in title:
            return "The gain of a non-inverting amplifier is Av = 1 + Rf/R1."
    if "output inverted" in normalized_question or ("inverted" in normalized_question and "output" in normalized_question):
        return (
            "The output is inverted because the signal is applied to the inverting terminal, "
            "which produces a 180 degree phase shift."
        )
    if "difference" in normalized_question and "inverting" in normalized_question and "non inverting" in normalized_question:
        return (
            "In an inverting amplifier the signal is applied to the inverting terminal and the output is out of phase, "
            "while in a non-inverting amplifier the signal is applied to the non-inverting terminal and the output stays in phase."
        )
    if "step" in normalized_question or "observation" in normalized_question:
        return " ".join(exp.get("procedure", []))
    return exp.get("theory", "") or exp.get("result", "")


def evaluate_viva_answer(exp: Dict[str, Any], question: str, student_answer: str) -> str:
    expected = infer_expected_answer(exp, question)
    expected_tokens = set(keyword_tokens(expected))
    answer_tokens = set(keyword_tokens(student_answer))
    overlap = len(expected_tokens & answer_tokens)

    if not student_answer.strip():
        verdict = "Incorrect"
    elif expected_tokens and overlap >= max(2, len(expected_tokens) // 3):
        verdict = "Correct"
    else:
        verdict = "Incorrect"

    return (
        f"{verdict}\n"
        f"Correct Answer: {expected}\n"
        f"Explanation: {expected}"
    )


def chatbot(
    user_input: str,
    selected_experiment: Optional[str] = None,
    mode: Optional[str] = None,
    current_question: Optional[str] = None,
    student_answer: Optional[str] = None,
) -> Dict[str, Any]:
    user_input = (user_input or "").strip()
    exp_key = find_experiment(user_input=user_input, selected_experiment=selected_experiment)
    exp = data.get(exp_key) if exp_key else None
    intent = detect_intent(user_input, mode=mode)

    if intent == "viva":
        if not exp:
            return {"text": "Please enter a valid experiment name for viva.", "image": None, "graph": None, "pdf": None}
        questions = generate_viva_questions(exp)
        return {
            "text": "Viva Questions:\n" + "\n".join(f"{idx + 1}. {q}" for idx, q in enumerate(questions)),
            "questions": questions,
            "experiment": exp.get("title"),
            "image": None,
            "graph": None,
            "pdf": None,
        }

    if intent == "evaluate":
        if not exp:
            return {"text": "Please enter a valid experiment name for viva.", "image": None, "graph": None, "pdf": None}
        evaluation = evaluate_viva_answer(exp, current_question or "", student_answer or user_input)
        return {"text": evaluation, "image": None, "graph": None, "pdf": None}

    if exp:
        if is_experiment_lookup(user_input, exp):
            return format_experiment_details(exp)

        if intent == "aim":
            return {"text": f"Aim: {exp.get('aim', '')}", "image": None, "graph": None, "pdf": None}
        if intent == "apparatus":
            return {"text": "Apparatus: " + ", ".join(exp.get("components", [])), "image": None, "graph": None, "pdf": None}
        if intent == "theory":
            return {"text": f"Theory: {exp.get('theory', '')}", "image": None, "graph": None, "pdf": None}
        if intent == "procedure":
            steps = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(exp.get("procedure", [])))
            return {"text": f"Procedure:\n{steps}", "image": None, "graph": None, "pdf": None}
        if intent == "result":
            return {"text": f"Result: {exp.get('result', '')}", "image": None, "graph": None, "pdf": None}
        if intent == "diagram":
            return {"text": f"Circuit/Diagram for {exp.get('title', '')}", "image": exp.get("image"), "graph": None, "pdf": None}
        if intent == "graph":
            return {"text": f"Graph for {exp.get('title', '')}", "image": None, "graph": exp.get("graph"), "pdf": None}

        return {"text": get_ai_doubt_response(user_input, exp=exp), "image": None, "graph": None, "pdf": None}

    return {"text": get_ai_doubt_response(user_input), "image": None, "graph": None, "pdf": None}


if __name__ == "__main__":
    while True:
        user = input("\nYou: ")
        print("\nBot:", chatbot(user)["text"])
