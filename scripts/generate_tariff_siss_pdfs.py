import os
import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SISS_URL = "https://www.siss.gob.cl/586/w3-propertyvalue-6385.html"
OUTPUT_JSON = "json/tariff_siss_pdfs.json"

def fetch_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"🔄 Cargando {SISS_URL} en navegador headless...")
        page.goto(SISS_URL, timeout=60000)
        page.wait_for_load_state("networkidle")
        content = page.content()
        browser.close()
    return content

def main():
    html_content = fetch_html()
    soup = BeautifulSoup(html_content, "html.parser")

    data = {}
    current_region = None
    current_company = None

    # Buscamos solo en la zona de contenido real
    for element in soup.find_all(["h3", "h4", "table"]):
        if element.name == "h3":
            current_region = element.get_text(strip=True)
            print(f"🗺️ Región: {current_region}")
            data.setdefault(current_region, {})
        elif element.name == "h4":
            current_company = element.get_text(strip=True)
            print(f"  🏢 Empresa: {current_company}")
            if current_region:
                data[current_region].setdefault(current_company, {})
        elif element.name == "table" and current_region and current_company:
            rows = element.find_all("tr")[1:]  # Saltar header

            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                locality = cols[0].get_text(strip=True)
                tarifa_cell = cols[1]

                link = tarifa_cell.find("a", href=True)
                if link and link["href"].lower().endswith(".pdf"):
                    pdf_url = link["href"]
                    pdf_url = pdf_url if pdf_url.startswith("http") else f"https://www.siss.gob.cl{pdf_url}"

                    print(f"    📄 Localidad: {locality} -> {pdf_url}")

                    data[current_region][current_company][locality] = {
                        "tarifa_vigente_pdf": pdf_url
                    }

    if not data:
        print("⚠️ No se encontraron localidades con PDFs.")
    else:
        os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Archivo generado: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
