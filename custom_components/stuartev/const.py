"""
Constants for Stuart Energy integration.

This module defines constants used throughout the Stuart Energy integration,
including API URLs, domain name, and logger configuration.
"""

import logging

DOMAIN = "stuartev"

DAYS_DEFAULT = 30
DAYS_MAX = 365
SCAN_INTERVAL_DEFAULT = 3
SCAN_INTERVAL_MAX = 24

FIREBASE_AUTH_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)
FIREBASE_REFRESH_URL = "https://securetoken.googleapis.com/v1/token"

BASE_API_URL = "https://api.stuart.energy/api"
API_KEY = "AlzaSyBK2HLTRsVtTBcF3uGg-ICYTkpJObsTig"

LOGGER: logging.Logger = logging.getLogger(DOMAIN)
