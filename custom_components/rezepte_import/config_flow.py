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
        vol.Required("conversation_agent",  default=defaults.get("conversation_agent",  AGENT_ID_DEFAULT)):         str,
        vol.Required("llmvision_provider",  default=defaults.get("llmvision_provider",  LLMVISION_PROVIDER_DEFAULT)): vol.In(LLMVISION_PROVIDERS),
    })

class RezepteImportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Einrichtungs-Dialog fuer Rezepte Import."""
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Rezepte Import", data=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Einstellungen nachtraeglich aendern (kein Neustart noetig)."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry,
                data=user_input,
                reason="reconfigure_successful",
            )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(entry.data if entry else {}),
        )
