import os
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter, Retry

# URL objetivo y archivos auxiliares
TARGET_URL = "https://www.siss.gob.cl/589/w3-propertyvalue-9034.html"
LAST_HASH_FILE = "scripts/last_page_hash.txt"
PDF_DIR = "pdfs"

# User-Agent personalizado para evitar bloqueos por scraping
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
    )
}

# Sesión con retry y backoff
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
)
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))

def get_last_modified_header():
    try:
        response = session.head(TARGET_URL, timeout=30, headers=HEADERS, allow_redirects=True)
        last_modified = response.headers.get("Last-Modified")
        if last_modified:
            print(f"📅 Última modificación reportada por el servidor: {last_modified}")
        else:
            print("⚠️ No se encontró cabecera Last-Modified en la respuesta HTTP.")
    except requests.RequestException as e:
        print(f"⚠️ Error obteniendo encabezado Last-Modified: {e}")

def calculate_page_hash(html_content):
    return hashlib.sha256(html_content.encode("utf-8")).hexdigest()

def load_last_hash():
    if os.path.exists(LAST_HASH_FILE):
        with open(LAST_HASH_FILE, "r") as f:
            return f.read().strip()
    return None

def save_current_hash(page_hash):
    os.makedirs(os.path.dirname(LAST_HASH_FILE), exist_ok=True)
    with open(LAST_HASH_FILE, "w") as f:
        f.write(page_hash)

def download_pdfs(soup):
    os.makedirs(PDF_DIR, exist_ok=True)
    count = 0
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(".pdf"):
            pdf_url = urljoin(TARGET_URL, href)
            pdf_filename = pdf_url.split("/")[-1]
            pdf_path = os.path.join(PDF_DIR, pdf_filename)

            if os.path.exists(pdf_path):
                continue  # Skip already downloaded

            try:
                print(f"⬇️  Descargando: {pdf_filename}")
                response = session.get(pdf_url, timeout=60, headers=HEADERS)
                with open(pdf_path, "wb") as f:
                    f.write(response.content)
                count += 1
            except requests.RequestException as e:
                print(f"❌ Error descargando {pdf_url}: {e}")
    print(f"✅ PDFs descargados nuevos: {count}")

def main():
    print("🔎 Verificando cambios en la página de tarifas...")

    get_last_modified_header()

    try:
        response = session.get(TARGET_URL, timeout=30, headers=HEADERS)
        html_content = response.text
    except requests.RequestException as e:
        print(f"⚠️ Error al conectar con la página de la SISS: {e}")
        return

    current_hash = calculate_page_hash(html_content)
    last_hash = load_last_hash()

    if current_hash == last_hash:
        print("🟢 La página no ha cambiado desde la última ejecución. Nada que hacer.")
        return

    print("🟡 La página ha cambiado. Procesando...")
    soup = BeautifulSoup(html_content, "html.parser")
    download_pdfs(soup)
    save_current_hash(current_hash)
    print("✅ Proceso finalizado. Hash actualizado.")

if __name__ == "__main__":
    main()
