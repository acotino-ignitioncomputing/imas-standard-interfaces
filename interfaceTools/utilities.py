# General utility functions

import sys
import yaml
import json
from pathlib import Path

# Path to the JSON schema describing the format of the interface definitions
SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "json_schema.json"


# Global parameters used for consistent amount of spacing, independent of user config
# TODO: replace with proper formatter
SPACING_2 = "  "
SPACING_4 = "    "


########################## Functions related to file loading ##########################
def get_schema_dict() -> dict:
    """TODO

    Returns:
        _description_
    """
    with open(SCHEMA_PATH) as file:
        schema_dict = json.load(file)
    return schema_dict


def load_interface_dict(interface_file_path: Path) -> dict:
    """TODO

    Args:
        interface_file_path: _description_

    Raises:
        Exception: _description_

    Returns:
        _description_
    """
    # Note: sys.stdin.isatty() checks if the standard input is interactive. If it is
    # then reading this would freeze the script.
    if interface_file_path == Path("-") and not sys.stdin.isatty():
        input_stream = sys.stdin.read()
        interface_dict = yaml.safe_load(input_stream)
    elif interface_file_path != Path("-"):
        with interface_file_path.open() as file:
            interface_dict = yaml.safe_load(file)
    else:
        raise Exception(
            f"Incorrect input argument input_path: {interface_file_path.name}"
        )

    return interface_dict


################## Functions on (keys of) interface dictionaries ####################
def extract_paths(paths: list[str | dict]) -> list[str]:
    """Collect all IDS paths from a list of strings and dictionaries.

    Args:
        paths: list of strings and / or dictionaries

    Returns:
        list of IDS paths
    """
    path_list = []

    for string_or_dict in paths:
        # Extract paths from string(s) or dictionaries
        if isinstance(string_or_dict, str):
            path_list.append(string_or_dict)
        elif isinstance(string_or_dict, dict):
            key = list(string_or_dict.keys())[0]
            if key not in ["all_or_none", "any_of", "all_of"]:
                # Based on json schema, any other key of dictionary is an IDS path
                path_list.append(key)
            else:
                path_list += extract_paths(string_or_dict[key])
        else:
            raise (
                Exception(
                    f"Invalid entry \n{SPACING_2}'{string_or_dict}'\n in {string_or_dict}"
                )
            )
    return sorted(path_list)
