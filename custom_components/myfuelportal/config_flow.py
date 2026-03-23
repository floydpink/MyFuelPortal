"""Config flow for MyFuelPortal."""
import logging

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, CONF_PROVIDER

_LOGGER = logging.getLogger(__name__)


class MyFuelPortalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            provider = user_input[CONF_PROVIDER].strip().lower()
            # Strip full URL down to subdomain if user pastes the whole thing
            for suffix in [".myfuelportal.com", "https://", "http://", "/"]:
                provider = provider.replace(suffix, "")

            try:
                ok = await self.hass.async_add_executor_job(
                    self._test_login, provider, user_input["username"], user_input["password"]
                )
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                if ok:
                    return self.async_create_entry(
                        title=f"MyFuelPortal ({provider})",
                        data={
                            CONF_PROVIDER: provider,
                            "username": user_input["username"],
                            "password": user_input["password"],
                        },
                    )
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_PROVIDER): str,
                vol.Required("username"): str,
                vol.Required("password"): str,
            }),
            errors=errors,
        )

    @staticmethod
    def _test_login(provider, username, password):
        from bs4 import BeautifulSoup
        import requests

        url = f"https://{provider}.myfuelportal.com/Account/Login?ReturnUrl=%2F"
        s = requests.Session()
        page = s.get(url, timeout=15)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        token = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token:
            return False
        resp = s.post(url, data={
            "EmailAddress": username,
            "Password": password,
            "RememberMe": "false",
            "__RequestVerificationToken": token["value"],
        }, timeout=15)
        return "/Account/Login" not in resp.url
