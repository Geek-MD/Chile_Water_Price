import os
import json
import requests
import fitz  # PyMuPDF

PDFS_DIR = "pdfs"
JSON_FILE = "json/tarifas_siss_pdfs.json"
OUTPUT_FILE = "json/tarifas_siss_data.json"

def download_pdf(url, path):
    if not os.path.exists(path):
        response = requests.get(url)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)

def extract_pdf_data(pdf_path):
    doc = fitz.open(pdf_path)
    text_data = []

    for page in doc:
        text = page.get_text("text")
        text_data.extend(text.split("\n"))

    return text_data

def detect_structure(text_lines):
    for line in text_lines[:50]:
        if "Tramo" in line and "Valor" in line:
            return "tabla"
        if "m3" in line and "$" in line:
            return "bloque"
    return "desconocido"

def parse_table_structure(text_lines):
    data = []
    capture = False

    for line in text_lines:
        if "Tramo" in line and "Valor" in line:
            capture = True
            continue
        if capture:
            parts = line.split()
            if len(parts) >= 2 and "$" in line:
                data.append({
                    "tramo": " ".join(parts[:-1]),
                    "valor": parts[-1]
                })

    return data

def parse_block_structure(text_lines):
    data = []
    for line in text_lines:
        if "m3" in line and "$" in line:
            parts = line.split()
            tramo = " ".join(parts[:-1])
            valor = parts[-1]
            data.append({"tramo": tramo, "valor": valor})
    return data

def process_pdf(pdf_path):
    text_lines = extract_pdf_data(pdf_path)
    structure = detect_structure(text_lines)

    if structure == "tabla":
        return parse_table_structure(text_lines)
    elif structure == "bloque":
        return parse_block_structure(text_lines)
    else:
        return []

def main():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        tarifas_links = json.load(f)

    result = {}

    for region, empresas in tarifas_links.items():
        result.setdefault(region, {})
        for empresa, localidades in empresas.items():
            result[region].setdefault(empresa, {})
            for localidad, info in localidades.items():
                pdf_url = info["tarifa_vigente_pdf"]
                pdf_filename = os.path.basename(pdf_url)
                pdf_path = os.path.join(PDFS_DIR, pdf_filename)

                print(f"Procesando {region} - {empresa} - {localidad}...")

                download_pdf(pdf_url, pdf_path)
                tarifas_data = process_pdf(pdf_path)

                result[region][empresa][localidad] = {
                    "tarifas": tarifas_data,
                    "source_pdf": pdf_url
                }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Datos extraídos en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
