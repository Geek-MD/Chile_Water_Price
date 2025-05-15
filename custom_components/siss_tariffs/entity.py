from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, TARIFFS_FILE
import json
import os

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

    @property
    def native_value(self):
        """Returns the URL to the PDF tariff (or future: real tariff value)."""
        if not os.path.exists(TARIFFS_FILE):
            return None

        with open(TARIFFS_FILE, "r", encoding="utf-8") as f:
            tariffs_data = json.load(f)

        try:
            pdf_url = tariffs_data[self.region][self.company][self.locality]["tarifa_vigente_pdf"]
            return pdf_url
        except KeyError:
            return None

    @property
    def extra_state_attributes(self):
        """Returns additional attributes."""
        return {
            "region": self.region,
            "company": self.company,
            "locality": self.locality,
        }
