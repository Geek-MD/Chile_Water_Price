import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import subprocess  # To call download_pdfs.py if needed

BASE_DIR = Path(__file__).resolve().parent
CONSTANTS_PATH = BASE_DIR / "constants.json"

# Load constants from JSON file
with open(CONSTANTS_PATH, "r", encoding="utf-8") as f:
    CONSTANTS = json.load(f)

BASE_URL = CONSTANTS["siss_site"]
TARIFAS_URL = CONSTANTS["tarifas_url"]
PDFS_JSON_PATH = "/data/pdfs.json"
HASH_FILE = "/data/hash.json"

# Get HTML from the SISS page
response = requests.get(TARIFAS_URL)
response.encoding = "utf-8"
html = response.text

# Calculate the current hash of the HTML
html_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()

# Load previous hash if exists
previous_hash = None
if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        previous_data = json.load(f)
        previous_hash = previous_data.get("hash")

# Skip if no changes
if previous_hash == html_hash:
    print("🔁 No changes detected. Exiting...")
    exit(0)

# Parse the HTML
soup = BeautifulSoup(html, "html.parser")

# Heuristic: look for a div with id containing "tarifas_vigentes"
container = soup.find("div", id=lambda x: x and "tarifas_vigentes" in x)
if not container:
    print("❌ Could not find tarifas_vigentes container.")
    exit(1)

results = []
current_company = None

# Iterate over blocks to extract company name and PDF URLs
for block in container.find_all(["h3", "table"]):
    if block.name == "h3":
        company_name = block.get_text(strip=True).replace(" - Tarifas vigentes", "")
        current_company = {"empresa": company_name, "pdfs": []}
    elif block.name == "table" and current_company:
        for row in block.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                link = cols[1].find("a")
                if link and ".pdf" in link.get("href", ""):
                    full_url = urljoin(TARIFAS_URL, link["href"])
                    current_company["pdfs"].append(full_url)
        if current_company["pdfs"]:
            results.append(current_company)

# Save JSON output
with open(PDFS_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# Save the new hash
with open(HASH_FILE, "w", encoding="utf-8") as f:
    json.dump({"hash": html_hash}, f, indent=2)

print(f"✅ {len(results)} companies processed. JSON saved to {PDFS_JSON_PATH}")

# Call download_pdfs.py if changes were detected
try:
    print("📥 Changes detected. Downloading PDFs...")
    subprocess.run(["python3", str(BASE_DIR / "download_pdfs.py")], check=True)
except subprocess.CalledProcessError as e:
    print(f"❌ Error executing download_pdfs.py: {e}")
