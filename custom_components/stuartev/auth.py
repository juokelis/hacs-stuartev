"""
Authentication module for Stuart Energy.

This module handles authentication with the Stuart Energy API, including obtaining
and refreshing tokens using Firebase authentication.
"""

import time
from http import HTTPStatus
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import FIREBASE_AUTH_URL, FIREBASE_REFRESH_URL, LOGGER


class StuartAuth:
    """Handle authentication with the Stuart Energy API."""

    def __init__(
        self, hass: HomeAssistant, email: str, password: str, api_key: str
    ) -> None:
        """
        Initialize the StuartAuth.

        :param hass: HomeAssistant instance
        :param email: User email
        :param password: User password
        """
        self.session = aiohttp_client.async_get_clientsession(hass)
        self.api_key = api_key
        self.email = email
        self.password = password
        self.token = None
        self.refresh_token = None
        self.token_expires = 0  # Epoch timestamp

    async def authenticate(self) -> Any | None:
        """
        Authenticate with the Firebase API and obtain tokens.

        :return: Authentication token if successful, None otherwise
        """
        LOGGER.info("Authenticating with Firebase API")
        payload = {
            "email": self.email,
            "password": self.password,
            "returnSecureToken": True,
        }
        async with self.session.post(
            f"{FIREBASE_AUTH_URL}?key={self.api_key}", json=payload
        ) as response:
            if response.status == HTTPStatus.OK:
                data = await response.json()
                self.token = data.get("idToken")
                self.refresh_token = data.get("refreshToken")
                expires_in = int(data.get("expiresIn", 3600))  # usually 3600 seconds
                self.token_expires = (
                    time.time() + expires_in - 60
                )  # buffer before expiry
                return self.token
            LOGGER.error("Failed to authenticate: %s", await response.text())
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
        payload = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        async with self.session.post(
            f"{FIREBASE_REFRESH_URL}?key={self.api_key}", json=payload
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
