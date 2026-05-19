"""
The main-function of this script uses Zenodo's REST API to
- create a new (version of a) deposition,
- construct new DOI URL from this deposition's ID and Zenodo's prefix
- upload the JSON Schema and publish the deposition.

Before uploading, the 'const'-value of key SCHEMA_VERSION_KEY in the JSON Schema is
updated to the new DOI URL.

Documention of Zenodo's REST API: https://developers.zenodo.org/#rest-api
"""

import requests
import json
import subprocess

from tools.constants import (
    ZENODO_URL,
    ZENODO_PREFIX,
    ZENODO_API_KEY,
    SCHEMA_FILENAME,
    SCHEMA_PATH,
    SCRIPT_PATH,
    SCHEMA_VERSION_KEY,
)
from tools.update_doi_value import update_doi_value
from tools.commit_schema import commit_schema_to_git


def main():

    headers = {"Authorization": f"Bearer {ZENODO_API_KEY}"}

    # Get list of depositions associated with API key
    deposition_list = requests.get(ZENODO_URL, headers=headers).json()

    if deposition_list:
        # Create new version of latest deposition

        links_dict = deposition_list[0]["links"]
        response = requests.post(links_dict["newversion"], headers=headers)
        # TODO: add error handling based on received HTTP error codes
        latest_draft_url = response.json()["links"]["latest_draft"]

        # Get new version of deposition
        response = requests.get(latest_draft_url, headers=headers)
        # TODO: add error handling based on received HTTP error codes
        new_deposition_dict = response.json()

    else:
        # Create new empty deposition
        new_deposition_dict = requests.post(ZENODO_URL, json={}, headers=headers).json()

    # Store deposition-ID for constructing new DOI, and bucket-url for uploading file
    new_deposition_id = new_deposition_dict["id"]
    bucket_url = new_deposition_dict["links"]["bucket"]

    # New doi_url consists of zenodo-prefix and deposition-ID
    new_doi = f"https://doi.org/{ZENODO_PREFIX}/zenodo.{new_deposition_id}"

    # Update value of key SCHEMA_VERSION_KEY in JSON Schema and YAML files
    update_doi_value(new_doi)

    # Check that validation of example definitions against schema still succeed
    process = subprocess.run(["uv", "run", "python", SCRIPT_PATH], capture_output=True)
    if process.returncode != 0:
        raise Exception(
            f"After updating the key '{SCHEMA_VERSION_KEY}' in schema and example"
            + f" definitions, validation failed: \n\t {process.stdout}"
        )

    # Call script to push changed files to current branch
    commit_schema_to_git()

    # Upload JSON Schema
    with open(SCHEMA_PATH, "rb") as json_schema_file:
        response = requests.put(
            f"{bucket_url}/{SCHEMA_FILENAME}", data=json_schema_file, headers=headers
        )

    # TODO: error handling on HTTP code of response

    # TODO: Add proper metadata
    metadata = {
        "metadata": {
            "title": "Interface schema",
            "upload_type": "publication",
            "publication_type": "standard",
            "description": "Schema for the description of an interface for simulation code using IMAS",
            "creators": [{"name": "Github Actions"}],
        }
    }
    response = requests.put(
        f"{ZENODO_URL}/{new_deposition_id}", data=json.dumps(metadata), headers=headers
    )

    # TODO: error handling on HTTP code of response

    # Publish new deposition
    requests.post(new_deposition_dict["links"]["publish"], headers=headers)


if __name__ == "__main__":
    main()
