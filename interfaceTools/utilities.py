# General utility functions

import sys
import yaml
import json
from pathlib import Path
from imas import util, IDSFactory

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


def split_path_allowed_values(IDS_path_with_allowed_values: dict) -> tuple[str, list]:
    """Splits the IDS path with allowed_values-criterium into a the IDS path and the
    list of allowed values.

    Args:
        IDS_path_with_allowed_values: dictionary whose key is an IDS path and whose
        value is the dictionary {allowed_values: [...]}

    Returns:
        tuple of the IDS path as a string and its allowed values as a list
    """

    IDS_path = tuple(IDS_path_with_allowed_values.keys())[0]
    allowed_values_list = IDS_path_with_allowed_values[IDS_path]["allowed_values"]

    return (IDS_path, allowed_values_list)


def get_all_child_paths(full_IDS_path: str, dd_version: str) -> list:
    """Given a full IDS path of the form IDS_name/IDS_node_path, return list of all
    lowest level child paths having the same form.

    Args:
        full_IDS_path: IDS path of the form IDS_name/IDS_node_path
        dd_version: version of Data Dictionary to use

    Returns:
        list of all lowest level child paths having the form IDS_name/IDS_node_path.
    """
    IDS_name = full_IDS_path.split("/")[0]
    IDS_path = full_IDS_path.replace(f"{IDS_name}/", "")

    # Create empty IDS to extract child paths
    ids_instance = IDSFactory(dd_version).new(IDS_name)

    # Search for lowerlevel paths
    all_child_paths = [
        f"{IDS_name}/{child_path}"
        for child_path in util.find_paths(ids_instance, f"{IDS_path}/")
    ]

    if not all_child_paths:
        # No paths underneath, so full_IDS_path was lowest level child path
        return [full_IDS_path]

    # Return all lowest level child paths
    return [
        path
        for path in all_child_paths
        if not util.find_paths(ids_instance, f"{path}/")
    ]


def check_mandatory_paths(
    interface_dict: dict, list_of_present_paths: list[str]
) -> list[str]:
    """Checks which mandatory IDS paths in interface_dict appear in
    list_of_present_paths. Returns a list of IDS paths that were missing

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema
        list_of_present_paths: list of full IDS paths of the form IDS_name/IDS_node_path

    Returns:
        list of full IDS paths that were mandatory in interface_dict but not present in
        list_of_present_paths
    """
    # Gather all mandatory paths. Handle paths with an allowed_valued criterium
    mandatory_paths_list = []
    for entry in interface_dict["paths"]:
        if isinstance(entry, str):
            mandatory_paths_list.append(entry)

        if (
            isinstance(entry, dict)
            and "any_of" not in entry
            and "all_or_none" not in entry
        ):
            # IDS path with allowed_values criterium

            path, _ = split_path_allowed_values(entry)
            mandatory_paths_list.append(path)

    # Replace parent paths with child paths
    mandatory_child_paths_list = []
    dd_version = interface_dict["dd_version_range"][0]

    for full_IDS_path in mandatory_paths_list:
        mandatory_child_paths_list += get_all_child_paths(full_IDS_path, dd_version)

    return [path for path in mandatory_paths_list if path not in list_of_present_paths]
