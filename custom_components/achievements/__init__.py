import logging

from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, callback, HassJob, Event
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from datetime import datetime, timedelta
from homeassistant.loader import async_get_integrations
from homeassistant.setup import async_get_loaded_integrations
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store
from awesomeversion import AwesomeVersion
from homeassistant.const import __version__
from homeassistant.helpers.entity_registry import async_get

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # here we store the coordinator for future access
    if entry.entry_id not in hass.data[DOMAIN]:
        hass.data[DOMAIN][entry.entry_id] = {}

    # will make sure async_setup_entry from sensor.py is called
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])

    # subscribe to config updates
    entry.async_on_unload(entry.add_update_listener(update_entry))

    detector = AchievementDetector(hass, entry)

    @callback
    def start_schedule(_event: Event) -> None:
        """Start the send schedule after the started event."""
        # right after HA startup completion
        async_call_later(
            hass,
            0,
            HassJob(
                detector.detect_achievements,
                name="achievement detection schedule",
                cancel_on_shutdown=True,
            ),
        )
        # Send every day
        async_track_time_interval(
            hass,
            detector.detect_achievements,
            timedelta(hours=1),
            name="achievements detection hourly",
            cancel_on_shutdown=True,
        )

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_schedule)

    return True


async def update_entry(hass, entry):
    """
    This method is called when options are updated
    We trigger the reloading of entry (that will eventually call async_unload_entry)
    """
    _LOGGER.debug("update_entry method called")
    # will make sure async_setup_entry from sensor.py is called
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """This method is called to clean all sensors before re-adding them"""
    _LOGGER.debug("async_unload_entry method called")
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR]
    )
    return unload_ok


class AchievementDetector:
    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self.hass = hass
        self._store = Store(hass, 1, f"achievement-detector-{config_entry.entry_id}")

    async def check_upgrade(self):
        store = await self._store.async_load()
        if store is None:
            return
        previous = AwesomeVersion(store["previous_running_version"])
        current = AwesomeVersion(__version__)
        if previous.beta and current.beta and current > previous:
            self.hass.bus.fire(
                "achievement_granted",
                {
                    "major_version": 0,
                    "minor_version": 1,
                    "achievement": {
                        "title": "Dangerous living",
                        "description": f"You've upgraded from one beta to another",
                        "source": "achievements-core",
                        "id": "2a9129ec-17c1-4a4b-afae-4fd7ddddf341",
                    },
                },
            )

    async def store(self):
        await self._store.async_save(
            {
                "previous_running_version": __version__,
            }
        )
        _LOGGER.debug("Persistent storage for achievement has been stored")

    async def detect_achievements(self, _: datetime | None = None):
        domains = async_get_loaded_integrations(self.hass)
        configured_integrations = await async_get_integrations(self.hass, domains)
        enabled_domains = set(configured_integrations)
        integrations = [
            integration
            for integration in configured_integrations.values()
            if not isinstance(integration, BaseException)
        ]

        custom_integration_count = sum(
            [1 for integration in integrations if not integration.is_built_in]
        )

        _LOGGER.debug(f"Found {custom_integration_count} custom integrations")
        if custom_integration_count >= 50:
            self.hass.bus.fire(
                "achievement_granted",
                {
                    "major_version": 0,
                    "minor_version": 1,
                    "achievement": {
                        "title": "Collector",
                        "description": f"You have installed {custom_integration_count} custom integration.",
                        "source": "achievements-core",
                        "id": "6a6a8a11-f477-4b08-8dad-51b9b1f0d49d",
                    },
                },
            )

        await self.check_upgrade()
        await self.store()

        # update count
        entity_registry = async_get(self.hass)
        updates = [
            entry
            for entry in entity_registry.entities.values()
            if entry.domain == "update"
        ]
        out_of_date = [
            entry
            for entry in updates
            if self.hass.states.get(entry.entity_id).state == "on"
        ]
        if len(out_of_date) > 10:
            self.hass.bus.fire(
                "achievement_granted",
                {
                    "major_version": 0,
                    "minor_version": 1,
                    "achievement": {
                        "title": "Out of date",
                        "description": f"You have {len(out_of_date)} pending updates. Time for an upgrade party!",
                        "source": "achievements-core",
                        "id": "ac347c90-f2a5-4166-af0f-e7fb00c81e59",
                    },
                },
            )
