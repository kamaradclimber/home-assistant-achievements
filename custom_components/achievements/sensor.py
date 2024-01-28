import logging

from collections.abc import Callable
from datetime import timedelta, datetime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from datetime import timedelta
from homeassistant.helpers.storage import Store
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import EntityCategory
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)

from .const import DOMAIN
from dataclasses import dataclass

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    main_sensor = AchievementCountSensorEntity(hass, entry, async_add_entities)

    async_add_entities([main_sensor])


def parse_date(string):
    try:
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%f%z")
    except Exception:
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S%z")


@dataclass(frozen=True, kw_only=True)
class GeoveloSensorEntityDescription(SensorEntityDescription):
    on_receive: Callable | None = None
    monthly_utility: bool = False


class AchievementCountSensorEntity(SensorEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
    ):
        super().__init__()
        self.config_entry = config_entry
        self.hass = hass
        self._async_add_entities = async_add_entities
        self._attr_name = "Achievement count"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_unique_id = f"achievements-{config_entry.entry_id}"

        self._attr_device_info = DeviceInfo(
            name=f"Achievements",
            entry_type=DeviceEntryType.SERVICE,
            identifiers={
                (
                    DOMAIN,
                    str(config_entry.entry_id),
                )
            },
        )

    @callback
    async def async_added_to_hass(self):
        await super().async_added_to_hass()
