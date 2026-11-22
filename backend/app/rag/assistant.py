"""RAG = Retrieval-Augmented Generation.

1. Retrieve: find the 4 policy chunks most similar to the question (FAISS).
2. Add the verified employee's record (looked up by id, so it's always the right person).
3. Generate: the LLM answers ONLY from those numbered sources and cites them like [S1].
If no LLM key is set (or the call fails), we show the best matching policy lines instead.
"""
import re

from langchain_core.messages import HumanMessage, SystemMessage

from .documents import employee_profile
from .index import policy_index
from .llm import get_llm

RULES = """You are the HR & Security assistant of an employee verification portal.
- Answer ONLY from the numbered sources below. Do not use outside knowledge.
- Put the source number after each fact, like [S1].
- If the sources don't contain the answer, say: "I couldn't find this in the company documents."
- For "can this person ..." questions, start with Yes, No or Needs approval, then the reason.
- Keep it short: 2 to 5 sentences."""


def build_sources(question: str, employee=None) -> list[dict]:
    sources = []
    if employee is not None:
        sources.append({"title": f"Employee record - {employee.name}", "section": "Profile",
                        "text": employee_profile(employee), "score": None})
    for doc, score in policy_index.search(question):
        sources.append({"title": doc.metadata["title"], "section": doc.metadata["section"],
                        "text": doc.page_content, "score": score})
    for i, s in enumerate(sources, start=1):
        s["id"] = f"S{i}"
    return sources


def fallback_answer(question: str, sources: list[dict]) -> str:
    """No LLM: show the policy sentences that share the most words with the question."""
    words = set(re.findall(r"[a-z0-9]+", question.lower()))
    best = []
    for s in sources:
        for sentence in re.split(r"(?<=[.!?])\s+|\n", s["text"]):
            sentence = sentence.strip(" -*#|").replace("**", "")
            overlap = len(words & set(re.findall(r"[a-z0-9]+", sentence.lower())))
            if len(sentence) > 25 and overlap:
                best.append((overlap, f"- {sentence} [{s['id']}]"))
    best.sort(key=lambda t: -t[0])
    lines = [line for _, line in best[:4]]
    return "\n".join(lines) if lines else "I couldn't find this in the company documents."


def answer(question: str, employee=None) -> dict:
    sources = build_sources(question, employee)
    context = "\n\n".join(f"[{s['id']}] ({s['title']} - {s['section']})\n{s['text']}" for s in sources)
    llm = get_llm()
    note = ""
    text = None
    if llm is not None:
        try:
            reply = llm.invoke([SystemMessage(content=RULES),
                                HumanMessage(content=f"Sources:\n{context}\n\nQuestion: {question}")])
            text = reply.content
        except Exception as exc:
            note = f"LLM call failed ({type(exc).__name__}); showing the matching policy lines."
    else:
        note = "No Groq key set; showing the matching policy lines."
    if text is None:
        text = fallback_answer(question, sources)
    return {"answer": text, "used_llm": not note, "note": note,
            "sources": [{"id": s["id"], "title": s["title"], "section": s["section"],
                         "score": s["score"], "snippet": s["text"][:400]} for s in sources]}
