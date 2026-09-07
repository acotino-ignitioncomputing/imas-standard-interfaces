"""Script for checking if a provided dataset complies with the provided interface"""

import logging
from pathlib import Path

from imas import DBEntry, IDSFactory

from .utilities import (
    check_all_or_none_criterium,
    check_any_criteria,
    check_mandatory_paths,
    extract_paths,
    get_schema_dict,
    load_interface_dict,
)
from .validate_definitions import validate_definitions_dict

# TODO: Fix general logger with formatter
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "


def get_present_paths(dataset: DBEntry, dd_version: str) -> list[str]:
    """Gather all IDS paths in the dataset that point to a non-empty data array. The
    function `DBENtry.list_filled_paths` is encapsulated in a try-except statement
    to catch the `DataEntryException` whenever an IDS name is not present in the dataset

    Args:
        dataset: IMAS Python DBEntry
        dd_version: version of Data Dictionary to use

    Returns:
        List of IDS paths that point to a non-empty data array in dataset
    """
    IDS_names_list = IDSFactory(dd_version).ids_names()

    list_of_present_paths = []

    for IDS_name in IDS_names_list:
        all_occurrences = dataset.list_all_occurrences(IDS_name)
        for occurrence in all_occurrences:
            # Prepend IDS_name before each path to get full path
            list_of_present_paths += [
                f"{IDS_name}/{path}"
                for path in dataset.list_filled_paths(
                    ids_name=IDS_name, occurrence=occurrence
                )
            ]

    return list_of_present_paths


def dataset_checker(dataset_path: Path, interface_path: Path, silent: bool) -> int:
    """Checks whether the provided IMAS dataset complies with the given IMAS interface.

    Args:
        dataset_path: URI to the dataset entry. Only NetCDF and HDF5 backends
        are supported.
        interface_path: Path to the YAML file containing the interface definition
        silent: If set to True, suppress all log messages.
    """

    # Set log level to ERROR in silent-mode
    if silent:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.WARNING)

    # Load schema
    schema_dict = get_schema_dict()

    # Load interface definition.
    interface_dict = load_interface_dict(interface_path)

    # Ensure interfaces validate against schema
    if validate_definitions_dict(interface_dict, schema_dict, silent=True) != 0:
        logger.warning(
            f"Interface '{interface_path}' does not validate against schema."
        )
        return 1

    # Load dataset
    with DBEntry(dataset_path, "r") as dataset:
        dd_version = interface_dict["dd_version_interface"]

        # Get present paths
        list_of_present_paths = get_present_paths(dataset, dd_version)

        # Check presence of mandatory paths in dataset
        missing_mandatory_paths = check_mandatory_paths(
            interface_dict, list_of_present_paths
        )

        if missing_mandatory_paths:
            logger.warning(
                f"\n{SPACING_2}Following mandatory paths are either empty or missing in"
                + " the dataset:\n"
                + f"\n{SPACING_4}"
                + f"\n{SPACING_4}".join(missing_mandatory_paths)
            )

        # Check the paths under each any-block
        missing_any = check_any_criteria(interface_dict, list_of_present_paths)

        if missing_any:
            logger.warning(
                f"\n{SPACING_2}The following paths are listed as a subset under an"
                f" any-block but no subset was contained in the dataset:\n"
                + f"\n{SPACING_4}"
                + f"\n{SPACING_4}".join(extract_paths(missing_any))
            )

        # Check the paths under each all_or_none-block
        missing_all_or_none = check_all_or_none_criterium(
            interface_dict, list_of_present_paths
        )

        # Logging based on missing_all_or_none
        if missing_all_or_none:
            logger.warning(
                f"\n{SPACING_2}Following paths are under an all_or_none-key, but not"
                + " all are present or absent in the dataset:\n"
                + f"\n{SPACING_4}"
                + f"\n{SPACING_4}".join(extract_paths(missing_all_or_none))
            )

        # TODO: Lastly, check for each path with constraints
        # missing_allowed_values = check_allowed_values(interface_dict, dataset)
        missing_allowed_values = []

    if (
        missing_mandatory_paths
        or missing_all_or_none
        or missing_any
        or missing_allowed_values
    ):
        logger.warning("\nDataset does not comply with interface")
        return 1
    else:
        logger.warning("\nDataset complies with interface")
        return 0
