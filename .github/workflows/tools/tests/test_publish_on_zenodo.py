"""
Test publishing using Zenodo's sandbox environment https://sandbox.zenodo.org
"""

from tools.publish_on_zenodo import main
from tools.constants import (
    SANDBOX_ZENODO_URL,
    SANDBOX_ZENODO_PREFIX,
    SANDBOX_ZENODO_API_KEY,
)

ZENODO_URL, ZENODO_PREFIX, ZENODO_API_KEY = (
    SANDBOX_ZENODO_URL,
    SANDBOX_ZENODO_PREFIX,
    SANDBOX_ZENODO_API_KEY,
)

main()
