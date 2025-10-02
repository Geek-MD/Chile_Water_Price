import os
import json
import hashlib
import requests
from pathlib import Path
from urllib.parse import urlparse

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path("/data")
PDFS_JSON_PATH = DATA_DIR / "pdfs.json"
HASH_FILE = DATA_DIR / "hash.json"
PDFS_HASH_KEY = "pdfs_hash"
NEW_PDFS_PATH = DATA_DIR / "new_pdfs.json"
PDFS_DIR = DATA_DIR / "pdfs"
PDFS_DIR.mkdir(parents=True, exist_ok=True)

# Helper: calculate SHA256 hash of a file
def calculate_file_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# Helper: download a file from a URL
def download_file(url, output_path):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

# Load pdfs.json
if not PDFS_JSON_PATH.exists():
    print("❌ pdfs.json not found.")
    exit(1)

with open(PDFS_JSON_PATH, "r", encoding="utf-8") as f:
    pdfs_data = json.load(f)

# Load or initialize hash file
previous_hash = None
if HASH_FILE.exists():
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        previous_hash = json.load(f).get(PDFS_HASH_KEY)

# Calculate new hash
new_hash = hashlib.sha256(json.dumps(pdfs_data, sort_keys=True).encode("utf-8")).hexdigest()

# Skip if no changes
if previous_hash == new_hash:
    print("🔁 No new PDFs to download.")
    exit(0)

print("📥 Changes detected. Downloading PDFs...")

# Download new PDFs
downloaded_files = []

for company in pdfs_data:
    for url in company.get("pdfs", []):
        filename = os.path.basename(urlparse(url).path)
        filepath = PDFS_DIR / filename

        if filepath.exists():
            continue

        try:
            download_file(url, filepath)
            downloaded_files.append(filename)
            print(f"✅ Downloaded: {filename}")
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")

# Update hash file
with open(HASH_FILE, "w", encoding="utf-8") as f:
    json.dump({PDFS_HASH_KEY: new_hash}, f, indent=2)

# Save list of new files
with open(NEW_PDFS_PATH, "w", encoding="utf-8") as f:
    json.dump(downloaded_files, f, indent=2)

print(f"📦 Download complete. {len(downloaded_files)} new files saved to {PDFS_DIR}")
print(f"📝 List of new files saved to {NEW_PDFS_PATH}")
