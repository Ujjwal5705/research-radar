"""
AI Feature: Summarize & simplify.

Takes a paper's abstract and asks a Groq-hosted LLM to rewrite it in plain
language for a non-expert reader. Deliberately simple - no caching, no
streaming - see README for why (scope control) and what we'd add next.
"""

from groq import Groq

from app.config import settings

# gpt-oss-20b: fast + cheap, good enough for a rewrite task like this.
# Groq deprecated llama-3.1-8b-instant in June 2026 in favor of this model.
SUMMARIZE_MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = (
    "You are a science communicator. Rewrite the given research paper abstract "
    "in plain, jargon-free language that a curious non-expert could understand. "
    "Keep it to 3-5 short sentences. Do not add any facts, numbers, or claims "
    "that are not present in the original abstract. Do not use markdown formatting."
)

_client: Groq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def summarize_abstract(abstract: str, client: Groq | None = None) -> str:
    if not abstract or not abstract.strip():
        raise ValueError("No abstract available to summarize.")

    client = client or get_client()
    response = client.chat.completions.create(
        model=SUMMARIZE_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": abstract},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Model returned an empty response.")
    return content.strip()
