"""
This script contains various constants.
"""

from pathlib import Path
import os

REPOSITORY_PATH = Path(__file__).parents[3]

SCHEMA_FILENAME = "json_schema.json"
SCHEMA_PATH = REPOSITORY_PATH / "schemas" / SCHEMA_FILENAME
EXAMPLE_DEFINITIONS_FOLDER = REPOSITORY_PATH / "example_definitions"
SCRIPT_PATH = REPOSITORY_PATH / "schemas" / "validate_definitions.py"

SCHEMA_VERSION_KEY = "schema_version"

# Sandbox of Zenodo. Used for testing
ZENODO_URL = os.getenv("ZENODO_URL")
ZENODO_PREFIX = os.getenv("ZENODO_PREFIX")
ZENODO_API_KEY = os.getenv("ZENODO_API_KEY")

""" IMPORTANT: before PR into IO's repo, ensure environment variables have these values

ZENODO_URL = "https://zenodo.org/api/deposit/depositions"
ZENODO_PREFIX = "10.5281"
ZENODO_API_KEY = os.getenv("ZENODO_API_KEY")

"""
