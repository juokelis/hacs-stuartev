import aiohttp
import pytest
from aioresponses import aioresponses

from custom_components.stuartev.auth import StuartAuth


@pytest.mark.asyncio
async def test_authenticate():
    async with aiohttp.ClientSession() as session:
        with aioresponses() as m:
            # Mock the authentication response
            m.post(
                "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AlzaSyBK2HLTRsVtTBcF3uGg-ICYTkpJObsTig",
                payload={"idToken": "test_token", "refreshToken": "test_refresh_token", "expiresIn": "3600"})

            auth = StuartAuth(session, "test@example.com", "password")
            token = await auth.authenticate()

            # Assertions
            assert token is not None
            assert token == "test_token"
