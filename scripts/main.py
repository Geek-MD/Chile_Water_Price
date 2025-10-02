#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

# -----------------------------
# Main orchestrator script
# This script runs the three stages in sequence:
# 1. Scraper (scraper.py)
# 2. Download PDFs (download_pdfs.py) only if changes detected
# 3. Parse PDFs (parse_pdfs.py) only if new PDFs downloaded
# -----------------------------

# Define paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path("/data")
PDFS_JSON = DATA_DIR / "pdfs.json"
NEW_PDFS_JSON = DATA_DIR / "new_pdfs.json"
DOWNLOADED_PDFS_DIR = DATA_DIR / "pdfs"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADED_PDFS_DIR.mkdir(parents=True, exist_ok=True)

# Run scraper.py
print("▶ Running scraper.py...")
subprocess.run(["python3", str(BASE_DIR / "scraper.py")], check=True)

# If there is a new_pdfs.json created, run download_pdfs.py
if NEW_PDFS_JSON.exists():
    print("▶ New PDFs detected. Running download_pdfs.py...")
    subprocess.run(["python3", str(BASE_DIR / "download_pdfs.py")], check=True)

    # After downloading PDFs, run parse_pdfs.py
    print("▶ Running parse_pdfs.py for new PDFs...")
    subprocess.run(["python3", str(BASE_DIR / "parse_pdfs.py")], check=True)
else:
    print("✅ No changes detected. Exiting.")
