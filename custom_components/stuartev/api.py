"""
API client for interacting with the Stuart Energy service.

This module provides the StuartEnergyApiClient class, which handles communication
with the Stuart Energy API, including fetching energy data and site information.
"""

import asyncio
from http import HTTPStatus
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .auth import StuartAuth
from .const import BASE_API_URL, LOGGER


class StuartEnergyApiClientError(Exception):
    """Exception to indicate a general API error."""


class StuartEnergyApiClientCommunicationError(
    StuartEnergyApiClientError,
):
    """Exception to indicate a communication error."""


class StuartEnergyApiClientAuthenticationError(
    StuartEnergyApiClientError,
):
    """Exception to indicate an authentication error."""


class StuartEnergyApiClientInvalidSiteIDError(StuartEnergyApiClientError):
    """Exception to indicate an invalid site ID error."""

    def __init__(self) -> None:
        """Initialize the error with a message."""
        super().__init__("Invalid site ID")


class StuartEnergyApiClient:
    """Client for interacting with the Stuart Energy API."""

    def __init__(
        self, hass: HomeAssistant, email: str, password: str, site_id: str, api_key: str
    ) -> None:
        """
        Initialize the StuartEnergyApiClient.

        :param hass: HomeAssistant instance
        :param email: User email
        :param password: User password
        :param site_id: Site ID
        """
        self.session = aiohttp_client.async_get_clientsession(hass)
        self.site_id = site_id
        self.auth = StuartAuth(hass, email, password, api_key)

    def _raise_invalid_site_error(self) -> None:
        """Raise an error if the site ID is invalid."""
        LOGGER.error("Site ID not found: %s", self.site_id)
        raise StuartEnergyApiClientInvalidSiteIDError

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        """
        Fetch data from the API.

        :param url: API endpoint URL
        :param params: API query parameters
        :return: data from the API response
        """
        token = await self.auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Referer": "https://app.stuart.energy",
        }

        try:
            async with self.session.get(
                url, headers=headers, params=params
            ) as response:
                if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                    retry_after = int(response.headers.get("Retry-After", 1))
                    LOGGER.warning(
                        "Rate limited by API, retrying after %d seconds", retry_after
                    )
                    await asyncio.sleep(retry_after)
                    return await self._get(url, params)
                if response.status == HTTPStatus.NOT_FOUND:
                    self._raise_invalid_site_error()
                if response.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                    LOGGER.warning("Unauthorized - refreshing token...")
                    token = await self.auth.refresh_auth_token()
                    headers["Authorization"] = f"Bearer {token}"
                    async with self.session.get(
                        url, headers=headers, params=params
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()

        except Exception as err:
            LOGGER.error("Error during API GET call: %s", err)
            raise StuartEnergyApiClientCommunicationError from err

    async def async_get_energy_data(
        self, date_from: str, date_to: str, aggregate_type: str = "Hour"
    ) -> Any | None:
        """
        Fetch energy data from the API.

        :param date_from: Start date for data retrieval
        :param date_to: End date for data retrieval
        :param aggregate_type: Aggregation type (default is "Hour")
        :return: JSON response with energy data
        """
        url = f"{BASE_API_URL}/slink/sites/{self.site_id}/details"
        params = {
            "dateFromLocal": date_from,
            "dateToLocal": date_to,
            "aggregateType": aggregate_type,
        }
        return await self._get(url, params)

    async def async_get_site_info(self) -> dict | None:
        """
        Fetch site information from the API.

        :return: JSON response with site information
        """
        url = f"{BASE_API_URL}/slink/sites/{self.site_id}"
        return await self._get(url)
