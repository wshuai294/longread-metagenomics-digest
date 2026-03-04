"""
Generate PDF report. Default: ./new_literature/YYYY-MM-DD.pdf (current directory).
Use --out for a custom path (e.g. Desktop if you have write permission).
"""
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from report import one_sentence_summary, summarize_repo
from qs_rank import get_qs_rank


def _escape(s: str) -> str:
    """Escape for ReportLab Paragraph (basic HTML)."""
    if not s:
        return ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def get_pdf_output_path() -> Path:
    """Default path: ./new_literature/YYYY-MM-DD.pdf (current working directory).
    Avoids macOS permission issues with writing to Desktop.
    """
    folder = Path.cwd() / "new_literature"
    folder.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    return folder / f"{date_str}.pdf"


def build_pdf_report(
    papers: list[dict[str, Any]],
    repos: list[dict[str, Any]],
    output_path: Path | str,
) -> None:
    """Build and save PDF report to output_path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = styles["Normal"]
    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=9,
        textColor="gray",
        spaceAfter=2,
    )
    link_style = ParagraphStyle(
        "Link",
        parent=styles["Normal"],
        fontSize=9,
        textColor="blue",
        spaceAfter=4,
    )

    story = []
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    story.append(Paragraph(_escape("Long-read sequencing & metagenomics digest"), title_style))
    story.append(Paragraph(_escape(f"Generated: {date_str}"), small_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            _escape("Recent papers (last 7 days, sorted by QS rank of first affiliation)"),
            heading_style,
        )
    )
    for p in papers:
        title = _escape(p.get("title", "No title"))
        source = p.get("source", "PubMed")
        url = p.get("url", "") or (
            f"https://pubmed.ncbi.nlm.nih.gov/{p.get('pmid', '')}/" if p.get("pmid") else ""
        )
        one_line = _escape(one_sentence_summary(p))
        aff = (p.get("affiliation") or "").strip()
        rank = get_qs_rank(aff)
        rank_display = str(rank) if rank < 9999 else "—"
        journal = (p.get("journal") or "").strip()
        corr = (p.get("corresponding_author") or "").strip()
        story.append(Paragraph(f"<b>[{source}]</b> {title}", body_style))
        if url:
            story.append(Paragraph(f'<a href="{_escape(url)}" color="blue">{_escape(url)}</a>', link_style))
        story.append(Paragraph(_escape(f"QS rank: {rank_display}"), small_style))
        if journal:
            story.append(Paragraph(_escape(f"Journal: {journal}"), small_style))
        if corr:
            story.append(Paragraph(_escape(f"Corresponding author: {corr}"), small_style))
        if aff:
            story.append(Paragraph(_escape(f"First affiliation: {aff}"), small_style))
        story.append(Paragraph(_escape(f"Summary: {one_line}"), small_style))
        story.append(Spacer(1, 0.15 * inch))
    if not papers:
        story.append(Paragraph("<i>No new papers in the selected period.</i>", body_style))
        story.append(Spacer(1, 0.15 * inch))

    story.append(
        Paragraph(_escape("GitHub repositories"), heading_style)
    )
    for r in repos:
        name = _escape(r.get("name", ""))
        url = (r.get("url") or "").strip()
        summary = _escape(summarize_repo(r))
        story.append(Paragraph(f'<a href="{_escape(url)}" color="blue">{name}</a>', body_style))
        story.append(Paragraph(summary, small_style))
        story.append(Spacer(1, 0.15 * inch))
    if not repos:
        story.append(Paragraph("<i>No repositories found.</i>", body_style))

    doc.build(story)
