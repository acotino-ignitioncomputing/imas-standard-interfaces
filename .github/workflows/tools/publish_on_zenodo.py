# Run the function 'publish_on_zenodo' with e.g. the tool 'uv'
#   cd .github/workflow
#   uv run --group zenodo_api python -m tools.publish_on_zenodo [latest_draft_url]
import click
import requests
import json

from tools.constants import (
    ZENODO_URL,
    ZENODO_API_KEY,
    SCHEMA_FILENAME,
    SCHEMA_PATH,
)


def publish_on_zenodo(latest_draft_url: str):
    """Upload the JSON Schema and publish the deposition of latest_draft_url on Zenodo.

    Documention of Zenodo's REST API: https://developers.zenodo.org/#rest-api

    Args:
        latest_draft_url: URL to (latest) version of deposition
    """

    headers = {"Authorization": f"Bearer {ZENODO_API_KEY}"}

    # Get new version of deposition
    response = requests.get(latest_draft_url, headers=headers)
    # TODO: add error handling based on received HTTP error codes
    new_deposition_dict = response.json()

    # Store deposition-ID and bucket-url for uploading file
    new_deposition_id = new_deposition_dict["id"]
    bucket_url = new_deposition_dict["links"]["bucket"]

    # Upload JSON Schema
    with open(SCHEMA_PATH, "rb") as json_schema_file:
        response = requests.put(
            f"{bucket_url}/{SCHEMA_FILENAME}", data=json_schema_file, headers=headers
        )

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


@click.command()
@click.argument("latest_draft_url")
def main(latest_draft_url: str):
    publish_on_zenodo(latest_draft_url)


if __name__ == "__main__":
    main()
