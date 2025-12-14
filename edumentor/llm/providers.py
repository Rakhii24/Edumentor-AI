from typing import List, Dict, Any
from edumentor.config import settings


def build_prompt(
    question: str,
    contexts: List[Dict[str, Any]],
    intent: str,
    exam_focus: str
) -> List[Dict[str, str]]:

    citations = []
    for c in contexts:
        m = c.get("metadata", {})
        src = m.get("source", "")
        page = m.get("page", "")
        title = m.get("title", "")
        citations.append(f"{title} | {src} | p.{page}")

    context_text = "\n\n".join([c.get("text", "") for c in contexts])

    system_prompt = (
        "You are EduMentor AI, an AI tutor for JEE/NEET preparation. "
        "Use ONLY the provided context. "
        "If information is missing, clearly state that it is not available in the context. "
        "Do NOT hallucinate.\n\n"
        "Structure the answer with these sections:\n"
        "1. Problem or Topic\n"
        "2. Retrieved Context\n"
        "3. Key Ideas\n"
        "4. Formulae\n"
        "5. Step-by-Step Solution or Derivation\n"
        "6. Units and Significant Figures\n"
        "7. Common Mistakes\n"
        "8. Quick Revision\n"
        "9. Suggested Next Topics\n\n"
        "Always include citations with title, file name, and page number."
    )

    user_prompt = (
        f"Exam Focus: {exam_focus}\n"
        f"Intent: {intent}\n"
        f"Question: {question}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Citations:\n" + "\n".join(citations)
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


class LLM:
    def __init__(self):
        import google.generativeai as genai

        # ✅ SAFELY HANDLE API KEY (LOCAL + STREAMLIT CLOUD)
        api_key = settings.google_api_key

        if not api_key:
            self.gemini_model = None
            return

        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel(settings.model_gemini)

    def generate(
        self,
        question: str,
        contexts: List[Dict[str, Any]],
        intent: str,
        exam_focus: str
    ) -> str:

        if not self.gemini_model:
            return (
                "⚠️ **System not configured**\n\n"
                "Please add your Google API key in Streamlit Secrets and restart the app."
            )

        messages = build_prompt(question, contexts, intent, exam_focus)

        # Gemini expects a single combined prompt
        prompt_text = (
            messages[0]["content"]
            + "\n\n"
            + messages[1]["content"]
        )

        try:
            response = self.gemini_model.generate_content(prompt_text)
            return response.text.strip() if hasattr(response, "text") else "⚠️ No response generated."

        except Exception as e:
            return f"❌ Error while generating answer: {str(e)}"
