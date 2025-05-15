import os
import json
import requests
import camelot

PDFS_DIR = "pdfs"
OUTPUT_JSON = "json/tariffs_data.json"

def parse_pdf(pdf_path, pdf_url):
    result = {
        "cargo_fijo": None,
        "variables": {},
        "source_pdf": pdf_url
    }

    print(f"Processing {pdf_path}...")

    tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')

    for table in tables:
        df = table.df

        for _, row in df.iterrows():
            row_data = " ".join(row.astype(str)).lower()

            # Cargo fijo
            if "cargo fijo" in row_data:
                for item in row:
                    if "cargo fijo" in item.lower():
                        parts = item.split()
                        for i, part in enumerate(parts):
                            if "fijo" in part.lower() and i+1 < len(parts):
                                value = parts[i+1].replace(",", ".").replace("$", "").strip()
                                if value.replace(".", "").isdigit():
                                    result["cargo_fijo"] = value

            # Variables
            if "variables" in row_data:
                for item in row:
                    if "variables" in item.lower():
                        continue
                    parts = item.split()
                    if len(parts) >= 2:
                        name = " ".join(parts[:-1])
                        value = parts[-1].replace(",", ".").replace("$", "").strip()
                        if value.replace(".", "").isdigit():
                            result["variables"][name] = value

    return result

def main():
    with open("json/tariff_siss_pdfs.json", "r", encoding="utf-8") as f:
        pdf_links = json.load(f)

    result_data = {}

    for region, companies in pdf_links.items():
        result_data.setdefault(region, {})
        for company, localities in companies.items():
            result_data[region].setdefault(company, {})
            for locality, info in localities.items():
                pdf_url = info["tarifa_vigente_pdf"]
                pdf_filename = os.path.basename(pdf_url)
                pdf_path = os.path.join(PDFS_DIR, pdf_filename)

                if not os.path.exists(pdf_path):
                    print(f"PDF {pdf_filename} not found in {PDFS_DIR}. Skipping...")
                    continue

                parsed_data = parse_pdf(pdf_path, pdf_url)
                result_data[region][company][locality] = parsed_data

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"Tariffs data saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
