import requests
import hashlib
import os

SISS_URL = "https://www.siss.gob.cl/586/w3-propertyvalue-6385.html"
OUTPUT_FILE = "html/tariff_siss_source.html"

def get_sha256(content):
    return hashlib.sha256(content).hexdigest()

def main():
    response = requests.get(SISS_URL, timeout=15)
    response.raise_for_status()
    new_content = response.content
    new_sha = get_sha256(new_content)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Compara con archivo local si existe
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "rb") as f:
            current_content = f.read()
        current_sha = get_sha256(current_content)

        if current_sha == new_sha:
            print("No hay cambios en la página SISS.")
            return  # Nada que hacer

    # Si hay cambios o no existe, sobrescribe
    with open(OUTPUT_FILE, "wb") as f:
        f.write(new_content)

    print(f"Archivo HTML actualizado en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
