"""General utility functions"""

import re
import json
import sys
from pathlib import Path

import yaml
from imas import IDSFactory, util, dd_zip

# Path to the JSON schema describing the format of the interface definitions
SCHEMA_PATH = Path(__file__).parents[1] / "schemas" / "json_schema.json"


# Global parameters used for consistent amount of spacing, independent of user config
# TODO: replace with proper formatter
SPACING_2 = "  "
SPACING_4 = "    "

# All valid versions of Data Dictionary
VALID_DD_VERSIONS = dd_zip.dd_xml_versions()


########################## Functions related to file loading ##########################
def get_schema_dict() -> dict:
    """Load the JSON schema

    Returns:
        Dictionary representation of JSON schema
    """
    with open(SCHEMA_PATH) as file:
        schema_dict = json.load(file)
    return schema_dict


def load_interface_dict(interface_file_path: Path) -> dict:
    """Load the interface definition from either a YAML file or standard input (if
    interface_file_path equals "-")

    Args:
        interface_file_path: Path to YAML file. If equal to "-", then stdin is used

    Raises:
        Exception: if interface_file_path equals "-" but stdin is indicated as
        'interactive'

    Returns:
        Dictionary representation of YAML file
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


####################### Functions related to Data Dictionary ########################
def strip_path_indexing(IDS_path: str | dict) -> str | dict:
    """Remove the path indexing as described in
    https://imas-data-dictionary.readthedocs.io/en/latest/IDS-path-syntax.html

    Args:
        full_IDS_path: An IDS path as described by the subschema
            subschema_for_constraint_IDS_path in the JSON Schema. It has the form
            IDS_name/IDS_node_path

    Returns:
        a string equal to full_IDS_path without the path indexing
    """
    stripped_IDS_path: str | dict

    if isinstance(IDS_path, str):
        stripped_IDS_path = re.sub("\([0-9\-\:]{1,}\)", "", IDS_path)
    elif isinstance(IDS_path, dict):
        old_key = tuple(IDS_path.keys())[0]
        new_key = re.sub("\([0-9\-\:]{1,}\)", "", old_key)
        stripped_IDS_path = {}

        stripped_IDS_path[new_key] = IDS_path[old_key]
    else:
        raise (
            "In function strip_path_indexing:\n"
            + f"{SPACING_2}Unexpected type '{type(IDS_path)} for input '{IDS_path}'"
        )

    return stripped_IDS_path


def split_ids_path(full_IDS_path: str) -> tuple[str, str]:
    """Given a full IDS path of the form IDS_name/IDS_node_path where IDS_node_path may
    contain path indexing, return the tuple (IDS_name, IDS_stripped_path) where
    IDS_stripped_path equals IDS_node_path without the path indexing.

    Args:
        full_IDS_path: IDS path of the form IDS_name/IDS_node_path

    Returns:
        2-tuple of strings
    """
    # Remove path indexing
    full_IDS_path = strip_path_indexing(full_IDS_path)

    IDS_name = full_IDS_path.split("/")[0]
    IDS_path = full_IDS_path.replace(f"{IDS_name}/", "")

    return IDS_name, IDS_path


def get_all_child_paths(full_IDS_path: str, dd_version: str) -> list:
    """Given a full IDS path of the form IDS_name/IDS_node_path, return list of all
    lowest level child paths that start with full_IDS_path.

    Args:
        full_IDS_path: IDS path of the form IDS_name/IDS_node_path
        dd_version: version of Data Dictionary to use

    Returns:
        list of all lowest level child paths having the form IDS_name/IDS_node_path.
    """
    IDS_name, IDS_path = split_ids_path(full_IDS_path)

    # Create empty IDS to extract child paths
    ids_instance = IDSFactory(dd_version).new(IDS_name)

    # Search for lower level paths
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


#################### Functions on keys of interface dictionaries ######################
def check_all_criterium(
    all_block: dict, list_of_present_paths: list[str], dd_version: str
) -> list[str]:
    """Checks if all paths in all_block['all'] are present in list_of_present_paths
    and returns a list of paths which were absent.
    It is assumed that no path in list_of_present_paths contains path indexing.

    Args:
        all_block: dictionary with key 'all', as dictated by the schema
        list_of_present_paths: list of full IDS paths of the form IDS_name/IDS_node_path
        dd_version: version of Data Dictionary

    Returns:
        list of
    """

    # Gather all mandatory paths. Paths that are dictionaries have (a) constraint(s)
    mandatory_paths_list = []
    for entry in all_block["all"]:
        if isinstance(entry, str):
            # Strip path indexing...
            mandatory_paths_list.append(strip_path_indexing(entry))

        else:
            # IDS path constraints
            path = tuple(entry.keys())[0]
            mandatory_paths_list.append(strip_path_indexing(path))

    # Replace parent paths with child paths
    mandatory_child_paths_list = []

    for full_IDS_path in mandatory_paths_list:
        mandatory_child_paths_list += get_all_child_paths(full_IDS_path, dd_version)

    return [
        path for path in mandatory_child_paths_list if path not in list_of_present_paths
    ]


def is_any_block_satisfied(
    any_block: dict[str, dict], list_of_present_paths: list[str], dd_version: str
) -> bool:
    """Return True if there is a subset of paths in any_block['any'] that is present
    in list_of_present_paths. It is assumed that no path in list_of_present_paths
    contains path indexing.

    Args:
        any_block: dictionary with key 'any', as dictated by the schema
        list_of_present_paths: list of full IDS paths of the form IDS_name/IDS_node_path
        dd_version: version of Data Dictionary
    """
    # Check if there is a subset contained in list_of_present_paths
    for entry in any_block:
        if isinstance(entry, str):
            # Single IDS path
            if entry in list_of_present_paths:
                return True
        elif isinstance(entry, dict) and "all" in entry:
            # Subset of paths. All must be present
            missing_paths = check_all_criterium(
                entry, list_of_present_paths, dd_version
            )
            return len(missing_paths) == 0
        else:
            raise Exception(f"Illegal entry under any-key: {entry=}")

    return False


def is_all_or_none_satisfied(
    all_or_none_block: dict[list], list_of_present_paths: list[str], dd_version: str
) -> bool:
    """Return True if all of the paths listed in all_or_none_block['all_or_none'] are
    either present or absent in list_of_present_paths.

    Args:
        all_or_none_block: dictionary with key 'all_or_none', as dictated by the schema
        list_of_present_paths: list of full IDS paths of the form IDS_name/IDS_node_path
        dd_version: version of Data Dictionary
    """
    # Get all child paths
    paths_in_block = []
    for full_IDS_path in all_or_none_block["all_or_none"]:
        paths_in_block += get_all_child_paths(
            strip_path_indexing(full_IDS_path), dd_version
        )

    # Check the presence of each path
    path_presence = [path in list_of_present_paths for path in paths_in_block]

    return all(path_presence) == any(path_presence)


######################## Functions on interface dictionaries ##########################
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
            if key not in ["all_or_none", "any", "all"]:
                # Based on json schema, any other key of dictionary is an IDS path
                path_list.append(key)
            else:
                path_list += extract_paths(string_or_dict[key])
        else:
            raise (
                Exception(
                    f"Invalid entry in list of paths:\n{SPACING_2}{string_or_dict}"
                )
            )
    return sorted(path_list)


def check_mandatory_paths(
    interface_dict: dict, list_of_present_paths: list[str]
) -> list[str]:
    """Checks which mandatory IDS paths in interface_dict appear in
    list_of_present_paths. Returns a list of IDS paths that are missing

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema
        list_of_present_paths: list of full IDS paths of the form IDS_name/IDS_node_path

    Returns:
        list of full IDS paths that are mandatory in interface_dict but not present in
        list_of_present_paths
    """
    # Get top-level all-block
    for entry in interface_dict["paths"]:
        if "all" in entry:
            return check_all_criterium(
                entry, list_of_present_paths, interface_dict["dd_version_interface"]
            )
    return []


def check_any_criteria(
    interface_dict: dict, list_of_present_paths: list[str]
) -> list[dict]:
    """Checks each any-criterium in interface_dict and returns a list of any-dicts
    who contain no subset of IDS paths that are present in list_of_present_paths.

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema
        list_of_present_paths: list of full IDS paths of the form IDS_name/IDS_node_path

    Returns:
        List of dictionaries with key 'any' where none of their listed subset of
        paths is in list_of_present_paths
    """
    dd_version = interface_dict["dd_version_interface"]

    # Get list of any-blocks
    any_blocks = [entry for entry in interface_dict["paths"] if "any" in entry]

    return [
        block
        for block in any_blocks
        if not is_any_block_satisfied(block, list_of_present_paths, dd_version)
    ]


def check_all_or_none_criterium(
    interface_dict: dict, list_of_present_paths: list[str]
) -> list[dict]:
    """For each all_or_none-block in interface_dict, check if either all paths are
    are present in list_of_present_paths or all are absent

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema
        list_of_present_paths: list of full IDS paths of the form IDS_name/IDS_node_path

    Returns:
        List of dictionaries with key 'all_or_none' where some of the listed paths are
        present in list_of_present_paths and some are absent.
    """
    dd_version = interface_dict["dd_version_interface"]

    # Get list of all_or_none-blocks
    all_or_none_blocks = [
        entry for entry in interface_dict["paths"] if "all_or_none" in entry
    ]

    return [
        block
        for block in all_or_none_blocks
        if not is_all_or_none_satisfied(block, list_of_present_paths, dd_version)
    ]
