"""
Authentication module for Stuart Energy.

This module handles authentication with the Stuart Energy API, including obtaining
and refreshing tokens using their authentication service.
"""

import time
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from homeassistant.helpers import aiohttp_client

from .const import AUTH_API_URL, LOGGER, REFRESH_API_URL

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class StuartAuth:
    """Handle authentication with the Stuart Energy API."""

    def __init__(
        self,
        hass: HomeAssistant,
        email: str,
        password: str,
        api_key: str,
        session: aiohttp_client.ClientSession | None = None,
    ) -> None:
        """
        Initialize the StuartAuth.

        :param hass: HomeAssistant instance
        :param email: User email
        :param password: User password
        :param api_key: API Key
        :param session: Optional aiohttp client session
        """
        self.session = session or aiohttp_client.async_get_clientsession(hass)
        self.email = email
        self.password = password
        self.api_key = api_key
        self.token = None
        self.refresh_token = None
        self.token_expires = 0  # Epoch timestamp

    async def authenticate(self) -> Any | None:
        """
        Authenticate with the Stuart Energy API and obtain tokens.

        :return: Authentication token if successful, None otherwise
        """
        LOGGER.info("Authenticating with Stuart Energy API")
        payload = {
            "email": self.email,
            "password": self.password,
            "returnSecureToken": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://app.stuart.energy/",
            "Origin": "https://app.stuart.energy",
        }
        params = {"key": self.api_key}
        async with self.session.post(
            AUTH_API_URL, json=payload, headers=headers, params=params
        ) as response:
            if response.status == HTTPStatus.OK:
                data = await response.json()
                self.token = data.get("token") or data.get("idToken")
                self.refresh_token = data.get("refreshToken")
                expires_in = int(data.get("expiresIn", 3600))
                self.token_expires = time.time() + expires_in - 60
                return self.token
            response_text = await response.text()
            LOGGER.debug("Authentication payload: %s", payload)
            LOGGER.debug("Authentication response status: %s", response.status)
            LOGGER.debug("Authentication response headers: %s", response.headers)
            LOGGER.debug("Authentication response body: %s", response_text)
            LOGGER.error("Failed to authenticate: %s", response_text)
            return None

    async def refresh_auth_token(self) -> Any | None:
        """
        Refresh the authentication token using the refresh token.

        :return: New authentication token if successful, None otherwise
        """
        if not self.refresh_token:
            LOGGER.warning("No refresh token available, re-authenticating.")
            return await self.authenticate()

        LOGGER.info("Refreshing authentication token")
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://app.stuart.energy/",
            "Origin": "https://app.stuart.energy",
        }
        params = {"key": self.api_key}
        async with self.session.post(
            REFRESH_API_URL, json=payload, headers=headers, params=params
        ) as response:
            if response.status == HTTPStatus.OK:
                data = await response.json()
                self.token = data.get("id_token")
                self.refresh_token = data.get("refresh_token")
                expires_in = int(data.get("expires_in", 3600))
                self.token_expires = time.time() + expires_in - 60
                return self.token
            LOGGER.error("Failed to refresh token: %s", await response.text())
            return await self.authenticate()

    async def get_token(self) -> Any | None:
        """
        Return a valid token, refreshing or re-authenticating if needed.

        :return: Valid authentication token
        """
        if not self.token or time.time() >= self.token_expires:
            LOGGER.info("Token expired or missing, refreshing...")
            return await self.refresh_auth_token()
        return self.token
