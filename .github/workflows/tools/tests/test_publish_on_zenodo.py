"""
Test publishing using Zenodo's sandbox environment https://sandbox.zenodo.org

Run using
    cd .github/workflow
    uv run python -m tools.tests.test_publish_on_zenodo
"""

import os
from tools.publish_on_zenodo import main

SANDBOX_ZENODO_URL = "https://sandbox.zenodo.org/api/deposit/depositions"  # Sandbox
SANDBOX_ZENODO_PREFIX = "10.5072"  # Sandbox
SANDBOX_ZENODO_API_KEY = os.getenv("ZENODO_SANDBOX_API_KEY")

ZENODO_URL, ZENODO_PREFIX, ZENODO_API_KEY = (
    SANDBOX_ZENODO_URL,
    SANDBOX_ZENODO_PREFIX,
    SANDBOX_ZENODO_API_KEY,
)

main()
