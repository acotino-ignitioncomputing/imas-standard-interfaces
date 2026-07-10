"""Script for checking if a provided dataset complies with the provided interface"""

from pathlib import Path
import click
import logging
import sys
import yaml

from validate_definitions import validate_definitions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "


def dataset_compliance(
    input_interface_path: str, input_dataset_path: str, silent: bool
) -> int:

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
    input_interface_path = Path(input_interface_path)
    with open(input_interface_path) as file:
        interface_dict = yaml.safe_load(file)

    # check format dataset (support .nc, hdf5) and load dataset accordingly

    # Check presence of mandatory paths in dataset
    missing_mandatory_paths = check_mandatory_paths(interface_dict, dataset)

    if missing_mandatory_paths:
        logger.warning(
            f"\n{SPACING_2}Following mandatory paths are missing in the dataset:"
            + f"\n{SPACING_4}"
            + f"\n{SPACING_4}".join(missing_mandatory_paths)
        )

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
