"""Constants for stuartev."""

import logging

DOMAIN = "stuartev"

FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIREBASE_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"

BASE_API_URL = "https://api.stuart.energy/api"
API_KEY = "AlzaSyBK2HLTRsVtTBcF3uGg-ICYTkpJObsTig"

LOGGER: logging.Logger = logging.getLogger(DOMAIN)
