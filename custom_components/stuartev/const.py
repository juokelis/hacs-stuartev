"""
Constants for Stuart Energy integration.

This module defines constants used throughout the Stuart Energy integration,
including API URLs, domain name, and logger configuration.
"""

import logging

DOMAIN = "stuartev"

CONF_API_KEY = "api_key"

DAYS_DEFAULT = 30
DAYS_MAX = 365
SCAN_INTERVAL_DEFAULT = 3
SCAN_INTERVAL_MAX = 24

BASE_API_URL = "https://api.stuart.energy/api"
AUTH_API_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
REFRESH_API_URL = "https://securetoken.googleapis.com/v1/token"

LOGGER: logging.Logger = logging.getLogger(DOMAIN)
