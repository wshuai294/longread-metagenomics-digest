"""
Configuration for the long-read metagenomics digest tool.
Use environment variables; see README for setup.
"""
import os
from pathlib import Path

# Email (required for sending report)
EMAIL_FROM = os.environ.get("DIGEST_EMAIL_FROM", "wshuai294@gmail.com")
EMAIL_TO = os.environ.get("DIGEST_EMAIL_TO", "wshuai294@gmail.com")
# Gmail: use an App Password, not your normal password
# https://support.google.com/accounts/answer/185833
SMTP_PASSWORD = os.environ.get("DIGEST_SMTP_PASSWORD", "")
SMTP_USER = os.environ.get("DIGEST_SMTP_USER", EMAIL_FROM)
SMTP_HOST = os.environ.get("DIGEST_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("DIGEST_SMTP_PORT", "587"))

# Optional: GitHub token for higher rate limit (https://github.com/settings/tokens)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Optional: NCBI API key for higher rate limit (https://www.ncbi.nlm.nih.gov/account/settings/)
NCBI_API_KEY = os.environ.get("NCBI_API_KEY", "")

# Time window: papers from the last N days (max 7 = one week)
DEFAULT_DAYS = 7
MAX_DAYS = 7

# How many items to fetch per source
MAX_PAPERS = int(os.environ.get("DIGEST_MAX_PAPERS", "15"))
MAX_REPOS = int(os.environ.get("DIGEST_MAX_REPOS", "10"))

# Report output (optional file path to also save report)
REPORT_PATH = os.environ.get("DIGEST_REPORT_PATH", "")

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent
