# Long-read sequencing & metagenomics digest

A Python tool that fetches **recent papers** (PubMed + bioRxiv) and **GitHub repositories** on long-read sequencing and metagenomics, then generates a **PDF report** (and optionally emails it).

**Time window:** Last **7 days** (one week). Papers are **sorted by QS World University Rank** of the first affiliation (top 1000). Each entry includes journal, corresponding author, first affiliation, QS rank, and a one-sentence summary (&lt;50 words).

---

## Quick start

### 1. Install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/longread-metagenomics-digest.git
cd longread-metagenomics-digest
pip install -r requirements.txt
```

(Replace `YOUR_USERNAME` with your GitHub username.)

### 2. Run (generate PDF)

```bash
python main.py
```

- **Output:** PDF is written to `./new_literature/YYYY-MM-DD.pdf` in the **current working directory** (folder is created if needed). To use another path (e.g. Desktop): `python main.py --out /path/to/report.pdf`.
- **Skip bioRxiv** (faster, PubMed + GitHub only):  
  `python main.py --no-biorxiv`
- **Custom PDF path:**  
  `python main.py --out /path/to/report.pdf`
- **Also send by email:**  
  `python main.py --email`  
  (requires `DIGEST_SMTP_PASSWORD`; see Configuration.)

---

## What it does

| Step | Description |
|------|-------------|
| **Papers** | Fetches **PubMed** and **bioRxiv** from the **last 7 days**. Topic: (long read \| nanopore \| pacbio) and (metagenomic \| metagenomics). First affiliation is extracted for both (first author for PubMed; first from API list or corresponding for bioRxiv). |
| **Rank** | Papers are **sorted by institution rank**: **QS** (top 1000) first, then **US News Best Global** if no QS match. Displayed as e.g. "Rank: 5 (QS)" or "Rank: 10 (US News)" or "—". |
| **Per paper** | **Publish date**, rank, journal name, corresponding author, first affiliation, and **full abstract**. |
| **Repos** | GitHub repos matching "metagenomics long-read OR nanopore OR pacbio sequencing", sorted by recently updated. |
| **Report** | **PDF** to `./new_literature/YYYY-MM-DD.pdf` (current directory). If `GROQ_API_KEY` or `GEMINI_API_KEY` is set, a **weekly digest summary** (3–5 paragraphs) is generated from all papers and added at the top. Optional: `--email` to also send the report. |

---

## Configuration (environment variables)

| Variable | Description | Default |
|----------|-------------|---------|
| `DIGEST_EMAIL_TO` | Recipient email (for `--email`) | `wshuai294@gmail.com` |
| `DIGEST_EMAIL_FROM` | Sender address | same as `DIGEST_EMAIL_TO` |
| `DIGEST_SMTP_USER` | SMTP login | from-address |
| `DIGEST_SMTP_PASSWORD` | SMTP password (Gmail: [App Password](https://support.google.com/accounts/answer/185833)) | *(required for `--email`)* |
| `DIGEST_SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `DIGEST_SMTP_PORT` | SMTP port | `587` |
| `DIGEST_MAX_PAPERS` | Max papers to include | `15` |
| `DIGEST_MAX_REPOS` | Max GitHub repos | `10` |
| `GITHUB_TOKEN` | Optional; higher GitHub API rate limit | — |
| `NCBI_API_KEY` | Optional; higher NCBI rate limit | — |
| `GROQ_API_KEY` | Optional; free LLM for weekly digest summary ([Groq](https://console.groq.com)) | — |
| `GEMINI_API_KEY` | Optional; free LLM fallback ([Google AI Studio](https://aistudio.google.com/apikey)) | — |

Time window is fixed at **7 days** (see `config.MAX_DAYS`).

---

## Project layout

| File | Description |
|------|-------------|
| `main.py` | Entrypoint: fetch → sort by QS rank → build PDF (and optionally email). |
| `config.py` | Settings (time window, email, limits) from environment. |
| `fetchers.py` | PubMed (E-utilities), bioRxiv API, and GitHub API. |
| `report.py` | Full abstract per paper, plain-text and HTML report builders. |
| `report_pdf.py` | PDF generation (ReportLab); default path `./new_literature/YYYY-MM-DD.pdf`. |
| `email_sender.py` | SMTP email (used only with `--email`). |
| `llm_summary.py` | Weekly digest summary via free LLM (Groq or Gemini). |
| `qs_rank.py` | Institution rank: QS first, US News fallback (top 1000 each). |
| `qs_rankings.csv` | QS World University Rankings (top ~1300). |
| `usnews_rankings.csv` | US News Best Global Universities (top 100, fallback when no QS match). |
| `requirements.txt` | Python dependencies (`requests`, `reportlab`). |

---

## Scheduling (e.g. weekly PDF)

Example cron (e.g. every Monday at 9:00):

```bash
0 9 * * 1 cd /path/to/longread-metagenomics-digest && python3 main.py
```

No env vars are required for PDF-only runs.

---

## Pushing to a new public GitHub repo

If you have this project locally and want to publish it:

1. **Create a new repository on GitHub**  
   Go to [github.com/new](https://github.com/new), choose a name (e.g. `longread-metagenomics-digest`), set visibility to **Public**, and do **not** add a README or .gitignore (you already have them).

2. **Add the remote and push** (replace `YOUR_USERNAME` and `REPO_NAME` with your repo):

   ```bash
   cd /path/to/cursor_play
   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

   Or with SSH:  
   `git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git` then `git push -u origin main`.

---

## License

MIT (or your choice). The QS rankings CSV is from public datasets (e.g. [QS-2022-ranking](https://github.com/hsiaoping-zhang/QS-world-university-rankings)).
