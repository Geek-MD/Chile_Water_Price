import os
import json
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
        self._tariffs_data = {}

    @property
    def native_value(self):
        """Returns Variables primera instancia as main value."""
        variables = self._tariffs_data.get("variables", {})
        return variables.get("primera instancia", None)

    @property
    def extra_state_attributes(self):
        return {
            "region": self.region,
            "company": self.company,
            "locality": self.locality,
            **self._tariffs_data
        }

    async def async_update(self):
        """Load tariffs from pre-processed JSON."""
        if not os.path.exists(TARIFFS_FILE):
            self._tariffs_data = {"error": "No tariffs data file"}
            return

        with open(TARIFFS_FILE, "r", encoding="utf-8") as f:
            tariffs_data = json.load(f)

        try:
            data = tariffs_data[self.region][self.company][self.locality]
            self._tariffs_data = data
        except KeyError:
            self._tariffs_data = {"error": "Data not found"}
