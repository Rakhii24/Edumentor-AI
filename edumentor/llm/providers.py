from typing import List, Dict, Any
from edumentor.config import settings


def build_prompt(question: str, contexts: List[Dict[str, Any]], intent: str, exam_focus: str) -> List[Dict[str, str]]:
    citations = []
    for c in contexts:
        m = c.get("metadata", {})
        src = m.get("source", "")
        page = m.get("page", "")
        title = m.get("title", "")
        citations.append(f"{title} | {src} | p.{page}")
    context_text = "\n\n".join([c["text"] for c in contexts])
    sys = (
        "You are EduMentor AI for JEE/NEET. Use only the provided context. "
        "Produce a structured, student-friendly answer aligned to the syllabus. "
        "If information is missing in the context, state the gap clearly and avoid hallucination. "
        "Use clear sections: Problem or Topic; Retrieved Context; Key Ideas; Formulae; Step-by-Step Solution or Derivation; Units and Significant Figures; Common Mistakes; Quick Revision; Suggested Next Topics. "
        "Cite sources with title, file name, and page."
    )
    usr = (
        f"Exam focus: {exam_focus}\n"
        f"Intent: {intent}\n"
        f"Question: {question}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Citations:\n" + "\n".join(citations)
    )
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": usr},
    ]


class LLM:
    def __init__(self):
        import google.generativeai as genai
        if not settings.google_api_key:
            self.gemini_model = None
        else:
            genai.configure(api_key=settings.google_api_key)
            self.gemini_model = genai.GenerativeModel(settings.model_gemini)

    def generate(self, question: str, contexts: List[Dict[str, Any]], intent: str, exam_focus: str) -> str:
        messages = build_prompt(question, contexts, intent, exam_focus)
        if not self.gemini_model:
            return "System not configured. Add your API key in .env and restart."
        text = messages[0]["content"] + "\n\n" + messages[1]["content"]
        r = self.gemini_model.generate_content(text)
        return getattr(r, "text", "") or ""
