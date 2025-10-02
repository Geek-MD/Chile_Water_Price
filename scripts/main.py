import json
import sys
import subprocess
from pathlib import Path

# Absolute path to config.json
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

# Validate config.json exists
if not CONFIG_PATH.exists():
    print("[ERROR] config.json file is missing. Container will stop.")
    sys.exit(1)

# Load config
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# Extract and validate GitHub credentials
GITHUB_USERNAME = config.get("GITHUB_USERNAME", "")
GITHUB_TOKEN = config.get("GITHUB_TOKEN", "")

if GITHUB_USERNAME == "GITHUB_USERNAME" or GITHUB_TOKEN == "GITHUB_TOKEN":
    print("[ERROR] GITHUB_USERNAME and/or GITHUB_TOKEN are not configured in config.json.")
    print("→ Please edit config.json with valid credentials and restart the container.")
    sys.exit(1)

print(f"[INFO] GitHub credentials loaded for user: {GITHUB_USERNAME}")

# Paths to intermediate JSONs
BASE_DIR = Path(__file__).resolve().parent
NEW_PDFS_PATH = BASE_DIR / "new_pdfs.json"
PDF_URLS_PATH = BASE_DIR / "pdf_urls.json"

# Function to run a script and print results
def run_script(script_name: str) -> bool:
    print(f"[INFO] Running {script_name}...")
    result = subprocess.run(["python", script_name], cwd=BASE_DIR)
    if result.returncode == 0:
        print(f"[INFO] {script_name} executed successfully.")
        return True
    else:
        print(f"[ERROR] {script_name} failed with exit code {result.returncode}.")
        return False

# ─────────────────────────────
# 1. Run scraper.py
# ─────────────────────────────
if not run_script("scraper.py"):
    print("[FATAL] scraper.py failed. Aborting process.")
    sys.exit(1)

# ─────────────────────────────
# 2. Check if PDF URLs changed → Run download_pdfs.py
# ─────────────────────────────
if PDF_URLS_PATH.exists():
    with open(PDF_URLS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("has_changes", False):
        if not run_script("download_pdfs.py"):
            print("[FATAL] download_pdfs.py failed. Aborting process.")
            sys.exit(1)
    else:
        print("[INFO] No changes in PDF URLs. Skipping download_pdfs.py.")
else:
    print("[WARN] pdf_urls.json not found. Assuming first run.")
    if not run_script("download_pdfs.py"):
        print("[FATAL] download_pdfs.py failed. Aborting process.")
        sys.exit(1)

# ─────────────────────────────
# 3. Check if new PDFs exist → Run parse_pdfs.py
# ─────────────────────────────
if NEW_PDFS_PATH.exists():
    with open(NEW_PDFS_PATH, "r", encoding="utf-8") as f:
        new_files = json.load(f).get("new_pdfs", [])
    if new_files:
        if not run_script("parse_pdfs.py"):
            print("[FATAL] parse_pdfs.py failed. Aborting process.")
            sys.exit(1)
    else:
        print("[INFO] No new PDFs to parse. Skipping parse_pdfs.py.")
else:
    print("[WARN] new_pdfs.json not found. Skipping parse_pdfs.py.")
