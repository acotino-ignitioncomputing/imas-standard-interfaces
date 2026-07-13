"""Script for checking if a provided dataset complies with the provided interface"""

from pathlib import Path
import click
import logging
import sys
import yaml
from imas import DBEntry, util
from imas.exception import DataEntryException

from validate_definitions import validate_definitions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "


def extract_mandatory_paths(paths: list, dataset: DBEntry) -> dict:
    """Construct dictionary of mandatory IDS paths, so outside any optional-path-key,
    where keys are IDS names and values are lists of IDS paths

    Args:
        paths: paths-key of dictionary-representation of YAML file satisfying the schema
        dataset: IMAS Python DBEntry, mainly used for accessing path-search functions

    Returns:
        dict: {IDS-name: [mandatory paths]}
    """

    # Construct dictionary {IDS-name: [mandatory paths]}
    mandatory_paths_dict = {}
    for entry in paths:
        # Filter optional paths
        if isinstance(entry, str) or (
            isinstance(entry, dict)
            and "all_or_none" not in entry
            and "any_of" not in entry
        ):
            full_IDS_path = list(entry.keys())[0] if isinstance(entry, dict) else entry
            IDS_name = full_IDS_path.split("/")[0]
            IDS_path = full_IDS_path.replace(f"{IDS_name}/", "")

            if IDS_name not in mandatory_paths_dict:
                mandatory_paths_dict[IDS_name] = []

            # Get all child paths by searching for 'IDS_path' and selecting those paths
            # of the form IDS_path/other_string
            mandatory_paths_dict[IDS_name] += [
                child_path
                for child_path in util.find_paths(
                    dataset.get(IDS_name, lazy=True), IDS_path
                )
                if "/" in child_path.replace(IDS_path, "")
            ]

    return mandatory_paths_dict


def get_filled_paths(dataset: DBEntry, IDS_name: str) -> list:
    """Wrapper for function `DBENtry.list_filled_paths` that catches the exception
    DataEntryException and returns empty list. This exceptio occurs whenever the
    IDS_name is not found.
    """

    try:
        filled_paths = dataset.list_filled_paths(IDS_name)
    except DataEntryException:
        filled_paths = []
    return filled_paths


def check_mandatory_paths(interface_dict: dict, dataset: DBEntry) -> list:
    """Check which mandatory paths of interface_dict are in dataset.

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema
        dataset: IMAS Python DBEntry

    Returns:
        List[str]: missing IDS paths
    """
    mandatory_paths_dict = extract_mandatory_paths(interface_dict["paths"], dataset)

    missing_mandatory_paths = []
    # Check if paths are present in dataset
    for IDS_name, mandatory_paths in mandatory_paths_dict.items():
        present_paths = get_filled_paths(dataset, IDS_name)
        missing_mandatory_paths += [
            f"{IDS_name}/{IDS_path}"
            for IDS_path in mandatory_paths
            if IDS_path not in present_paths
        ]

    return missing_mandatory_paths


def check_all_or_none_block(interface_dict: dict, dataset: DBEntry) -> list:

    # Get list of sublists of IDS paths under an all_or_none-key
    all_or_none_list: list[list[str]] = [
        entry["all_or_none"]
        for entry in interface_dict["paths"]
        if isinstance(entry, dict) and "all_or_none" in entry
    ]

    missing_all_or_none = []
    for sublist in all_or_none_list:
        is_present_list: list[bool] = []

        for full_path in sublist:
            IDS_name = full_path.split("/")[0]
            IDS_path = full_path.replace(f"{IDS_name}/", "")

            present_paths = get_filled_paths(dataset, IDS_name)

            # Collect whether IDS path is in dataset or not
            is_present_list.append(IDS_path in present_paths)

        # Check if there was a present path and an absent path
        if all(is_present_list) != any(is_present_list):
            missing_all_or_none += sublist

    return missing_all_or_none


def dataset_compliance(
    input_interface_path: str, input_dataset_path: str, silent: bool
) -> int:
    input_interface_path = Path(input_interface_path)

    # Set log level to ERROR in silent-mode
    if silent:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.WARNING)

    # Ensure interfaces validate against schema
    if validate_definitions(input_interface_path, silent=True) != 0:
        logger.warning(
            f"Interface '{input_interface_path}' does not validate against schema."
        )
        return 1

    # Load interface definition
    with input_interface_path.open() as file:
        interface_dict = yaml.safe_load(file)

    # Load dataset
    dataset = DBEntry(input_dataset_path, "r")

    # Check presence of mandatory paths in dataset
    missing_mandatory_paths = check_mandatory_paths(interface_dict, dataset)

    if missing_mandatory_paths:
        logger.warning(
            f"\n{SPACING_2}Following mandatory paths are either empty or missing in the"
            + " dataset:"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_mandatory_paths)
        )

    # Paths listed under all_or_none should either be all present or all absent in
    # interface_A
    missing_all_or_none = check_all_or_none_block(interface_dict, dataset)

    # Logging based on missing_all_or_none
    if missing_all_or_none:
        logger.warning(
            f"\n{SPACING_2}Following paths are under an all_or_none-key, but not all"
            + " are present or absent in the dataset:\n"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_all_or_none)
        )

    # Check any_of-criteria

    # Check allowed_values-criteria

    dataset.close()

    if missing_mandatory_paths:
        logger.warning("\nDataset does not comply with interface")
        return 1
    else:
        logger.warning("\nDataset complies with interface")
        return 0


@click.command()
@click.argument("input_interface_path")
@click.argument("input_dataset_path")
@click.option("-s", "--silent", is_flag=True, help="If set, supress any log messages")
def main(input_interface_path: str, input_dataset_path: str, silent: bool):
    error_code = dataset_compliance(input_interface_path, input_dataset_path, silent)
    sys.exit(error_code)


if __name__ == "__main__":
    main()
