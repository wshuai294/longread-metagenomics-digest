"""
Summarization and report generation.
Papers: use abstract as short summary (first ~300 chars or 2 sentences).
Repos: use description + language + stars as summary.
Papers are assumed already sorted by QS rank (best first).
"""
from datetime import datetime
from html import escape as html_escape
from typing import Any

from qs_rank import get_qs_rank


def summarize_paper(paper: dict[str, Any], max_chars: int = 320) -> str:
    """Short summary from title + abstract."""
    abstract = (paper.get("abstract") or "").strip()
    if not abstract or abstract == "(No abstract)":
        return paper.get("title", "")[:max_chars]
    if len(abstract) <= max_chars:
        return abstract
    # Prefer sentence boundary
    cut = abstract[: max_chars + 1].rsplit(". ", 1)
    return (cut[0] + ".").strip() if len(cut) > 1 else abstract[:max_chars].rstrip() + "…"


def one_sentence_summary(paper: dict[str, Any], max_words: int = 50) -> str:
    """One sentence summary of the research, under max_words words."""
    abstract = (paper.get("abstract") or "").strip()
    if not abstract or abstract == "(No abstract)":
        title = (paper.get("title") or "").strip()
        words = title.split()[:max_words]
        return " ".join(words) + ("." if words and not title.endswith(".") else "")
    # First sentence only, then trim to max_words
    first_sentence = abstract.split(". ")[0].strip()
    if not first_sentence.endswith("."):
        first_sentence += "."
    words = first_sentence.split()
    if len(words) <= max_words:
        return first_sentence
    return " ".join(words[:max_words]).rstrip(".,") + "."


def summarize_repo(repo: dict[str, Any]) -> str:
    """One-line summary: description, language, stars."""
    desc = (repo.get("description") or "").strip()
    lang = repo.get("language") or ""
    stars = repo.get("stars", 0)
    parts = [desc]
    if lang:
        parts.append(f" [{lang}]")
    if stars is not None:
        parts.append(f" — ★ {stars}")
    return "".join(parts)


def build_report(papers: list[dict], repos: list[dict]) -> str:
    """Build a plain-text and HTML-friendly report. Papers sorted by QS rank (best first)."""
    lines = []
    lines.append("Long-read sequencing & metagenomics digest")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    lines.append("## Recent papers (last 7 days, sorted by QS rank of first affiliation)")
    lines.append("")
    for p in papers:
        title = p.get("title", "No title")
        url = p.get("url", "") or (f"https://pubmed.ncbi.nlm.nih.gov/{p.get('pmid', '')}/" if p.get("pmid") else "")
        source = p.get("source", "PubMed")
        one_line = one_sentence_summary(p)
        rank = get_qs_rank(p.get("affiliation") or "")
        rank_str = str(rank) if rank < 9999 else "—"
        aff = (p.get("affiliation") or "").strip()
        journal = (p.get("journal") or "").strip()
        corr = (p.get("corresponding_author") or "").strip()
        lines.append(f"• [{source}] {title}")
        if url:
            lines.append(f"  {url}")
        lines.append(f"  QS rank: {rank_str}")
        if journal:
            lines.append(f"  Journal: {journal}")
        if corr:
            lines.append(f"  Corresponding author: {corr}")
        if aff:
            lines.append(f"  First affiliation: {aff}")
        lines.append(f"  Summary: {one_line}")
        lines.append("")
    if not papers:
        lines.append("(No new papers in the selected period.)")
        lines.append("")

    lines.append("## GitHub repositories")
    lines.append("")
    for r in repos:
        name = r.get("name", "")
        url = r.get("url", "")
        summary = summarize_repo(r)
        lines.append(f"• {name}")
        if url:
            lines.append(f"  {url}")
        lines.append(f"  {summary}")
        lines.append("")
    if not repos:
        lines.append("(No repositories found.)")
        lines.append("")

    return "\n".join(lines)


def build_html_report(papers: list[dict], repos: list[dict]) -> str:
    """Build HTML report for email body. Papers sorted by QS rank."""
    html_parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<style>body{font-family:sans-serif;max-width:720px;margin:1em auto;padding:0 1em;}",
        "a{color:#0969da;} h2{margin-top:1.2em;} ul{list-style:none;padding-left:0;}",
        "li{margin-bottom:1em;border-left:3px solid #ddd;padding-left:0.8em;}",
        ".meta{color:#656d76;font-size:0.9em;} .source{font-size:0.85em;color:#0969da;}</style></head><body>",
        f"<h1>Long-read sequencing & metagenomics digest</h1>",
        f"<p class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
        "<h2>Recent papers (last 7 days, by QS rank of first affiliation)</h2><ul>",
    ]
    for p in papers:
        title = html_escape(p.get("title", "No title"))
        url = p.get("url", "") or (f"https://pubmed.ncbi.nlm.nih.gov/{p.get('pmid', '')}/" if p.get("pmid") else "#")
        if not url:
            url = "#"
        source = p.get("source", "PubMed")
        one_line = html_escape(one_sentence_summary(p))
        rank = get_qs_rank(p.get("affiliation") or "")
        rank_display = str(rank) if rank < 9999 else "—"
        aff = html_escape((p.get("affiliation") or "").strip())
        journal = html_escape((p.get("journal") or "").strip())
        corr = html_escape((p.get("corresponding_author") or "").strip())
        meta_bits = [f"QS rank: {rank_display}"]
        if journal:
            meta_bits.append(f"Journal: {journal}")
        if corr:
            meta_bits.append(f"Corresponding author: {corr}")
        if aff:
            meta_bits.append(f"First affiliation: {aff}")
        meta_html = "<br><span class='meta'>" + " · ".join(meta_bits) + "</span>" if meta_bits else ""
        html_parts.append(
            f"<li><span class='source'>[{source}]</span> <a href='{url}'>{title}</a>{meta_html}<br><span class='meta'><b>Summary:</b> {one_line}</span></li>"
        )
    if not papers:
        html_parts.append("<li><em>No new papers in the selected period.</em></li>")
    html_parts.append("</ul><h2>GitHub repositories</h2><ul>")
    for r in repos:
        name = r.get("name", "")
        url = r.get("url", "#")
        summary = summarize_repo(r)
        html_parts.append(
            f"<li><a href='{url}'>{name}</a><br><span class='meta'>{summary}</span></li>"
        )
    if not repos:
        html_parts.append("<li><em>No repositories found.</em></li>")
    html_parts.append("</ul></body></html>")
    return "".join(html_parts)
