"""Script for checking the compatibility of two provided interfaces."""

from pathlib import Path
import click
import logging
import sys
import yaml

from validate_definitions import validate_definitions, extract_paths

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def check_mandatory_paths(interface_A_dict, interface_B_dict):
    """Check which mandatory paths of interface_B are listed in interface_A

    Args:
        interface_A_dict: dictionary-representation of YAML file satisfying the schema
        interface_B_dict: dictionary-representation of YAML file satisfying the schema

    Returns:
        List[str]:  IDS paths not present in interface_A, but listed as mandatory in
            interface_B
    """
    mandatory_paths_list_A = [
        path for path in interface_A_dict["paths"] if isinstance(path, str)
    ]
    mandatory_paths_list_B = [
        path for path in interface_B_dict["paths"] if isinstance(path, str)
    ]

    return [
        path for path in mandatory_paths_list_B if path not in mandatory_paths_list_A
    ]


def check_all_or_none_block(interface_A_dict, interface_B_dict):
    """For each all_or_none-block in interface_B_dict, check if either all paths are
    are listed in interface_A_dict or none are listed

    Args:
        interface_A_dict: dictionary-representation of YAML file satisfying the schema
        interface_B_dict: dictionary-representation of YAML file satisfying the schema

    Returns:
        List[str]: IDS paths from an all_or_none-block in interface_B that are not all
            present or absent in interface A
    """
    mandatory_paths_list_A = [
        path for path in interface_A_dict["paths"] if isinstance(path, str)
    ]

    all_or_none_list: list[list[str]] = [
        entry["all_or_none"]
        for entry in interface_B_dict["paths"]
        if isinstance(entry, dict) and "all_or_none" in entry
    ]

    missing_all_or_none = []
    for sublist in all_or_none_list:
        is_present = [(path in mandatory_paths_list_A) for path in sublist]

        # Check if there was a present path and an absent path
        if all(is_present) != any(is_present):
            missing_all_or_none += sublist

    return missing_all_or_none


def check_any_of_blocks(interface_A_dict, interface_B_dict):
    # documentation
    # return list[str]: paths from any_of-block where no subset is contained in interface_A

    # Any of the paths listed under an any_of-block should be in interface_A

    mandatory_paths_list_A = [
        path for path in interface_A_dict["paths"] if isinstance(path, str)
    ]

    optional_path_list: list[dict] = [
        entry
        for entry in interface_B_dict["paths"]
        if isinstance(entry, dict) and "any_of" in entry
    ]

    missing_any_of = []
    for d in optional_path_list:
        any_present = False
        for str_or_dict in d["any_of"]:
            if isinstance(str_or_dict, str) and str_or_dict in mandatory_paths_list_A:
                any_present = True
                break
            if isinstance(str_or_dict, dict) and "all_of" in str_or_dict:
                # Top any_of-key is satisfied if every path under all_of-key is present
                all_present = True
                for path in str_or_dict["all_of"]:
                    if path not in mandatory_paths_list_A:
                        all_present = False
                        break
                any_present = all_present

        if not any_present:
            missing_any_of += extract_paths(d["any_of"])

    return missing_any_of


def check_allowed_values(interface_A_dict, interface_B_dict):
    # docstring
    # return list[str]: paths which don't satisfy the allowed_value constraint in interface B

    return []


def check_compatibility(path_interface_A: str, path_interface_B: str, silent: bool):
    """Check if the provided output interface is compatible with the provided
    input interface.

    Interface_A is called compatible with interface_B, if all IDS paths and constraints
    listed in interface_B are also present in Interface_A.

    Args:
        path_interface_A: path to YAML file containing definition for interface_A
        path_interface_B: path to YAML file containing definition for interface_B
        silent: whether to print log messages.
    """

    # Set log level to ERROR in silent-mode
    if silent:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.WARNING)

    # Ensure interfaces validate against schema
    if validate_definitions(path_interface_A, silent=True) != 0:
        logger.warning(
            f"Interface '{path_interface_A}' does not validate against schema."
        )
        return 1

    if validate_definitions(path_interface_B, silent=True) != 0:
        logger.warning(
            f"Interface '{path_interface_B}' does not validate against schema."
        )
        return 1

    # Load YAML files
    path_interface_A = Path(path_interface_A)
    path_interface_B = Path(path_interface_B)

    with open(path_interface_A) as file:
        interface_A_dict = yaml.safe_load(file)

    with open(path_interface_B) as file:
        interface_B_dict = yaml.safe_load(file)

    logger.warning(
        f"\nCheck if interface '{path_interface_A}' is compatible with"
        f" '{path_interface_B}' ..."
    )

    # If interface_A contains optional paths then 'compatibility' is ill-defined
    if any(
        [
            isinstance(entry, dict) and ("any_of" in entry or "all_or_none" in entry)
            for entry in interface_A_dict["paths"]
        ]
    ):
        logger.warning(
            f"WARNING: interface '{path_interface_A}' lists optional paths "
            + "such that 'compatibility' is ill-defined."
        )

    # First check mandatory IDS paths, and collect which are missing
    missing_mandatory_paths = check_mandatory_paths(interface_A_dict, interface_B_dict)

    if missing_mandatory_paths:
        logger.warning(
            f"\n{SPACING_2}Following mandatory paths are missing:"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_mandatory_paths)
        )

    # Next, check for the optional paths in interface_B.

    # Paths listed under all_or_none should either be all present or all absent in
    # interface_A
    missing_all_or_none = check_all_or_none_block(interface_A_dict, interface_B_dict)

    # Logging based on missing_all_or_none
    if missing_all_or_none:
        logger.warning(
            f"\n{SPACING_2}Following paths are under an all_or_none-key, but not all are "
            + f"present or absent in interface '{path_interface_A}':\n"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_all_or_none)
        )

    # Check the paths under each any_of-block
    missing_any_of = check_any_of_blocks(interface_A_dict, interface_B_dict)

    if missing_any_of:
        logger.warning(
            f"\n{SPACING_2}The following paths are listed as a subset under an any_of-block,"
            f" but no subset was contained in interface '{path_interface_A}':\n"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_any_of)
        )

    # TODO: Lastly, check for allowed_values
    missing_allowed_values = check_allowed_values(interface_A_dict, interface_B_dict)

    if (
        missing_mandatory_paths
        or missing_all_or_none
        or missing_any_of
        or missing_allowed_values
    ):
        logger.warning("\nInterfaces are not compatible")

        return 1
    else:
        logger.warning("\nNo issues found in the compability check")
        return 0


@click.command()
@click.argument("path_interface_a")
@click.argument("path_interface_b")
@click.option("-s", "--silent", is_flag=True, help="If set, supress any log messages")
def main(path_interface_a: str, path_interface_b: str, silent: bool):
    error_code = check_compatibility(path_interface_a, path_interface_b, silent)
    sys.exit(error_code)


if __name__ == "__main__":
    main()
