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

BASE_API_URL = "https://api.stuart.energy/api"
AUTH_API_URL = f"{BASE_API_URL}/slink/auth/login"
REFRESH_API_URL = f"{BASE_API_URL}/slink/auth/refresh"

LOGGER: logging.Logger = logging.getLogger(DOMAIN)
