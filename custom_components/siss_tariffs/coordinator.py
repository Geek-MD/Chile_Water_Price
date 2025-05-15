from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .tariff_fetcher import ensure_html_and_parse
from .const import DOMAIN, UPDATE_INTERVAL_DAYS

_LOGGER = logging.getLogger(__name__)

async def async_setup_coordinator(hass):
    coordinator = SissTariffsCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})["coordinator"] = coordinator
    return coordinator

class SissTariffsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass):
        super().__init__(
            hass,
            _LOGGER,
            name="SISS Tariffs Coordinator",
            update_interval=timedelta(days=UPDATE_INTERVAL_DAYS)
        )

    async def _async_update_data(self):
        try:
            _LOGGER.info("Checking for SISS tariffs update...")
            await self.hass.async_add_executor_job(ensure_html_and_parse)
        except Exception as err:
            raise UpdateFailed(f"Failed to update SISS tariffs: {err}")
