"""Config flow for Fuel Prices Italy."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_FUEL_TYPES,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MAX_STATIONS,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    CONF_SHOW_SELF,
    CONF_SHOW_SERVICED,
    DEFAULT_FUEL_TYPES,
    DEFAULT_RADIUS_KM,
    FUEL_SELECT_OPTIONS,
    MAX_STATIONS,
    MIN_SCAN_INTERVAL_MINUTES,
)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_LATITUDE, default=defaults.get(CONF_LATITUDE, 45.644912)): NumberSelector(
                NumberSelectorConfig(min=-90, max=90, step=0.000001, mode=NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_LONGITUDE, default=defaults.get(CONF_LONGITUDE, 12.330887)): NumberSelector(
                NumberSelectorConfig(min=-180, max=180, step=0.000001, mode=NumberSelectorMode.BOX)
            ),
            vol.Required(CONF_RADIUS_KM, default=defaults.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM)): NumberSelector(
                NumberSelectorConfig(min=1, max=50, step=0.5, mode=NumberSelectorMode.SLIDER, unit_of_measurement="km")
            ),
            vol.Required(CONF_FUEL_TYPES, default=defaults.get(CONF_FUEL_TYPES, DEFAULT_FUEL_TYPES)): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": fuel_id, "label": label}
                        for fuel_id, label in FUEL_SELECT_OPTIONS.items()
                    ],
                    multiple=True,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_SHOW_SELF, default=defaults.get(CONF_SHOW_SELF, True)): BooleanSelector(),
            vol.Required(CONF_SHOW_SERVICED, default=defaults.get(CONF_SHOW_SERVICED, False)): BooleanSelector(),
            vol.Required(CONF_SCAN_INTERVAL, default=defaults.get(CONF_SCAN_INTERVAL, 60)): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL_MINUTES,
                    max=1440,
                    step=15,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="min",
                )
            ),
            vol.Required(CONF_MAX_STATIONS, default=defaults.get(CONF_MAX_STATIONS, MAX_STATIONS)): NumberSelector(
                NumberSelectorConfig(min=1, max=100, step=1, mode=NumberSelectorMode.BOX)
            ),
        }
    )


class ConfigFlow(config_entries.ConfigFlow, domain="fuel_prices_italy"):
    """Handle a config flow for Fuel Prices Italy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            if not user_input[CONF_SHOW_SELF] and not user_input[CONF_SHOW_SERVICED]:
                return self.async_show_form(
                    step_id="user",
                    data_schema=_schema(user_input),
                    errors={CONF_SHOW_SELF: "select_at_least_one_mode"},
                )

            await self.async_set_unique_id(
                f"{user_input[CONF_LATITUDE]:.6f}_{user_input[CONF_LONGITUDE]:.6f}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Fuel Prices Italy", data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema())

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """Handle Fuel Prices Italy options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage integration options."""
        defaults = {**self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            if not user_input[CONF_SHOW_SELF] and not user_input[CONF_SHOW_SERVICED]:
                return self.async_show_form(
                    step_id="init",
                    data_schema=_schema(user_input),
                    errors={CONF_SHOW_SELF: "select_at_least_one_mode"},
                )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=_schema(defaults))

