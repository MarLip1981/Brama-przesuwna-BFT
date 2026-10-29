"""Config flow for Brama przesuwna BFT."""

from homeassistant import config_entries

from .const import DEFAULT_NAME, DOMAIN


class BramaPrzesuwnaBFTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up the BFT gate integration from the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the single integration entry without unnecessary form fields."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title=DEFAULT_NAME, data={})
