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

choice = input(
    "WARNING: \n\tThis test runs the main function of 'publish_on_zenodo.py'.\n"
    + "\tThis WILL push a new commit to the current branch using git.\n"
    + "\tIf this is expected, type 'yes':\n"
    + "Continue? "
)
if choice == "yes":
    main()
else:
    print("Test aborted")
