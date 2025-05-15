import requests
from bs4 import BeautifulSoup
import json
import os
import time

SISS_URL = "https://www.siss.gob.cl/586/w3-propertyvalue-6385.html"
OUTPUT_FILE = "json/tariff_siss_pdfs.json"

def fetch_tarifas_links():
    retries = 3
    backoff = 5  # segundos

    for attempt in range(1, retries + 1):
        try:
            print(f"Intento {attempt} de {retries}: solicitando {SISS_URL}")
            response = requests.get(SISS_URL, timeout=15)
            response.raise_for_status()
            break  # Éxito
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            print(f"Timeout al conectar con SISS en intento {attempt}. Retrying in {backoff} seconds...")
            time.sleep(backoff)
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con SISS: {e}")
            raise SystemExit(1)
    else:
        print("No se pudo conectar con SISS después de varios intentos.")
        raise SystemExit(1)

    soup = BeautifulSoup(response.content, "html.parser")

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
                    pdf_url = requests.compat.urljoin(SISS_URL, link["href"])

                    data[current_region][current_empresa][localidad] = {
                        "tarifa_vigente_pdf": pdf_url
                    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"JSON generado en {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_tarifas_links()
