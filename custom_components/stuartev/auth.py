"""Authentication towards Stuart Energy."""

import time

import aiohttp

from .const import FIREBASE_AUTH_URL, FIREBASE_REFRESH_URL, API_KEY, LOGGER


class StuartAuth:
    def __init__(self, session: aiohttp.ClientSession, email: str, password: str):
        self.session = session
        self.email = email
        self.password = password
        self.token = None
        self.refresh_token = None
        self.token_expires = 0  # Epoch timestamp

    async def authenticate(self):
        LOGGER.info("Authenticating with Firebase API")
        payload = {"email": self.email, "password": self.password, "returnSecureToken": True}
        async with self.session.post(f"{FIREBASE_AUTH_URL}?key={API_KEY}", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                self.token = data.get("idToken")
                self.refresh_token = data.get("refreshToken")
                expires_in = int(data.get("expiresIn", 3600))  # usually 3600 seconds
                self.token_expires = time.time() + expires_in - 60  # buffer before expiry
                return self.token
            LOGGER.error("Failed to authenticate: %s", await response.text())
            return None

    async def refresh_auth_token(self):
        if not self.refresh_token:
            LOGGER.warning("No refresh token available, re-authenticating.")
            return await self.authenticate()

        LOGGER.info("Refreshing authentication token")
        payload = {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        async with self.session.post(f"{FIREBASE_REFRESH_URL}?key={API_KEY}", json=payload) as response:
            if response.status == 200:
                data = await response.json()
                self.token = data.get("id_token")
                self.refresh_token = data.get("refresh_token")
                expires_in = int(data.get("expires_in", 3600))
                self.token_expires = time.time() + expires_in - 60
                return self.token
            LOGGER.error("Failed to refresh token: %s", await response.text())
            return await self.authenticate()

    async def get_token(self):
        """Return a valid token, refresh or re-auth if needed."""
        if not self.token or time.time() >= self.token_expires:
            LOGGER.info("Token expired or missing, refreshing...")
            return await self.refresh_auth_token()
        return self.token
