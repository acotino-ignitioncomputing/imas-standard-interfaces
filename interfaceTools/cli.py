import sys
from pathlib import Path

import click

from interfaceTools.check_dataset import dataset_checker
from interfaceTools.validate_definitions import validate_definitions


@click.group()
def main():
    """Command line interface for IMAS Standard Interfaces."""


@main.command(name="validate")
@click.argument(
    "input_path",
    type=click.Path(exists=True, allow_dash=True, path_type=Path),
    default="-",
)
@click.option("-s", "--silent", is_flag=True, help="If set, suppress any log messages")
def validate(input_path: Path, silent: bool):
    """Validate the syntax of the provided YAML files with respect to the
    JSON Schema. Also checks the correctness of the IDS names and paths
    with respect to the Data Dictionary version mentioned in each YAML file.

    \b
    Args:
    \b
    input_path: absolute or relative path to YAML file or to folder containing YAML
    files at some depth-level. The contents of a YAML file could also be read from
    stdin.

    ------------------------ Examples ------------------------

    \b
    To validate a single YAML file
        $imas-interfaces validate example_nice_inv_input.yaml

    \b
    To validate every YAML file inside a folder and its subfolders
        $imas-interfaces validate example_definitions/

    \b
    Using stdin
        #cat example_nice_inv_input.yaml | imas-interfaces validate

    """

    # First check if standard input is indicated as 'interactive'
    if input_path == Path("-") and sys.stdin.isatty():
        raise click.UsageError("No input given")

    exit_code = validate_definitions(input_path, silent)
    sys.exit(exit_code)


@main.command(name="check_dataset")
@click.argument(
    "dataset_path",
    type=click.Path(exists=False, allow_dash=False, path_type=Path),
)
@click.argument(
    "interface_path",
    type=click.Path(exists=True, allow_dash=True, path_type=Path),
    default="-",
)
@click.option("-s", "--silent", is_flag=True, help="If set, suppress any log messages")
def check_dataset(dataset_path: Path, interface_path: Path, silent: bool):
    """Checks whether the provided IMAS dataset complies with the given IMAS interface.

    \b
    Args:
    \b
    dataset_path: URI to the dataset entry. Only netCDF and HDF5 backends
        are supported.
    \b
    interface_path: Path to the YAML file containing the interface definition. The
        contents of a YAML file could also be read from stdin

    silent: If set to True, suppress all log messages.


    ------------------------ Examples ------------------------

    \b
    Using a netCDF file
        $imas-interfaces check_dataset iter-105027.nc example_efit++IMAS_input.yaml

    \b
    Using stdin
        $cat example_efit++IMAS_input.yaml | imas-interfaces check_dataset iter.nc

    """
    # First check if standard input is indicated as 'interactive'
    if interface_path == Path("-") and sys.stdin.isatty():
        raise click.UsageError("No input given")

    error_code = dataset_checker(dataset_path, interface_path, silent)
    sys.exit(error_code)


if __name__ == "__main__":
    main()
