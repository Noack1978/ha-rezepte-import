"""Config Flow für Rezepte Import."""
from __future__ import annotations
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from . import DOMAIN, AGENT_ID_DEFAULT, LLMVISION_PROVIDER_DEFAULT

LLMVISION_PROVIDERS = ["Google", "OpenAI", "Anthropic", "Ollama", "Custom OpenAI"]

class RezepteImportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Rezepte Import", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("conversation_agent", default=AGENT_ID_DEFAULT): str,
                vol.Required("llmvision_provider", default=LLMVISION_PROVIDER_DEFAULT): vol.In(LLMVISION_PROVIDERS),
            }),
        )
