# Run the function 'get_latest_draft_url' with e.g. the tool 'uv'
#   cd .github/workflow
#   uv run --group zenodo_api python -m tools.get_latest_draft_url
import requests

from tools.constants import (
    ZENODO_URL,
    ZENODO_API_KEY,
)


def get_latest_draft_url() -> str:
    """Create a new (version of a) deposition using Zenodo's REST API and return the
    URL of this deposition as a string.

    Documention of Zenodo's REST API: https://developers.zenodo.org/#rest-api

    Returns:
        The 'latest_draft' url of the deposition on Zenodo
    """

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

        latest_draft_url = new_deposition_dict["links"]["latest_draft"]

    return latest_draft_url


if __name__ == "__main__":
    print(get_latest_draft_url())
