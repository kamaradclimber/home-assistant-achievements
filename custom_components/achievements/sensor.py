import logging

from typing import Optional
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
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
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
class AchievementDescription(BinarySensorEntityDescription):
    config_entry: ConfigEntry
    granted_on: datetime
    description: str
    source: str


class AchievementSensor(BinarySensorEntity):
    def __init__(self, description):
        super().__init__()
        self.entity_description = description
        self._attr_unique_id = f"achievement.{description.key}"
        # if the achievement is created, it is on
        self._attr_is_on = True
        self._attr_icon = "mdi:medal-outline"
        self._attr_extra_state_attributes = {
            "granted_on": description.granted_on,
            "description": description.description,
            "source": description.source,
        }
        self._attr_device_info = DeviceInfo(
            name=f"Achievements",
            entry_type=DeviceEntryType.SERVICE,
            identifiers={
                (
                    DOMAIN,
                    str(description.config_entry.entry_id),
                )
            },
        )


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

        def receive_achievement(event):
            _LOGGER.info(f"Received event: {event}")
            self.declare_achievement(event)

        self._stop_listen = self.hass.bus.async_listen(
            "achievement_granted", receive_achievement
        )

    def validate_achievement(self, achievement):
        for key in ["title", "source", "description", "id"]:
            if key not in achievement:
                raise InvalidAchievementEvent(f"Achievement must have a {key}")

    def declare_achievement(self, event):
        achievement = event.data["achievement"]
        self.validate_achievement(achievement)
        granted_on = datetime.now()
        if "granted_on" in achievement:
            granted_on = datetime.strptime(
                achievement["granted_on"], "%Y-%m-%dT%H:%M:%S%z"
            )
        description = AchievementDescription(
            name=achievement["title"],
            key=f'{achievement["source"]}.{achievement["id"]}',
            description=achievement["description"],
            granted_on=granted_on,
            source=achievement["source"],
            config_entry=self.config_entry,
        )
        self._async_add_entities([AchievementSensor(description)])


class InvalidAchievementEvent(Exception):
    pass
