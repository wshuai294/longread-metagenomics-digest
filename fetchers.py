"""
Fetchers for papers (PubMed) and GitHub repositories.
"""
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any

import requests

import config


def _pubmed_esearch(query: str, retmax: int = 20, mindate: str | None = None) -> list[str]:
    """Search PubMed; returns list of PMIDs."""
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    params: dict[str, Any] = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "sort": "date",
        "tool": "longread-metagenomics-digest",
        "email": config.EMAIL_TO,
    }
    if config.NCBI_API_KEY:
        params["api_key"] = config.NCBI_API_KEY
    if mindate:
        params["mindate"] = mindate

    r = requests.get(f"{base}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    ids = data.get("esearchresult", {}).get("idlist", [])
    return ids


def _pubmed_efetch(pmids: list[str]) -> list[dict[str, Any]]:
    """Fetch article details for given PMIDs (PubMed returns XML)."""
    if not pmids:
        return []
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    params: dict[str, Any] = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": "longread-metagenomics-digest",
        "email": config.EMAIL_TO,
    }
    if config.NCBI_API_KEY:
        params["api_key"] = config.NCBI_API_KEY

    r = requests.get(f"{base}/efetch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {"mb": "http://www.ncbi.nlm.nih.gov"}
    # PubMed XML uses default ns; we'll use local names only
    out = []
    for art in root.findall(".//PubmedArticle") or root.findall(".//Article"):
        try:
            med = art.find(".//Article") or art
            if med is None:
                continue
            pmid_el = art.find(".//PMID")
            pmid = (pmid_el.text or "").strip() if pmid_el is not None else ""
            title_el = med.find(".//ArticleTitle")
            title = (title_el.text or "").strip() if title_el is not None else ""
            abstract_el = med.find(".//Abstract")
            if abstract_el is not None:
                abstract = " ".join(
                    (e.text or "").strip() for e in abstract_el.findall(".//AbstractText")
                ).strip()
            else:
                abstract = ""
            year_el = art.find(".//PubDate/Year") or art.find(".//JournalIssue/PubDate/Year")
            year = (year_el.text or "").strip() if year_el is not None else ""
            # Journal name
            journal_el = med.find(".//Journal/Title") or med.find(".//Journal/JT") or art.find(".//Journal/Title")
            journal = (journal_el.text or "").strip() if journal_el is not None and journal_el.text else ""
            # First author's first affiliation (for QS rank sorting) and corresponding author (last author)
            first_aff = ""
            corresponding_author = ""
            author_list = art.find(".//AuthorList") or med.find(".//AuthorList")
            if author_list is not None:
                authors = author_list.findall(".//Author")
                if authors:
                    first_author = authors[0]
                    aff_el = first_author.find(".//Affiliation") or first_author.find(".//AffiliationInfo/Affiliation")
                    if aff_el is not None and aff_el.text:
                        first_aff = (aff_el.text or "").strip()
                    # Corresponding author: use last author (senior/corresponding convention)
                    last_author = authors[-1]
                    last_name = last_author.find("LastName")
                    fore_name = last_author.find("ForeName")
                    initials = last_author.find("Initials")
                    ln = (last_name.text or "").strip() if last_name is not None else ""
                    fn = (fore_name.text or "").strip() if fore_name is not None else ""
                    inits = (initials.text or "").strip() if initials is not None else ""
                    if ln:
                        corresponding_author = f"{fn} {ln}".strip() if fn else (f"{inits} {ln}".strip() if inits else ln)
            out.append({
                "pmid": str(pmid),
                "title": title or "No title",
                "abstract": abstract or "(No abstract)",
                "year": year,
                "affiliation": first_aff,
                "journal": journal,
                "corresponding_author": corresponding_author,
                "source": "PubMed",
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            })
        except Exception:
            continue
    return out


def fetch_biorxiv(days_back: int = 7) -> list[dict[str, Any]]:
    """Fetch recent bioRxiv preprints; filter by long-read + metagenomics keywords."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    base = "https://api.biorxiv.org/details/biorxiv"
    keywords = ("long read", "long-read", "nanopore", "pacbio", "metagenomic", "metagenomics")
    out: list[dict[str, Any]] = []
    cursor = 0
    try:
        while True:
            r = requests.get(f"{base}/{start_str}/{end_str}/{cursor}/json", timeout=25)
            r.raise_for_status()
            data = r.json()
            collection = data.get("collection", [])
            if not collection:
                break
            for item in collection:
                title = (item.get("title") or item.get("preprint_title") or "").strip()
                abstract = (item.get("abstract") or item.get("preprint_abstract") or "").strip()
                text = f"{title} {abstract}".lower()
                if not any(kw in text for kw in keywords):
                    continue
                doi = (item.get("doi") or item.get("biorxiv_doi") or "").strip()
                url = f"https://www.biorxiv.org/content/{doi}" if doi else ""
                # First affiliation: use first element if API returns a list (author order), else single value
                raw_aff = (
                    item.get("preprint_author_corresponding_institution")
                    or item.get("affiliation")
                    or item.get("affiliations")
                    or ""
                )
                if isinstance(raw_aff, list):
                    aff = (raw_aff[0] if raw_aff else "") or ""
                else:
                    aff = str(raw_aff).strip()
                # Corresponding author: bioRxiv API may return preprint_author_corresponding or author string
                corr_author = (item.get("preprint_author_corresponding") or item.get("authors") or "")
                if isinstance(corr_author, list):
                    corr_author = (corr_author[0] if corr_author else "") or ""
                corr_author = str(corr_author).strip()
                if not corr_author and item.get("preprint_authors"):
                    # Take first author from "Author1; Author2; ..." as fallback
                    authors_str = item.get("preprint_authors", "")
                    if isinstance(authors_str, str) and ";" in authors_str:
                        corr_author = authors_str.split(";")[0].strip()
                    elif authors_str:
                        corr_author = str(authors_str).strip()
                out.append({
                    "pmid": "",  # no PMID for preprints
                    "doi": doi,
                    "title": title or "No title",
                    "abstract": abstract or "(No abstract)",
                    "year": start_date.strftime("%Y"),
                    "affiliation": aff,
                    "journal": "bioRxiv (preprint)",
                    "corresponding_author": corr_author,
                    "source": "bioRxiv",
                    "url": url,
                })
                if len(out) >= config.MAX_PAPERS:
                    break
            if len(out) >= config.MAX_PAPERS:
                break
            cursor += len(collection)
            if len(collection) < 100:
                break
    except (requests.RequestException, ValueError):
        # API timeout or parse error: return what we have
        pass
    return out[: config.MAX_PAPERS]


def fetch_papers(days_back: int = 7) -> list[dict[str, Any]]:
    """Fetch recent papers on long-read sequencing and metagenomics from PubMed."""
    mindate = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    query = "(long read[Title/Abstract] OR long-read[Title/Abstract] OR nanopore[Title/Abstract] OR pacbio[Title/Abstract]) AND (metagenomic[Title/Abstract] OR metagenomics[Title/Abstract])"
    ids = _pubmed_esearch(query, retmax=config.MAX_PAPERS, mindate=mindate)
    if not ids:
        return []
    time.sleep(0.34)  # NCBI rate limit
    return _pubmed_efetch(ids)


def fetch_github_repos() -> list[dict[str, Any]]:
    """Fetch relevant GitHub repos (sorted by recently updated, then stars)."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"token {config.GITHUB_TOKEN}"

    # Search: metagenomics + long read / nanopore
    q = "metagenomics long-read OR nanopore OR pacbio sequencing"
    params = {"q": q, "sort": "updated", "per_page": config.MAX_REPOS}
    r = requests.get(
        "https://api.github.com/search/repositories",
        params=params,
        headers=headers,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])

    out = []
    for repo in items:
        out.append({
            "name": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "description": repo.get("description") or "(No description)",
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language") or "",
            "updated": repo.get("updated_at", ""),
        })
    return out
