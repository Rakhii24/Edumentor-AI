import re


def detect_intent(text: str) -> str:
    t = text.lower()
    if re.search(r"\bdefine|what is\b", t):
        return "definition"
    if re.search(r"\bderive|prove|show that|deduce\b", t):
        return "derivation"
    if re.search(r"\bcalculate|find|compute|evaluate|numerical|value\b", t) or re.search(r"[0-9].*\b(m|kg|s|mol|N|J|Pa|m/s|Hz|C|V)\b", t):
        return "numerical"
    if re.search(r"\bexplain|why|how|concept\b", t):
        return "conceptual"
    return "conceptual"
