"""Config Flow fuer Rezepte Import."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from . import DOMAIN, AGENT_ID_DEFAULT, LLMVISION_PROVIDER_DEFAULT

LLMVISION_PROVIDERS = ["Google", "OpenAI", "Anthropic", "Ollama", "Groq", "Custom OpenAI"]

def _schema(defaults: dict) -> vol.Schema:
    return vol.Schema({
        vol.Required("conversation_agent", default=defaults.get("conversation_agent", AGENT_ID_DEFAULT)): str,
        vol.Required("llmvision_provider", default=defaults.get("llmvision_provider", LLMVISION_PROVIDER_DEFAULT)): vol.In(LLMVISION_PROVIDERS),
    })


class RezepteImportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Einrichtungs-Dialog."""
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Rezepte Import", data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Einstellungen aendern – HA laedt Integration danach automatisch neu."""
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry,
                data=user_input,
                reason="reconfigure_successful",
            )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(entry.data),
        )


class RezepteImportOptionsFlow(config_entries.OptionsFlow):
    """Alternativer Weg zum Aendern der Einstellungen (aeltere HA-Versionen)."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            # Einstellungen in data speichern und Integration neu laden
            self.hass.config_entries.async_update_entry(self._entry, data={**self._entry.data, **user_input})
            await self.hass.config_entries.async_reload(self._entry.entry_id)
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(self._entry.data),
        )

    @staticmethod
    def async_get_options_flow(entry: config_entries.ConfigEntry) -> RezepteImportOptionsFlow:
        return RezepteImportOptionsFlow(entry)
