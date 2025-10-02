import os
import json
import re
import pdfplumber
from pathlib import Path
from dateutil import parser as date_parser
from datetime import datetime

# Define base and output directories
BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "pdfs"
JSON_DIR = BASE_DIR / "json"
NEW_PDFS_FILE = BASE_DIR / "new_pdfs.json"

# Output structure order
SECTIONS_ORDER = [
    "informacion_general",
    "cargo_fijo",
    "variables",
    "riles",
    "otros_cobros",
    "corte",
    "reposicion",
    "aportes_financiamiento_reembolsable",
    "revision_proyectos",
    "verificacion_medidores"
]

# Keywords used to identify section transitions
SECTION_KEYWORDS = {
    "cargo_fijo": ["cargo fijo", "cargo mensual"],
    "variables": ["variable", "consumo", "tarifa por m3", "m³"],
    "riles": ["riles", "residuos industriales líquidos"],
    "otros_cobros": ["otros cobros", "cobros adicionales"],
    "corte": ["corte", "suspensión del servicio"],
    "reposicion": ["reposición", "reconexion"],
    "aportes_financiamiento_reembolsable": ["aporte", "financiamiento", "reembolsable"],
    "revision_proyectos": ["revisión de proyectos", "proyectos sanitarios"],
    "verificacion_medidores": ["verificación de medidores", "medidores"]
}

def parse_number(value):
    try:
        # Replace comma with dot for decimal conversion
        value = value.replace(",", ".").replace("$", "").replace("CLP", "").strip()
        return float(re.findall(r"[-+]?\d*\.\d+|\d+", value)[0])
    except:
        return value.strip()

def parse_date(text):
    try:
        dt = date_parser.parse(text, dayfirst=True, fuzzy=True)
        return dt.strftime("%d/%m/%Y")
    except:
        return None

def detect_section(keywords_map, line):
    lower = line.lower()
    for section, keywords in keywords_map.items():
        for kw in keywords:
            if kw in lower:
                return section
    return None

def extract_data_from_pdf(pdf_path):
    data = {section: {} for section in SECTIONS_ORDER}
    current_section = "informacion_general"
    data[current_section] = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split("\n")
            for line in lines:
                # Detect section changes
                detected = detect_section(SECTION_KEYWORDS, line)
                if detected:
                    current_section = detected
                    continue

                # Extract key-value pairs
                if ":" in line:
                    key, val = line.split(":", 1)
                elif "-" in line:
                    key, val = line.split("-", 1)
                else:
                    continue

                key = key.strip()
                val = val.strip()

                # Format date or parse as float
                parsed_val = parse_date(val) or parse_number(val)

                # If current section not defined (failsafe)
                if current_section not in data:
                    data[current_section] = {}

                data[current_section][key] = parsed_val

    return data

def save_json(output_path, data):
    # Ensure proper section order in output
    ordered_data = {section: data.get(section, {}) for section in SECTIONS_ORDER}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ordered_data, f, indent=2, ensure_ascii=False)

def main():
    if not PDF_DIR.exists() or not NEW_PDFS_FILE.exists():
        print("Missing directories or new_pdfs.json file.")
        return

    with open(NEW_PDFS_FILE, "r", encoding="utf-8") as f:
        pdf_files = json.load(f)

    for pdf_filename in pdf_files:
        pdf_path = PDF_DIR / pdf_filename
        output_filename = pdf_filename.replace(".pdf", ".json")
        output_path = JSON_DIR / output_filename

        print(f"Processing {pdf_filename}...")
        try:
            parsed_data = extract_data_from_pdf(pdf_path)
            save_json(output_path, parsed_data)
            print(f"Saved: {output_filename}")
        except Exception as e:
            print(f"Error processing {pdf_filename}: {e}")

if __name__ == "__main__":
    main()
