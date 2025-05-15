import os
import json
import requests
import fitz  # PyMuPDF
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, TARIFFS_FILE

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN]["coordinator"]

    region = entry.data["region"]
    company = entry.data["company"]
    locality = entry.data["locality"]

    entity = SissTariffEntity(coordinator, region, company, locality)
    async_add_entities([entity])

class SissTariffEntity(CoordinatorEntity, Entity):
    def __init__(self, coordinator, region, company, locality):
        super().__init__(coordinator)
        self._attr_unique_id = f"siss_tariff_{region}_{company}_{locality}".replace(" ", "_").lower()
        self._attr_name = f"{locality} Tariff"
        self.region = region
        self.company = company
        self.locality = locality
        self._attr_icon = "mdi:water"
        self._tariff_value = None

    @property
    def native_value(self):
        """Returns the current tariff value in CLP."""
        return self._tariff_value

    @property
    def extra_state_attributes(self):
        return {
            "region": self.region,
            "company": self.company,
            "locality": self.locality,
        }

    async def async_update(self):
        """Called when coordinator updates."""
        self._tariff_value = await self.hass.async_add_executor_job(self.get_tariff_from_pdf)

    def get_tariff_from_pdf(self):
        if not os.path.exists(TARIFFS_FILE):
            return None

        with open(TARIFFS_FILE, "r", encoding="utf-8") as f:
            tariffs_data = json.load(f)

        try:
            pdf_url = tariffs_data[self.region][self.company][self.locality]["tarifa_vigente_pdf"]
        except KeyError:
            return None

        pdf_dir = os.path.join(os.path.dirname(TARIFFS_FILE), "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_file = os.path.join(pdf_dir, f"{self.region}_{self.company}_{self.locality}.pdf".replace(" ", "_"))

        # Descargar PDF si no existe localmente
        if not os.path.exists(pdf_file):
            try:
                response = requests.get(pdf_url, timeout=15)
                response.raise_for_status()
                with open(pdf_file, "wb") as f:
                    f.write(response.content)
            except Exception as e:
                return f"Error downloading PDF: {e}"

        # Parsear PDF de forma flexible
        try:
            doc = fitz.open(pdf_file)
            candidates = []

            for page in doc:
                text = page.get_text("text")
                lines = text.split("\n")

                for line in lines:
                    clean_line = line.strip().replace("\xa0", " ").replace("\t", " ").lower()

                    if any(keyword in clean_line for keyword in ["m3", "metros cúbicos", "consumo", "tarifa", "valor", "$"]):
                        words = clean_line.split()
                        for word in words:
                            if word.startswith("$") and any(char.isdigit() for char in word):
                                candidates.append({
                                    "line": line.strip(),
                                    "value": word,
                                    "score": self.calculate_score(clean_line)
                                })

            if not candidates:
                return "Tariff not found"

            # Elegir el candidato con mayor score
            best_candidate = sorted(candidates, key=lambda x: x["score"], reverse=True)[0]
            return best_candidate["value"]

        except Exception as e:
            return f"Error parsing PDF: {e}"

    def calculate_score(self, line):
        score = 0
        if "m3" in line: score += 5
        if "metros cúbicos" in line: score += 5
        if "consumo" in line: score += 3
        if "tarifa" in line: score += 3
        if "valor" in line: score += 2
        if "$" in line: score += 2
        return score
