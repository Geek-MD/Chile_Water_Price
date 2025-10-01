import hashlib
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import json

URL = "https://www.siss.gob.cl/589/w3-propertyvalue-9034.html"
BASE_URL = "https://www.siss.gob.cl"
HEADERS_FILE = "last_modified.txt"
HASH_FILE = "page_hash.txt"
OUTPUT_FILE = "data/urls.json"

def get_last_modified():
    response = requests.head(URL, allow_redirects=True)
    return response.headers.get("Last-Modified")

def get_page_content():
    response = requests.get(URL)
    response.encoding = "utf-8"
    return response.text

def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_previous(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None

def save(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(data)

def extract_pdf_urls(html):
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", id="SISS23_pa_tarifas_vigentes")
    data = []

    if not container:
        return data

    current_company = None

    for tag in container.find_all(["h3", "tr"]):
        if tag.name == "h3":
            current_company = tag.get_text(strip=True).replace(" - Tarifas vigentes", "")
        elif tag.name == "tr" and current_company:
            columns = tag.find_all("td")
            if len(columns) >= 2:
                link_tag = columns[1].find("a")
                if link_tag and "href" in link_tag.attrs:
                    href = link_tag["href"]
                    if href.lower().endswith(".pdf"):
                        full_url = urljoin(BASE_URL, href)
                        data.append({
                            "empresa": current_company,
                            "url": full_url
                        })

    return data

def save_json(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    print("Checking last modified header...")
    last_modified = get_last_modified()
    old_last_modified = load_previous(HEADERS_FILE)

    html = get_page_content()
    current_hash = compute_hash(html)
    old_hash = load_previous(HASH_FILE)

    if last_modified == old_last_modified and current_hash == old_hash:
        print("No changes detected on the page.")
        return

    print("Changes detected! Scraping new data...")

    pdf_data = extract_pdf_urls(html)
    save_json(pdf_data, OUTPUT_FILE)

    save(HEADERS_FILE, last_modified if last_modified else "")
    save(HASH_FILE, current_hash)

    print(f"Scraping complete. Found {len(pdf_data)} PDFs.")

if __name__ == "__main__":
    main()
