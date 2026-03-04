#!/usr/bin/env python3
"""
Long-read sequencing & metagenomics digest: fetch papers + GitHub repos,
summarize, and generate a PDF report (default: ./new_literature/YYYY-MM-DD.pdf).
"""
import argparse
import sys
from pathlib import Path

import config
import fetchers
import report
import report_pdf
from email_sender import send_report
from qs_rank import sort_papers_by_qs_rank


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch papers and GitHub repos on long-read sequencing & metagenomics, generate PDF digest."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=config.DEFAULT_DAYS,
        help=f"Papers from the last N days (default: {config.DEFAULT_DAYS}, max: {config.MAX_DAYS} = one week)",
    )
    parser.add_argument(
        "--email",
        action="store_true",
        help="Also send report to email (requires DIGEST_SMTP_PASSWORD)",
    )
    parser.add_argument(
        "--no-biorxiv",
        action="store_true",
        help="Skip fetching bioRxiv preprints (only PubMed + GitHub)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="PDF output path (default: ./new_literature/YYYY-MM-DD.pdf)",
    )
    args = parser.parse_args()
    days_back = min(max(1, args.days), config.MAX_DAYS)
    if days_back != args.days:
        print(f"Time window limited to {days_back} days (within a week).")

    print("Fetching papers from PubMed...")
    pubmed_papers = fetchers.fetch_papers(days_back=days_back)
    print(f"  Found {len(pubmed_papers)} papers.")

    if args.no_biorxiv:
        biorxiv_papers = []
        print("Skipping bioRxiv (--no-biorxiv).")
    else:
        print("Fetching papers from bioRxiv...")
        biorxiv_papers = fetchers.fetch_biorxiv(days_back=days_back)
        print(f"  Found {len(biorxiv_papers)} preprints.")

    papers = sort_papers_by_qs_rank(pubmed_papers + biorxiv_papers)

    print("Fetching GitHub repositories...")
    repos = fetchers.fetch_github_repos()
    print(f"  Found {len(repos)} repos.")

    pdf_path = Path(args.out) if args.out else report_pdf.get_pdf_output_path()
    report_pdf.build_pdf_report(papers, repos, pdf_path)
    print(f"PDF report written to {pdf_path}")

    if args.email:
        plain = report.build_report(papers, repos)
        html = report.build_html_report(papers, repos)
        try:
            send_report(plain, html)
            print(f"Report sent to {config.EMAIL_TO}")
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
