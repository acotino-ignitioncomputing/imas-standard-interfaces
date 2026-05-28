"""
Test publishing using Zenodo's sandbox environment https://sandbox.zenodo.org

Run using
    cd .github/workflow
    uv run --group zenodo_api python -m tools.tests.test_publish_on_zenodo
"""

import os
from tools.get_latest_draft_url import get_latest_draft_url
from tools.construct_new_doi import construct_new_doi
from tools.update_doi_value import update_doi_value
from tools.publish_on_zenodo import publish_on_zenodo

SANDBOX_ZENODO_URL = "https://sandbox.zenodo.org/api/deposit/depositions"  # Sandbox
SANDBOX_ZENODO_PREFIX = "10.5072"  # Sandbox
SANDBOX_ZENODO_API_KEY = os.getenv("ZENODO_SANDBOX_API_KEY")

ZENODO_URL, ZENODO_PREFIX, ZENODO_API_KEY = (
    SANDBOX_ZENODO_URL,
    SANDBOX_ZENODO_PREFIX,
    SANDBOX_ZENODO_API_KEY,
)

choice = input(
    "WARNING: \n\tThis test runs the Python functions used in the publish_schema.yaml workflow.\n"
    + "\tThis WILL update the DOI URL in the JSON Schema and example definitions.\n"
    + "\tIf this is expected, type 'yes':\n"
    + "Continue? "
)
if choice == "yes":
    print("""Testing the creation of a new version on Zenodo's sandbox""")
    latest_draft_url = get_latest_draft_url()
    new_doi_url = construct_new_doi(latest_draft_url)
    update_doi_value(new_doi_url)
    publish_on_zenodo(latest_draft_url)
else:
    print("Test aborted")
