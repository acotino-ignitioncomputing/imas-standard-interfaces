"""
This script contains various constants.
"""

from pathlib import Path
import os

SCHEMA_FILENAME = "json_schema.json"
SCHEMA_PATH = Path(__file__).parents[3] / "schemas" / SCHEMA_FILENAME
EXAMPLE_DEFINITIONS_FOLDER = Path(__file__).parents[3] / "example_definitions"

SCHEMA_VERSION_KEY = "schema_version"

# Sandbox of Zenodo. Used for testing
ZENODO_URL = "https://sandbox.zenodo.org/api/deposit/depositions"  # Sandbox
ZENODO_PREFIX = "10.5072"  # Sandbox
ZENODO_API_KEY = os.getenv("ZENODO_SANDBOX_API_KEY")

""" IMPORTANT: before removing draft-status of PR, change above global variables

ZENODO_URL = "https://zenodo.org/api/deposit/depositions"
ZENODO_PREFIX = "10.5281"
ZENODO_API_KEY = os.getenv("ZENODO_API_KEY")

"""
