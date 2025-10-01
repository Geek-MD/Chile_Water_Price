# scripts/parser.py

import os
from pathlib import Path
from extract_tarifa_data import extract_data_from_pdf  # Reutiliza el extractor ya probado
import json

PDF_DIR = Path("pdf")
JSON_DIR = Path("json")

JSON_DIR.mkdir(exist_ok=True)

for pdf_file in PDF_DIR.glob("*.pdf"):
    output_filename = JSON_DIR / f"{pdf_file.stem}.json"

    print(f"Procesando: {pdf_file.name}")
    try:
        data = extract_data_from_pdf(str(pdf_file))
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Guardado: {output_filename}")
    except Exception as e:
        print(f"❌ Error en {pdf_file.name}: {e}")
