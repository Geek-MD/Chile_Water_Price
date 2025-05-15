import camelot
import json
import os

PDFS_DIR = "pdfs"
OUTPUT_JSON = "json/tariffs_data.json"

def parse_pdf_with_camelot(pdf_path, region, company, locality, pdf_url):
    result = {
        "cargo_fijo": None,
        "variables": {},
        "source_pdf": pdf_url
    }

    # Extraer tablas con detección de bordes (lattice)
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')

    for table in tables:
        df = table.df

        # Buscar Cargo fijo
        mask = df.apply(lambda row: row.astype(str).str.contains("Cargo fijo", case=False).any(), axis=1)
        cargo_rows = df[mask]
        for _, row in cargo_rows.iterrows():
            for item in row:
                if "Cargo fijo" in item:
                    parts = item.split()
                    for i, part in enumerate(parts):
                        if "fijo" in part and i+1 < len(parts):
                            candidate = parts[i+1].replace(",", ".").replace("$", "").strip()
                            if candidate.replace(".", "").isdigit():
                                result["cargo_fijo"] = candidate

        # Buscar Variables ($/m3) dentro de la tabla
        mask = df.apply(lambda row: row.astype(str).str.contains("Variables", case=False).any(), axis=1)
        variables_rows = df[mask]
        for _, row in variables_rows.iterrows():
            for i, cell in enumerate(row):
                if "variables" in cell.lower():
                    # Buscar a la derecha los valores de Variables
                    for j in range(i+1, len(row)):
                        name = row[i].strip()
                        value = row[j].replace(",", ".").replace("$", "").strip()
                        if value.replace(".", "").isdigit():
                            result["variables"][name] = value

    return result

def main():
    # Simular pdf_links (de tariff_siss_pdfs.json)
    pdf_links = {
        "Región de Arica y Parinacota": {
            "Aguas del Altiplano": {
                "Arica": {
                    "tarifa_vigente_pdf": "https://www.siss.gob.cl/path/to/altiplano_arica.pdf"
                }
            }
        }
    }

    result_data = {}

    for region, companies in pdf_links.items():
        result_data.setdefault(region, {})
        for company, localities in companies.items():
            result_data[region].setdefault(company, {})
            for locality, info in localities.items():
                pdf_url = info["tarifa_vigente_pdf"]
                pdf_filename = os.path.basename(pdf_url)
                pdf_path = os.path.join(PDFS_DIR, pdf_filename)

                print(f"Parsing {region} / {company} / {locality} with Camelot...")
                parsed_data = parse_pdf_with_camelot(pdf_path, region, company, locality, pdf_url)
                result_data[region][company][locality] = parsed_data

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"Tariffs data saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
