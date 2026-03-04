"""
Institution rank: QS World University Rankings first, fallback to US News Best Global.
Best rank = 1. Unmatched affiliations get rank 9999 (sort last).
Returns (rank, source) for display; source is "QS", "US News", or None.
"""
import csv
from pathlib import Path
from typing import Any

from config import PROJECT_ROOT

_NO_MATCH = 9999


def _load_rank_table(csv_path: Path, rank_key: str, name_key: str, max_rank: int = 1000) -> list[tuple[int, str]]:
    """Load (rank, university_name) from CSV."""
    if not csv_path.exists():
        return []
    rows: list[tuple[int, str]] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_rank = (row.get(rank_key) or row.get("Rank") or "").strip()
            name = (row.get(name_key) or row.get("University") or "").strip()
            if not raw_rank or not name:
                continue
            raw_rank = raw_rank.lstrip("= ")
            try:
                rank = int(raw_rank)
            except ValueError:
                continue
            if rank > max_rank:
                continue
            rows.append((rank, name))
    rows.sort(key=lambda x: (x[0], x[1].lower()))
    return rows


_QS_ROWS: list[tuple[int, str]] = _load_rank_table(
    PROJECT_ROOT / "qs_rankings.csv", "Rank", "University", max_rank=1000
)
_USNEWS_ROWS: list[tuple[int, str]] = _load_rank_table(
    PROJECT_ROOT / "usnews_rankings.csv", "Rank", "University", max_rank=1000
)


def _match_rank(affiliation: str, rows: list[tuple[int, str]]) -> int:
    """Return best (lowest) matching rank or _NO_MATCH."""
    if not (affiliation or "").strip() or not rows:
        return _NO_MATCH
    aff_lower = affiliation.strip().lower()
    best = _NO_MATCH
    for rank, name in rows:
        uni_lower = name.lower()
        if uni_lower in aff_lower or aff_lower in uni_lower:
            if rank < best:
                best = rank
    return best


def get_qs_rank(affiliation: str) -> int:
    """Return QS rank (9999 if no match). Used for sorting."""
    return _match_rank(affiliation, _QS_ROWS)


def get_best_rank(affiliation: str) -> tuple[int, str | None]:
    """Return (rank, source). source is 'QS', 'US News', or None if no match."""
    qs_r = _match_rank(affiliation, _QS_ROWS)
    if qs_r < _NO_MATCH:
        return (qs_r, "QS")
    usn_r = _match_rank(affiliation, _USNEWS_ROWS)
    if usn_r < _NO_MATCH:
        return (usn_r, "US News")
    return (_NO_MATCH, None)


def get_rank_display(affiliation: str) -> tuple[str, str | None]:
    """Return (rank_str, source) for display. e.g. ('5', 'QS') or ('—', None)."""
    rank, source = get_best_rank(affiliation)
    if rank < _NO_MATCH:
        return (str(rank), source)
    return ("—", None)


def sort_papers_by_qs_rank(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort papers by best available rank (QS first, then US News, ascending)."""
    def sort_key(p: dict[str, Any]) -> int:
        return get_best_rank(p.get("affiliation") or "")[0]
    return sorted(papers, key=sort_key)
