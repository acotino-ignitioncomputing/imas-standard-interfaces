"""Script for checking if a provided dataset complies with the provided interface"""

from pathlib import Path
import click
import logging
import sys
import yaml
from imas import DBEntry, util
from imas.exception import DataEntryException

from validate_definitions import validate_definitions, extract_paths

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "


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


def is_path_in_dataset(dataset, path):
    # docs, typehints
    IDS_name = path.split("/")[0]

    return path in get_filled_paths(dataset, IDS_name)


def check_mandatory_paths(interface_dict: dict, dataset: DBEntry) -> list:
    """Check which mandatory paths of interface_dict are in dataset.

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema
        dataset: IMAS Python DBEntry

    Returns:
        List[str]: missing IDS paths
    """
    mandatory_paths_list = [
        path for path in interface_dict["paths"] if isinstance(path, str)
    ]

    # Get all child paths by searching for 'IDS_path' and selecting those paths
    # of the form IDS_path/other_string
    mandatory_child_paths_list = []
    for full_IDS_path in mandatory_paths_list:
        IDS_name = full_IDS_path.split("/")[0]
        IDS_path = full_IDS_path.replace(f"{IDS_name}/", "")

        mandatory_child_paths_list += [
            child_path
            for child_path in util.find_paths(
                dataset.get(IDS_name, lazy=True), IDS_path
            )
            if "/" in child_path.replace(IDS_path, "")
        ]

    return [
        path
        for path in mandatory_child_paths_list
        if not is_path_in_dataset(dataset, path)
    ]


def check_all_or_none_block(interface_dict: dict, dataset: DBEntry) -> list:
    """TODO: write docstring"""
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


@click.command()
@click.argument("input_interface_path")
@click.argument("input_dataset_path")
@click.option("-s", "--silent", is_flag=True, help="If set, supress any log messages")
def main(input_interface_path: str, input_dataset_path: str, silent: bool):
    error_code = dataset_compliance(input_interface_path, input_dataset_path, silent)
    sys.exit(error_code)


if __name__ == "__main__":
    main()
