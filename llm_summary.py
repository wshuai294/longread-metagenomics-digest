"""
Generate a weekly digest summary of all papers using free LLM APIs (Groq or Gemini).
Set GROQ_API_KEY or GEMINI_API_KEY in the environment. Groq is tried first.
"""
from typing import Any

import requests

import config

# Max papers to include in the prompt (to stay under context limits)
_MAX_PAPERS_FOR_SUMMARY = 50
# Max chars of abstract per paper
_ABSTRACT_EXCERPT = 350


def _build_prompt(papers: list[dict[str, Any]]) -> str:
    """Build prompt text: list of title + abstract excerpt per paper."""
    parts = []
    for i, p in enumerate(papers[: _MAX_PAPERS_FOR_SUMMARY], 1):
        title = (p.get("title") or "No title").strip()
        abstract = (p.get("abstract") or "").strip() or "(No abstract)"
        if len(abstract) > _ABSTRACT_EXCERPT:
            abstract = abstract[:_ABSTRACT_EXCERPT].rsplit(" ", 1)[0] + "…"
        parts.append(f"[{i}] {title}\n{abstract}")
    return "\n\n".join(parts)


def _call_groq(prompt: str) -> str:
    """Call Groq API (free tier). https://console.groq.com"""
    if not config.GROQ_API_KEY:
        return ""
    system = (
        "You are a science writer. Summarize the following set of recent papers "
        "on long-read sequencing and metagenomics into one cohesive digest. "
        "Write 3-5 paragraphs that synthesize main themes, methods, and findings. "
        "Use clear, concise academic English."
    )
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 1024,
                "temperature": 0.3,
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        choice = data.get("choices", [{}])[0]
        return (choice.get("message", {}).get("content") or "").strip()
    except Exception as e:
        if config.__dict__.get("DEBUG_LLM"):
            print(f"  Groq error: {e}", flush=True)
        return ""


def _call_gemini(prompt: str) -> str:
    """Call Google Gemini API (free tier). See https://ai.google.dev/gemini-api/docs/quickstart"""
    if not config.GEMINI_API_KEY:
        return ""
    instruction = (
        "Summarize the following set of recent papers on long-read sequencing and metagenomics "
        "into one cohesive digest. Write 3-5 paragraphs that synthesize main themes, methods, and findings. "
        "Use clear, concise academic English."
    )
    full_text = f"{instruction}\n\n{prompt}"
    # Model list per official quickstart: gemini-3-flash-preview first
    # https://ai.google.dev/gemini-api/docs/quickstart
    for model in (
        "gemini-3-flash-preview",
        "gemini-1.5-flash-8b",
        "gemini-2.0-flash-exp",
        "gemini-pro",
    ):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            r = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": config.GEMINI_API_KEY,
                },
                json={
                    "contents": [{"parts": [{"text": full_text}]}],
                    "generationConfig": {
                        "maxOutputTokens": 1024,
                        "temperature": 0.3,
                    },
                },
                timeout=90,
            )
            r.raise_for_status()
            data = r.json()
            candidates = data.get("candidates", [])
            if not candidates:
                continue
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                continue
            text = (parts[0].get("text") or "").strip()
            if text:
                return text
        except Exception as e:
            err_msg = str(e)
            if hasattr(e, "response") and getattr(e.response, "text", None):
                err_msg = e.response.text[:200] if len(e.response.text) > 200 else e.response.text
            if __import__("os").environ.get("DEBUG_LLM"):
                print(f"  Gemini ({model}): {err_msg}", flush=True)
            continue
    return ""


def get_weekly_digest_summary(papers: list[dict[str, Any]]) -> str:
    """
    Return a cohesive digest summary of all papers using a free LLM (Groq or Gemini).
    Returns empty string if no API key is set or the request fails.
    """
    if not papers:
        return ""
    prompt = _build_prompt(papers)
    if not prompt.strip():
        return ""
    summary = _call_groq(prompt)
    if not summary:
        summary = _call_gemini(prompt)
    return summary
