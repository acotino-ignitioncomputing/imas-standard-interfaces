"""Script for checking if a provided dataset complies with the provided interface"""

from pathlib import Path
import logging
from imas import DBEntry, IDSFactory
from imas.exception import DataEntryException

from .validate_definitions import validate_definitions_dict
from .utilities import extract_paths, load_interface_dict, check_mandatory_paths

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "


def get_present_paths(dataset: DBEntry, dd_version: str) -> list[str]:
    """Gather all IDS paths that point to a non-empty data array in dataset. The
    function `DBENtry.list_filled_paths` is encapsulated in a try-except statement
    to catch the `DataEntryException` whenever an IDS name is not found in dataset.

    Args:
        dataset: IMAS Python DBEntry
        dd_version: version of Data Dictionary to use

    Returns:
        List of IDS paths that point to a non-empty data array in dataset
    """
    IDS_names_list = IDSFactory(dd_version).ids_names()

    list_of_present_paths = []

    for IDS_name in IDS_names_list:
        try:
            # Prepend IDS_name before each path to get full path
            list_of_present_paths += [
                f"{IDS_name}/{path}" for path in dataset.list_filled_paths(IDS_name)
            ]
        except DataEntryException:
            # IDS name not found
            continue

    return list_of_present_paths


def check_all_or_none_block(interface_dict: dict, dataset: DBEntry) -> list:
    """For each all_or_none-block in interface_dict, check if either all paths are
    are present in dataset or none are present

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema
        dataset: IMAS Python DBEntry

    Returns:
        List[str]: IDS paths from an all_or_none-block in interface that are not all
            present or absent in dataset
    """
    # Get list of sublists of IDS paths under each all_or_none-key
    all_or_none_list: list[list[str]] = [
        entry["all_or_none"]
        for entry in interface_dict["paths"]
        if isinstance(entry, dict) and "all_or_none" in entry
    ]

    missing_all_or_none = []
    for sublist in all_or_none_list:
        is_present_list: list[bool] = []

        # Collect whether IDS path is in dataset or not
        is_present_list = [is_path_in_dataset(dataset, path) for path in sublist]

        # Check if there was a present path and an absent path
        if all(is_present_list) != any(is_present_list):
            missing_all_or_none += sublist

    return missing_all_or_none


def check_any_of_blocks(interface_dict: dict, dataset: DBEntry) -> list:
    """TODO: write docstring"""
    # Get list of dict of IDS paths under each any_of-key
    optional_path_list: list[dict] = [
        entry
        for entry in interface_dict["paths"]
        if isinstance(entry, dict) and "any_of" in entry
    ]

    missing_any_of = []
    for d in optional_path_list:

        # Per any_of-block, check if any subset of paths is present
        any_present = False
        for str_or_dict in d["any_of"]:
            if isinstance(str_or_dict, str) and is_path_in_dataset(
                dataset, str_or_dict
            ):
                any_present = True
                break
            if isinstance(str_or_dict, dict) and "all_of" in str_or_dict:
                # Top any_of-key is satisfied if every path under all_of-key is present
                all_present = True
                for path in str_or_dict["all_of"]:
                    if not is_path_in_dataset(dataset, path):
                        all_present = False
                        break
                any_present = all_present

        if not any_present:
            missing_any_of += extract_paths(d["any_of"])

    return missing_any_of


def check_allowed_values(interface_dict: dict, dataset: DBEntry) -> list:
    # docstring
    # return list[str]: paths which don't satisfy the allowed_value constraint in interface B

    return []


def dataset_checker(dataset_path: Path, interface_path: Path, silent: bool) -> int:

    # Set log level to ERROR in silent-mode
    if silent:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.WARNING)

    # Load interface definition.
    interface_dict = load_interface_dict(interface_path)

    # Ensure interfaces validate against schema
    if validate_definitions_dict(interface_dict, silent=True) != 0:
        logger.warning(
            f"Interface '{interface_path}' does not validate against schema."
        )
        return 1
    # Load dataset
    dataset = DBEntry(dataset_path, "r")

    # Get present paths
    dd_version = interface_dict["dd_version_range"][0]
    list_of_present_paths = get_present_paths(dataset, dd_version)

    # Check presence of mandatory paths in dataset
    missing_mandatory_paths = check_mandatory_paths(
        interface_dict, list_of_present_paths
    )

    breakpoint()

    if missing_mandatory_paths:
        logger.warning(
            f"\n{SPACING_2}Following mandatory paths are either empty or missing in the"
            + " dataset:\n"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_mandatory_paths)
        )

    # Paths listed under all_or_none should either be all present or all absent in
    # dataset
    missing_all_or_none = check_all_or_none_block(interface_dict, dataset)

    # Logging based on missing_all_or_none
    if missing_all_or_none:
        logger.warning(
            f"\n{SPACING_2}Following paths are under an all_or_none-key, but not all"
            + " are present or absent in the dataset:\n"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_all_or_none)
        )

    # Check the paths under each any_of-block
    missing_any_of = check_any_of_blocks(interface_dict, dataset)

    if missing_any_of:
        logger.warning(
            f"\n{SPACING_2}The following paths are listed as a subset under an"
            f" any_of-block but no subset was contained in the dataset:\n"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_any_of)
        )

    # TODO: Lastly, check for allowed_values
    missing_allowed_values = check_allowed_values(interface_dict, dataset)

    dataset.close()

    if (
        missing_mandatory_paths
        or missing_all_or_none
        or missing_any_of
        or missing_allowed_values
    ):
        logger.warning("\nDataset does not comply with interface")
        return 1
    else:
        logger.warning("\nDataset complies with interface")
        return 0
