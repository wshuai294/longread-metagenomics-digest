"""
QS World University Rankings: match first affiliation string to a rank.
Best rank = 1 (MIT). Unmatched affiliations get rank 9999 (sort last).
This implementation uses the QS 2022 ranking CSV (top ~1300) and
matches against the first affiliation using simple substring matching.
"""
import csv
from pathlib import Path
from typing import Any

from config import PROJECT_ROOT


def _load_qs_table(max_rank: int = 1000) -> list[tuple[int, str]]:
    """Load QS rankings (rank, university name) up to max_rank from CSV."""
    csv_path = PROJECT_ROOT / "qs_rankings.csv"
    if not csv_path.exists():
        return []
    rows: list[tuple[int, str]] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_rank = (row.get("Rank") or "").strip()
            name = (row.get("University") or "").strip()
            if not raw_rank or not name:
                continue
            # Handle ranks like "=3"
            raw_rank = raw_rank.lstrip("= ")
            try:
                rank = int(raw_rank)
            except ValueError:
                continue
            if rank > max_rank:
                continue
            rows.append((rank, name))
    # Sort by numeric rank, then name
    rows.sort(key=lambda x: (x[0], x[1].lower()))
    return rows


_QS_ROWS: list[tuple[int, str]] = _load_qs_table()


def get_qs_rank(affiliation: str) -> int:
    """Return QS rank for the given affiliation string (first author's institution).

    Lower is better (1 = top). Returns 9999 if no match or table missing.
    """
    if not (affiliation or "").strip():
        return 9999
    if not _QS_ROWS:
        return 9999
    aff_lower = affiliation.strip().lower()
    best_rank = 9999
    for rank, name in _QS_ROWS:
        uni_lower = name.lower()
        # Use substring match in either direction to be more forgiving
        if uni_lower in aff_lower or aff_lower in uni_lower:
            if rank < best_rank:
                best_rank = rank
    return best_rank


def sort_papers_by_qs_rank(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort papers by QS rank of first affiliation (ascending: best rank first)."""
    return sorted(papers, key=lambda p: get_qs_rank(p.get("affiliation") or ""))
