"""Script for checking if a provided dataset complies with the provided interface"""

from pathlib import Path
import click
import logging
import sys
import yaml
import netCDF4

from validate_definitions import validate_definitions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "


def extract_mandatory_paths(paths: list) -> dict:
    """Construct dictionary of mandatory IDS paths, so outside any optional-path-key,
    where keys are IDS names and values are lists of IDS paths

    Args:
        paths: paths-key of dictionary-representation of YAML file satisfying the schema

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

            mandatory_paths_dict[IDS_name].append(IDS_path)

    # TODO: also add child paths of parent paths
    return mandatory_paths_dict


def check_presence_mandatory_paths(
    interface_dict: dict, dataset: netCDF4.Dataset
) -> list:
    """Check which mandatory paths of interface_dict are in dataset.

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema
        dataset: netCDF4-dataset of IMAS data

    Returns:
        List[str]: missing IDS paths
    """
    mandatory_paths_dict = extract_mandatory_paths(interface_dict["paths"])

    missing_mandatory_paths = []
    # Check if paths are present in dataset
    for IDS_name, mandatory_paths in mandatory_paths_dict.items():
        for IDS_path in mandatory_paths:
            # Construct path specific to NetCDF4 dataset of IMAS data
            netcdf_path = IDS_path.replace("/", ".")

            if netcdf_path not in dataset[f"{IDS_name}/0"].variables:
                missing_mandatory_paths.append(f"{IDS_name}/{IDS_path}")

    return missing_mandatory_paths


def dataset_compliance(
    input_interface_path: str, input_dataset_path: str, silent: bool
) -> int:
    input_interface_path = Path(input_interface_path)
    input_dataset_path = Path(input_dataset_path)

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

    # Load interface def, (How to load dataset? nc -> xarray (or netcdf4?), hdf5 -> imas.DBEntry)
    with open(input_interface_path) as file:
        interface_dict = yaml.safe_load(file)

    # Check format dataset (support .nc, hdf5 maybe later) and load dataset accordingly
    if input_dataset_path.suffix == ".nc":
        dataset = netCDF4.Dataset(input_dataset_path, mode="r")
    else:
        logger.error("Data format of provided dataset is not supported")
        return 1

    # Check presence of mandatory paths in dataset
    missing_mandatory_paths = check_presence_mandatory_paths(interface_dict, dataset)

    if missing_mandatory_paths:
        logger.warning(
            f"\n{SPACING_2}Following mandatory paths are missing in the dataset:"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_mandatory_paths)
        )

    # Check if present data arrays are non-empty
    # (provide missing_mandatory_paths and skip these)

    # Check all_or_none criteria...

    # Check any_of-criteria

    # Check allowed_values-criteria

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
