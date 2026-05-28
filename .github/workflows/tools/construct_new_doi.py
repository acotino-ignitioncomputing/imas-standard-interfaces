import click
import requests
from tools.constants import (
    ZENODO_PREFIX,
    ZENODO_API_KEY,
)


def construct_new_doi(latest_draft_url: str) -> str:
    """Construct new DOI URL from the deposition's ID (pointed by latest_draft_url) and
      Zenodo's prefix.

    Args:
        latest_draft_url: URL to (latest) version of deposition

    Returns:
        new DOI URL as a string
    """
    headers = {"Authorization": f"Bearer {ZENODO_API_KEY}"}

    # Get new version of deposition
    response = requests.get(latest_draft_url, headers=headers)
    # TODO: add error handling based on received HTTP error codes
    new_deposition_dict = response.json()

    # Get deposition-ID: doi_url consists of zenodo-prefix and deposition-ID
    new_deposition_id = new_deposition_dict["id"]

    return f"https://doi.org/{ZENODO_PREFIX}/zenodo.{new_deposition_id}"


@click.command()
@click.argument("latest_draft_url")
def main(latest_draft_url: str) -> str:
    print(construct_new_doi(latest_draft_url))


if __name__ == "__main__":
    main()
