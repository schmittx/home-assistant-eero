"""Support for Eero sensor entities."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfDataRate,
    UnitOfInformation,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import EeroEntity, EeroEntityDescription
from .api.const import (
    DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_CATEGORY_HOME,
    DEVICE_CATEGORY_OTHER,
    STATE_DISABLED,
    STATE_FAILURE,
    STATE_NETWORK,
    STATE_PROFILE,
)
from .const import (
    CONF_ACTIVITY,
    CONF_ACTIVITY_CLIENTS,
    CONF_ACTIVITY_EEROS,
    CONF_ACTIVITY_NETWORK,
    CONF_ACTIVITY_PROFILES,
    CONF_BACKUP_NETWORKS,
    CONF_CLIENTS,
    CONF_EEROS,
    CONF_NETWORKS,
    CONF_PROFILES,
    DATA_COORDINATOR,
    DOMAIN as EERO_DOMAIN,
)

DEVICE_CATEGORIES = [
    DEVICE_CATEGORY_COMPUTERS_PERSONAL,
    DEVICE_CATEGORY_ENTERTAINMENT,
    DEVICE_CATEGORY_HOME,
    DEVICE_CATEGORY_OTHER,
]

SPEED_UNIT_MAP = {
    "Kbps": UnitOfDataRate.KILOBITS_PER_SECOND,
    "Mbps": UnitOfDataRate.MEGABITS_PER_SECOND,
    "Gbps": UnitOfDataRate.GIGABITS_PER_SECOND,
}

@dataclass
class EeroSensorEntityDescription(EeroEntityDescription, SensorEntityDescription):
    """Class to describe an Eero sensor entity."""

    native_value: Callable = lambda resource, key: getattr(resource, key)
    entity_category: str[EntityCategory] | None = EntityCategory.DIAGNOSTIC
    activity_type: bool = False
    wireless_only: bool = False

SENSOR_DESCRIPTIONS: list[EeroSensorEntityDescription] = [
    EeroSensorEntityDescription(
        key="connected_clients_count",
        name="Connected Clients",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="clients",
    ),
    EeroSensorEntityDescription(
        key="connected_guest_clients_count",
        name="Connected Guest Clients",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="clients",
    ),
    EeroSensorEntityDescription(
        key="public_ip",
        name="Public IP",
    ),
    EeroSensorEntityDescription(
        key="speed_down",
        name="Download Speed",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_value=lambda resource, key: getattr(resource, key)[0],
        extra_attrs={
            "last_updated": lambda resource: getattr(resource, "speed_date"),
        },
    ),
    EeroSensorEntityDescription(
        key="speed_up",
        name="Upload Speed",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_value=lambda resource, key: getattr(resource, key)[0],
        extra_attrs={
            "last_updated": lambda resource: getattr(resource, "speed_date"),
        },
    ),
    EeroSensorEntityDescription(
        key="status",
        name="Status",
    ),
    EeroSensorEntityDescription(
        key="ad_block_status",
        name="Ad Blocking Status",
        device_class=SensorDeviceClass.ENUM,
        options=[STATE_DISABLED, STATE_NETWORK, STATE_PROFILE],
        premium_type=True,
    ),
    EeroSensorEntityDescription(
        key="adblock_day",
        name="Ad Blocks Day",
        native_unit_of_measurement="ads",
        state_class=SensorStateClass.TOTAL_INCREASING,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="adblock_week",
        name="Ad Blocks Week",
        native_unit_of_measurement="ads",
        state_class=SensorStateClass.TOTAL_INCREASING,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="adblock_month",
        name="Ad Blocks Month",
        native_unit_of_measurement="ads",
        state_class=SensorStateClass.TOTAL_INCREASING,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="blocked_day",
        name="Threat Blocks Day",
        native_unit_of_measurement="threats",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_value=lambda resource, key: getattr(resource, key)["blocked"] if resource.is_network else getattr(resource, key),
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="blocked_week",
        name="Threat Blocks Week",
        native_unit_of_measurement="threats",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_value=lambda resource, key: getattr(resource, key)["blocked"] if resource.is_network else getattr(resource, key),
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="blocked_month",
        name="Threat Blocks Month",
        native_unit_of_measurement="threats",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_value=lambda resource, key: getattr(resource, key)["blocked"] if resource.is_network else getattr(resource, key),
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="data_usage_day",
        name="Data Usage Day",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_value=lambda resource, key: (getattr(resource, key)[0] + getattr(resource, key)[1]),
        native_unit_of_measurement=UnitOfInformation.BYTES,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="data_usage_week",
        name="Data Usage Week",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_value=lambda resource, key: (getattr(resource, key)[0] + getattr(resource, key)[1]),
        native_unit_of_measurement=UnitOfInformation.BYTES,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="data_usage_month",
        name="Data Usage Month",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_value=lambda resource, key: (getattr(resource, key)[0] + getattr(resource, key)[1]),
        native_unit_of_measurement=UnitOfInformation.BYTES,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="inspected_day",
        name="Scans Day",
        native_unit_of_measurement="scans",
        state_class=SensorStateClass.TOTAL_INCREASING,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="inspected_week",
        name="Scans Week",
        native_unit_of_measurement="scans",
        state_class=SensorStateClass.TOTAL_INCREASING,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="inspected_month",
        name="Scans Month",
        native_unit_of_measurement="scans",
        state_class=SensorStateClass.TOTAL_INCREASING,
        activity_type=True,
    ),
    EeroSensorEntityDescription(
        key="ip",
        name="IP Address",
    ),
    EeroSensorEntityDescription(
        key="last_active",
        name="Last Active",
        device_class=SensorDeviceClass.TIMESTAMP,
        native_value=lambda resource, key: datetime.fromisoformat(getattr(resource, key).replace("Z", "+00:00")),
    ),
    EeroSensorEntityDescription(
        key="signal",
        name="Signal Strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        wireless_only=True,
    ),
    EeroSensorEntityDescription(
        key="usage_down",
        name="Download Rate",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    ),
    EeroSensorEntityDescription(
        key="usage_up",
        name="Upload Rate",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up an Eero sensor entity based on a config entry."""
    entry = hass.data[EERO_DOMAIN][config_entry.entry_id]
    coordinator = entry[DATA_COORDINATOR]
    entities: list[EeroSensorEntity] = []

    SUPPORTED_KEYS = {
        description.key: description for description in SENSOR_DESCRIPTIONS
    }

    for network in coordinator.data.networks:
        if network.id in entry[CONF_NETWORKS]:
            activity = entry[CONF_ACTIVITY].get(network.id, {})
            for key, description in SUPPORTED_KEYS.items():
                if any(
                    [
                        description.premium_type and not network.premium_enabled,
                        description.activity_type and not network.premium_enabled,
                        description.activity_type and key not in activity.get(CONF_ACTIVITY_NETWORK, []),
                    ]
                ):
                    continue
                elif hasattr(network, key):
                    entities.append(
                        EeroSensorEntity(
                            coordinator,
                            network.id,
                            None,
                            description,
                        )
                    )

            for backup_network in network.backup_networks:
                if backup_network.id in entry[CONF_BACKUP_NETWORKS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if hasattr(backup_network, key):
                            entities.append(
                                EeroSensorEntity(
                                    coordinator,
                                    network.id,
                                    backup_network.id,
                                    description,
                                )
                            )

            for eero in network.eeros:
                if eero.id in entry[CONF_EEROS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if any(
                            [
                                description.premium_type and not network.premium_enabled,
                                description.activity_type and not network.premium_enabled,
                                description.activity_type and key not in activity.get(CONF_ACTIVITY_EEROS, []),
                            ]
                        ):
                            continue
                        elif hasattr(eero, key):
                            entities.append(
                                EeroSensorEntity(
                                    coordinator,
                                    network.id,
                                    eero.id,
                                    description,
                                )
                            )

            for profile in network.profiles:
                if profile.id in entry[CONF_PROFILES]:
                    for key, description in SUPPORTED_KEYS.items():
                        if any(
                            [
                                description.premium_type and not network.premium_enabled,
                                description.activity_type and not network.premium_enabled,
                                description.activity_type and key not in activity.get(CONF_ACTIVITY_PROFILES, []),
                            ]
                        ):
                            continue
                        elif hasattr(profile, key):
                            entities.append(
                                EeroSensorEntity(
                                    coordinator,
                                    network.id,
                                    profile.id,
                                    description,
                                )
                            )

            for client in network.clients:
                if client.id in entry[CONF_CLIENTS]:
                    for key, description in SUPPORTED_KEYS.items():
                        if any(
                            [
                                description.premium_type and not network.premium_enabled,
                                description.activity_type and not network.premium_enabled,
                                description.activity_type and key not in activity.get(CONF_ACTIVITY_CLIENTS, []),
                                description.wireless_only and not client.wireless,
                            ]
                        ):
                            continue
                        elif hasattr(client, key):
                            entities.append(
                                EeroSensorEntity(
                                    coordinator,
                                    network.id,
                                    client.id,
                                    description,
                                )
                            )

    async_add_entities(entities)


class EeroSensorEntity(EeroEntity, SensorEntity):
    """Representation of an Eero sensor entity."""

    @property
    def native_value(self) -> StateType | date | datetime:
        """Return the value reported by the sensor."""
        return self.entity_description.native_value(self.resource, self.entity_description.key)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement of the sensor, if any."""
        if self.entity_description.key.startswith("speed"):
            native_unit = getattr(self.resource, self.entity_description.key)[1]
            return SPEED_UNIT_MAP.get(native_unit, native_unit)
        return self.entity_description.native_unit_of_measurement

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes.

        Implemented by platform classes. Convention for attribute names
        is lowercase snake_case.
        """
        attrs = {}
        if self.entity_description.extra_attrs:
            for key, func in self.entity_description.extra_attrs.items():
                attrs[key] = func(self.resource)
        if self.entity_description.key.startswith("blocked") and self.resource.is_network:
            data = getattr(self.resource, self.entity_description.key)
            for key, value in data.items():
                if key != "blocked":
                    attrs[key] = value
        if self.entity_description.key.startswith("data_usage"):
            attrs["download"], attrs["upload"] = getattr(self.resource, self.entity_description.key)
        if self.entity_description.key.endswith("clients_count"):
            for category in DEVICE_CATEGORIES:
                attr = f"{self.entity_description.key}_{category}"
                if hasattr(self.resource, attr):
                    attrs[category] = getattr(self.resource, attr)
        if self.entity_description.key == "status" and self.resource.is_backup_network:
            attrs["checked"] = getattr(self.resource, "checked")
            if all(
                [
                    self.state == STATE_FAILURE,
                    failure_reason := getattr(self.resource, "failure_reason"),
                ]
            ):
                attrs["failure_reason"] = failure_reason.lower()
        return attrs
