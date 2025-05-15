import requests
import hashlib
import os
import json
from bs4 import BeautifulSoup
from .const import SISS_URL, HTML_FILE, TARIFFS_FILE

def get_sha256(content):
    return hashlib.sha256(content).hexdigest()

def ensure_html_and_parse():
    download_needed = False

    if not os.path.exists(HTML_FILE):
        download_needed = True
    else:
        current_content = open(HTML_FILE, "rb").read()
        current_sha = get_sha256(current_content)

        response = requests.get(SISS_URL, timeout=15)
        response.raise_for_status()
        new_content = response.content
        new_sha = get_sha256(new_content)

        if current_sha != new_sha:
            download_needed = True

    if download_needed:
        print(f"Updating {HTML_FILE}")
        with open(HTML_FILE, "wb") as f:
            f.write(new_content)
        parse_html_to_json(new_content)

def parse_html_to_json(content):
    soup = BeautifulSoup(content, "html.parser")

    data = {}
    current_region = None
    current_empresa = None

    for element in soup.find_all(["h3", "h4", "table"]):
        if element.name == "h3":
            current_region = element.get_text(strip=True)
            data.setdefault(current_region, {})
        elif element.name == "h4":
            current_empresa = element.get_text(strip=True)
            if current_region:
                data[current_region].setdefault(current_empresa, {})
        elif element.name == "table" and current_region and current_empresa:
            rows = element.find_all("tr")[1:]

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                localidad = cols[0].get_text(strip=True)
                tarifa_vigente_cell = cols[1]

                link = tarifa_vigente_cell.find("a", href=True)
                if link and link["href"].lower().endswith(".pdf"):
                    pdf_url = link["href"]

                    data[current_region][current_empresa][localidad] = {
                        "tarifa_vigente_pdf": pdf_url
                    }

    os.makedirs(os.path.dirname(TARIFFS_FILE), exist_ok=True)
    with open(TARIFFS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Tariffs JSON updated at {TARIFFS_FILE}")
