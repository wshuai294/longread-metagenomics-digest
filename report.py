"""
Report generation: full abstract per paper, repo summary.
Papers are assumed already sorted by institution rank (best first).
"""
from datetime import datetime
from html import escape as html_escape
from typing import Any

from qs_rank import get_rank_display


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


def build_report(papers: list[dict], repos: list[dict], digest_summary: str = "") -> str:
    """Build a plain-text and HTML-friendly report. Papers sorted by QS rank (best first)."""
    lines = []
    lines.append("Long-read sequencing & metagenomics digest")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    if digest_summary and digest_summary.strip():
        lines.append("## Weekly digest summary")
        lines.append("")
        lines.append(digest_summary.strip())
        lines.append("")
    lines.append("## Recent papers (last 7 days, sorted by QS rank of first affiliation)")
    lines.append("")
    for p in papers:
        title = p.get("title", "No title")
        url = p.get("url", "") or (f"https://pubmed.ncbi.nlm.nih.gov/{p.get('pmid', '')}/" if p.get("pmid") else "")
        source = p.get("source", "PubMed")
        abstract = (p.get("abstract") or "").strip() or "(No abstract)"
        rank_str, rank_source = get_rank_display(p.get("affiliation") or "")
        rank_display = f"  Rank: {rank_str}" + (f" ({rank_source})" if rank_source else "")
        aff = (p.get("affiliation") or "").strip()
        journal = (p.get("journal") or "").strip()
        corr = (p.get("corresponding_author") or "").strip()
        pub_date = (p.get("pub_date") or "").strip()
        lines.append(f"• [{source}] {title}")
        if url:
            lines.append(f"  {url}")
        lines.append(f"  Publish date: {pub_date or '—'}")
        lines.append(f"  {rank_display}")
        if journal:
            lines.append(f"  Journal: {journal}")
        if corr:
            lines.append(f"  Corresponding author: {corr}")
        if aff:
            lines.append(f"  First affiliation: {aff}")
        lines.append(f"  Abstract: {abstract}")
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


def build_html_report(papers: list[dict], repos: list[dict], digest_summary: str = "") -> str:
    """Build HTML report for email body. Papers sorted by QS rank."""
    html_parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<style>body{font-family:sans-serif;max-width:720px;margin:1em auto;padding:0 1em;}",
        "a{color:#0969da;} h2{margin-top:1.2em;} ul{list-style:none;padding-left:0;}",
        "li{margin-bottom:1em;border-left:3px solid #ddd;padding-left:0.8em;}",
        ".meta{color:#656d76;font-size:0.9em;} .source{font-size:0.85em;color:#0969da;}",
        ".digest{background:#f6f8fa;padding:1em;border-radius:6px;margin:1em 0;}</style></head><body>",
        f"<h1>Long-read sequencing & metagenomics digest</h1>",
        f"<p class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
    ]
    if digest_summary and digest_summary.strip():
        html_parts.append("<h2>Weekly digest summary</h2>")
        html_parts.append(f"<div class='digest'>{html_escape(digest_summary.strip()).replace(chr(10), '<br>')}</div>")
    html_parts.append("<h2>Recent papers (last 7 days, by QS rank of first affiliation)</h2><ul>")
    for p in papers:
        title = html_escape(p.get("title", "No title"))
        url = p.get("url", "") or (f"https://pubmed.ncbi.nlm.nih.gov/{p.get('pmid', '')}/" if p.get("pmid") else "#")
        if not url:
            url = "#"
        source = p.get("source", "PubMed")
        abstract = html_escape((p.get("abstract") or "").strip() or "(No abstract)")
        rank_str, rank_source = get_rank_display(p.get("affiliation") or "")
        rank_label = f"Rank: {rank_str}" + (f" ({rank_source})" if rank_source else "")
        aff = html_escape((p.get("affiliation") or "").strip())
        journal = html_escape((p.get("journal") or "").strip())
        corr = html_escape((p.get("corresponding_author") or "").strip())
        pub_date = html_escape((p.get("pub_date") or "").strip()) or "—"
        meta_bits = [f"Publish date: {pub_date}", rank_label]
        if journal:
            meta_bits.append(f"Journal: {journal}")
        if corr:
            meta_bits.append(f"Corresponding author: {corr}")
        if aff:
            meta_bits.append(f"First affiliation: {aff}")
        meta_html = "<br><span class='meta'>" + " · ".join(meta_bits) + "</span>" if meta_bits else ""
        html_parts.append(
            f"<li><span class='source'>[{source}]</span> <a href='{url}'>{title}</a>{meta_html}<br><span class='meta'><b>Abstract:</b> {abstract}</span></li>"
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
