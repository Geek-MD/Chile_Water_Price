import os
import sys
import requests
import hashlib
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configuración
BASE_URL = "https://www.siss.gob.cl"
TARGET_URL = "https://www.siss.gob.cl/589/w3-propertyvalue-9034.html"
DIV_ID = "SISS23_pa_tarifas_vigentes"
PDF_DIR = "pdf"
DATA_DIR = "data"
LAST_MODIFIED_FILE = "last_modified.txt"
HASH_FILE = "page_hash.txt"
OUTPUT_JSON = os.path.join(DATA_DIR, "pdfs.json")

# Asegurar directorios
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def get_last_modified():
    """Obtiene la cabecera Last-Modified del recurso si existe"""
    try:
        response = requests.head(TARGET_URL, timeout=30, allow_redirects=True)
        return response.headers.get("Last-Modified")
    except requests.RequestException as e:
        print(f"⚠️ Error obteniendo encabezado Last-Modified: {e}")
        return None

def load_file(filepath):
    return open(filepath, "r").read().strip() if os.path.exists(filepath) else None

def save_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def hash_div_content(html):
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find("div", {"id": DIV_ID})
    return hashlib.sha256(div.encode("utf-8")).hexdigest() if div else None

def normalize_text(text):
    return text.replace('\xa0', ' ').strip()

def get_pdf_links(html):
    soup = BeautifulSoup(html, "html.parser")
    data = []
    h3_blocks = soup.find_all("h3", class_="titulo")

    for h3 in h3_blocks:
        empresa = normalize_text(h3.text.split(" - ")[0])
        table = h3.find_next("table")
        if not table:
            continue

        for row in table.find_all("tr")[1:]:  # Saltar encabezado
            cols = row.find_all("td")
            if len(cols) >= 3:
                pdf_tag = cols[1].find("a")
                if pdf_tag and pdf_tag["href"].endswith(".pdf"):
                    pdf_url = urljoin(BASE_URL, pdf_tag["href"])
                    nombre_archivo = os.path.basename(pdf_tag["href"])
                    data.append({
                        "empresa": empresa,
                        "archivo": nombre_archivo,
                        "url": pdf_url
                    })
    return data

def descargar_pdf(item):
    nombre = item["archivo"]
    destino = os.path.join(PDF_DIR, nombre)
    if os.path.exists(destino):
        print(f"Ya existe: {nombre}")
        return
    try:
        r = requests.get(item["url"], timeout=30)
        r.raise_for_status()
        with open(destino, "wb") as f:
            f.write(r.content)
        print(f"Descargado: {nombre}")
    except requests.RequestException as e:
        print(f"❌ Error descargando {nombre}: {e}")

def main():
    print("🔎 Verificando cambios en la página de tarifas...")

    # Obtener cabecera Last-Modified
    current_last_modified = get_last_modified()
    saved_last_modified = load_file(LAST_MODIFIED_FILE)

    # Obtener HTML completo con timeout alto
    try:
        response = requests.get(TARGET_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️ Error al conectar con la página de la SISS: {e}")
        sys.exit(0)  # Salir sin error para no romper el workflow

    html = response.text
    current_hash = hash_div_content(html)
    saved_hash = load_file(HASH_FILE)

    # Comprobar si hay cambios
    if current_last_modified == saved_last_modified and current_hash == saved_hash:
        print("✅ Sin cambios detectados.")
        sys.exit(0)

    print("⚠️ Cambios detectados. Procesando PDFs...")
    pdfs = get_pdf_links(html)

    for item in pdfs:
        descargar_pdf(item)

    save_file(OUTPUT_JSON, json.dumps(pdfs, indent=2, ensure_ascii=False))
    if current_last_modified:
        save_file(LAST_MODIFIED_FILE, current_last_modified)
    if current_hash:
        save_file(HASH_FILE, current_hash)

    print(f"Proceso finalizado. {len(pdfs)} PDFs registrados en {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
