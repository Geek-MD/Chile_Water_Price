import json
import logging
import hashlib
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Ensure folders exist before logging
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Configure logging to file
logging.basicConfig(
    filename="logs/scraper.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Constants
BASE_URL = "https://www.siss.gob.cl"
DEFAULT_TARIFAS_URL = f"{BASE_URL}/589/w3-propertyvalue-9034.html"
META_FILE = "output/siss_tarifas_meta.json"
PDF_LINKS_FILE = "output/pdf_links.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SISS-Tarifas-Scraper/1.0; +https://github.com/Geek-MD/Chile_Water_Price)"
}


def load_meta():
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_meta(meta):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def get_last_modified_and_hash(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        last_modified = response.headers.get("Last-Modified", None)
        page_hash = hashlib.sha256(response.content).hexdigest()
        return last_modified, page_hash, response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logging.warning("Received 404 Not Found for %s", url)
            return "404", None, None
        else:
            logging.error("HTTP error: %s", e)
            raise
    except Exception as e:
        logging.error("Error fetching page: %s", e)
        raise


def fallback_discover_tarifas_url():
    logging.info("Executing fallback routine to locate 'Tarifas Vigentes' page...")

    try:
        homepage = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        homepage.raise_for_status()
        soup = BeautifulSoup(homepage.text, "html.parser")

        info_link_tag = soup.find("a", string=lambda x: x and "Información del Sector Sanitario" in x)
        if not info_link_tag:
            raise ValueError("No 'Información del Sector Sanitario' link found")

        info_url = BASE_URL + info_link_tag.get("href")
        logging.info("Found 'Información del Sector Sanitario' URL: %s", info_url)

        info_page = requests.get(info_url, headers=HEADERS, timeout=30)
        info_page.raise_for_status()
        info_soup = BeautifulSoup(info_page.text, "html.parser")

        tarifas_link_tag = info_soup.find("a", string=lambda x: x and "Tarifas Vigentes" in x)
        if not tarifas_link_tag:
            raise ValueError("No 'Tarifas Vigentes' link found")

        tarifas_url = BASE_URL + tarifas_link_tag.get("href")
        logging.info("Discovered new Tarifas Vigentes URL: %s", tarifas_url)
        return tarifas_url

    except Exception as e:
        logging.error("Fallback routine failed: %s", e)
        raise


def extract_pdf_links(html):
    soup = BeautifulSoup(html, "html.parser")
    pdf_links = []

    container = soup.find("div", id="recuadros_articulo_3455")
    if not container:
        raise ValueError("Could not find container with id 'recuadros_articulo_3455'")

    for link in container.find_all("a", href=True):
        href = link["href"]
        if href.endswith(".pdf"):
            name = link.get_text(strip=True)
            full_url = BASE_URL + href if href.startswith("/") else href
            pdf_links.append({"name": name, "url": full_url})

    return pdf_links


def save_pdf_links(links):
    with open(PDF_LINKS_FILE, "w", encoding="utf-8") as f:
        json.dump(links, f, indent=2, ensure_ascii=False)


def main():
    meta = load_meta()
    current_url = meta.get("tarifas_url", DEFAULT_TARIFAS_URL)

    logging.info("Checking Tarifas Vigentes page: %s", current_url)
    last_modified, page_hash, html = get_last_modified_and_hash(current_url)

    if last_modified == "404":
        logging.warning("Page not found, executing fallback...")
        current_url = fallback_discover_tarifas_url()
        last_modified, page_hash, html = get_last_modified_and_hash(current_url)

    previous_hash = meta.get("hash")
    previous_last_modified = meta.get("last_modified")

    if last_modified == previous_last_modified and page_hash == previous_hash:
        logging.info("No changes detected in Tarifas Vigentes page. Exiting.")
        return

    logging.info("Change detected! Updating records...")
    pdf_links = extract_pdf_links(html)
    save_pdf_links(pdf_links)

    meta.update({
        "tarifas_url": current_url,
        "last_checked": datetime.utcnow().isoformat(),
        "last_modified": last_modified,
        "hash": page_hash,
        "pdf_count": len(pdf_links)
    })

    save_meta(meta)
    logging.info("Updated metadata and PDF link list.")


if __name__ == "__main__":
    main()
