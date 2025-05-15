import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig
import json
from .const import DOMAIN, TARIFFS_FILE

class SissTariffsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title=user_input["localidad"], data=user_input)

        # Leer datos desde tariffs.json
        with open(TARIFFS_FILE, "r", encoding="utf-8") as f:
            tariffs_data = json.load(f)

        regions = list(tariffs_data.keys())

        schema = vol.Schema({
            vol.Required("region"): vol.In(regions),
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_company(self, user_input=None):
        errors = {}

        region = self.context["region"]

        if user_input is not None:
            self.context["company"] = user_input["company"]
            return await self.async_step_locality()

        with open(TARIFFS_FILE, "r", encoding="utf-8") as f:
            tariffs_data = json.load(f)

        companies = list(tariffs_data[region].keys())

        schema = vol.Schema({
            vol.Required("company"): vol.In(companies),
        })

        return self.async_show_form(step_id="company", data_schema=schema, errors=errors)

    async def async_step_locality(self, user_input=None):
        errors = {}

        region = self.context["region"]
        company = self.context["company"]

        if user_input is not None:
            return self.async_create_entry(title=user_input["locality"], data={
                "region": region,
                "company": company,
                "locality": user_input["locality"],
            })

        with open(TARIFFS_FILE, "r", encoding="utf-8") as f:
            tariffs_data = json.load(f)

        localities = list(tariffs_data[region][company].keys())

        schema = vol.Schema({
            vol.Required("locality"): vol.In(localities),
        })

        return self.async_show_form(step_id="locality", data_schema=schema, errors=errors)
