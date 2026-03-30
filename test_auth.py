import asyncio
import logging
import sys

from aiohttp import ClientSession, TCPConnector


# Mocking parts of HA needed for the test
class MockHass:
    def __init__(self):
        self.session = None

    @property
    def http_client(self):
        return self.session

# Since we don't have a real HA instance, we'll bypass aiohttp_client.async_get_clientsession
# and provide our own session.
from custom_components.stuartev.auth import StuartAuth

# Configure logging
logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger("stuartev_test")

async def test_auth(email, password, api_key):
    # Use a basic TCPConnector to avoid aiodns issues in some environments
    # Specifically setting use_dns_cache=False can trigger standard resolver if aiodns fails,
    # but more explicitly, we want to ensure we don't use aiodns if it's broken.
    from aiohttp.resolver import ThreadedResolver
    connector = TCPConnector(resolver=ThreadedResolver())
    async with ClientSession(connector=connector) as session:
        # Patching StuartAuth to use our session directly
        # because async_get_clientsession requires a real HA instance.
        class TestAuth(StuartAuth):
            def __init__(self, email, password, api_key, session):
                self.session = session
                self.email = email
                self.password = password
                self.api_key = api_key
                self.token = None
                self.refresh_token = None
                self.token_expires = 0

        auth = TestAuth(email, password, api_key, session)

        print(f"Testing authentication for: {email}")
        token = await auth.authenticate()

        if token:
            print("Successfully authenticated!")
            print(f"Token: {token[:10]}...")
            print(f"Refresh Token: {auth.refresh_token[:10]}...")
        else:
            print("Authentication failed.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python test_auth.py <email> <password> <api_key>")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    api_key = sys.argv[3]

    asyncio.run(test_auth(email, password, api_key))
