import aiohttp

from .auth import StuartAuth
from .const import BASE_API_URL, LOGGER


class StuartEnergyClient:
    def __init__(self, session: aiohttp.ClientSession, email: str, password: str, site_id: str):
        self.session = session
        self.site_id = site_id
        self.auth = StuartAuth(session, email, password)

    async def async_get_energy_data(self, date_from, date_to, aggregate_type="Hour"):
        url = f"{BASE_API_URL}/slink/sites/{self.site_id}/details"
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "aggregateType": aggregate_type,
        }

        token = await self.auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 404:
                    LOGGER.error("Site ID not found: %s", self.site_id)
                    raise ValueError("Invalid site ID")
                elif response.status in (401, 403):
                    LOGGER.warning("Unauthorized – refreshing token...")
                    token = await self.auth.refresh_auth_token()
                    headers["Authorization"] = f"Bearer {token}"
                    async with self.session.get(url, headers=headers, params=params) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as err:
            LOGGER.error("Error fetching energy data: %s", err)
            return None

    async def async_get_site_info(self):
        url = f"{BASE_API_URL}/slink/sites/{self.site_id}"

        token = await self.auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as err:
            LOGGER.error("Error fetching site info: %s", err)
            return None
