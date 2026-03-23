"""MyFuelPortal data coordinator."""
import logging
from datetime import timedelta

from bs4 import BeautifulSoup
import requests

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class MyFuelPortalCoordinator(DataUpdateCoordinator):
    """Fetch tank data from MyFuelPortal."""

    def __init__(self, hass, provider, username, password):
        super().__init__(
            hass,
            _LOGGER,
            name="MyFuelPortal",
            update_interval=timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS),
        )
        self.provider = provider
        self.username = username
        self.password = password
        self._base = f"https://{provider}.myfuelportal.com"

    async def _async_update_data(self):
        return await self.hass.async_add_executor_job(self._fetch)

    def _fetch(self):
        login_url = f"{self._base}/Account/Login?ReturnUrl=%2F"
        tank_url = f"{self._base}/Tank"

        session = requests.Session()
        page = session.get(login_url, timeout=15)
        page.raise_for_status()

        soup = BeautifulSoup(page.text, "html.parser")
        token_el = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token_el:
            raise UpdateFailed("Cannot find CSRF token on login page")

        resp = session.post(
            login_url,
            data={
                "EmailAddress": self.username,
                "Password": self.password,
                "RememberMe": "false",
                "__RequestVerificationToken": token_el["value"],
            },
            timeout=15,
        )
        if "/Account/Login" in resp.url:
            raise UpdateFailed("Login failed — check credentials")

        resp = session.get(tank_url, timeout=15)
        if resp.status_code != 200:
            raise UpdateFailed(f"Tank page returned {resp.status_code}")

        soup = BeautifulSoup(resp.text, "html.parser")
        tanks = []
        for div in soup.select("div.tank-row"):
            try:
                name_tag = div.select_one(".text-larger")
                if not name_tag:
                    continue
                name = name_tag.get_text(strip=True)

                pct_tag = div.select_one(".progress-bar")
                percent = float(pct_tag.get_text(strip=True).replace("%", "")) if pct_tag else None

                gal_tag = div.find(string=lambda t: t and "Approximately" in t)
                gallons = float(gal_tag.split()[1]) if gal_tag else None

                reading_tag = div.find(string=lambda t: t and "Reading Date:" in t)
                reading_date = self._parse_date(reading_tag, "Reading Date:")

                delivery_tag = div.find(string=lambda t: t and "Last Delivery:" in t)
                last_delivery = self._parse_date(delivery_tag, "Last Delivery:")

                capacity = round(gallons / (percent / 100), 1) if gallons and percent else None

                tanks.append({
                    "name": name,
                    "percent": percent,
                    "gallons": gallons,
                    "capacity": capacity,
                    "reading_date": reading_date,
                    "last_delivery": last_delivery,
                })
            except Exception as exc:
                _LOGGER.warning("Failed to parse tank: %s", exc)

        return {"tanks": tanks}

    @staticmethod
    def _parse_date(tag, prefix):
        if not tag:
            return None
        raw = tag.replace(prefix, "").strip()
        try:
            from datetime import datetime
            return datetime.strptime(raw, "%m/%d/%Y").date().isoformat()
        except (ValueError, AttributeError):
            return raw
