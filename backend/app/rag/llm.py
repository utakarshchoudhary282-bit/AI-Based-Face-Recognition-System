"""The LLM: Groq's Llama 3.1 (free API key from console.groq.com). None if no key is set."""
from ..config import settings


def get_llm():
    if not settings.GROQ_API_KEY:
        return None
    from langchain_groq import ChatGroq
    return ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY, temperature=0.1, max_tokens=500)
