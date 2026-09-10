import sys
from pathlib import Path

import click

from interfaceTools.check_dataset import dataset_checker
from interfaceTools.validate_definitions import validate_definitions
from interfaceTools.translate_definition import translate_definition
from interfaceTools.compute_difference import compute_difference


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
@click.option(
    "--show_suggestions",
    is_flag=True,
    help=(
        "If set, attempt to provide suggestions for incorrect paths."
        + " Significantly slows down the script."
    ),
)
def validate(input_path: Path, silent: bool, show_suggestions: bool):
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

    exit_code = validate_definitions(input_path, silent, show_suggestions)
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


@main.command(name="translate")
@click.argument(
    "input_path",
    type=click.Path(exists=True, allow_dash=True, path_type=Path),
    default="-",
)
@click.argument(
    "new_dd_version",
    type=str,
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Write output to a file instead of stdout.",
)
def translate(input_path: Path, new_dd_version: str, output: Path | None):
    """Translates the IDS paths of the provided YAML file to the provided version of the
    Data Dictionary and prints the results to screen.

    Notes:
    Path indexing is not transfered during translating.
    All paths that could not be translated are placed in comments at the bottom.

    \b
    Args:
    \b
    input_path: absolute or relative path to YAML file. The contents of a YAML file
    could also be read from stdin.
    new_dd_version: target version of the Data Dictionary.
    output: absolute or relative path to store the result in.

    ------------------------ Examples ------------------------

    \b
    To translate a single YAML file to DD version 4.0.0
        $imas-interfaces translate input_efit++IMAS_dd_3.42.0.yaml 4.0.0

    \b
    Save output to file
        $imas-interfaces translate -o result.yaml input_efit++IMAS_dd_3.42.0.yaml 4.0.0
    """

    # First check if standard input is indicated as 'interactive'
    if input_path == Path("-") and sys.stdin.isatty():
        raise click.UsageError("No input given")

    exit_code = translate_definition(input_path, new_dd_version, output)
    sys.exit(exit_code)


@main.command(name="difference")
@click.argument(
    "input_path_1",
    type=click.Path(exists=True, allow_dash=True, path_type=Path),
)
@click.argument(
    "input_path_2",
    type=click.Path(exists=True, allow_dash=True, path_type=Path),
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Write output to a file instead of stdout.",
)
@click.option(
    "--ignore_optional_paths",
    is_flag=True,
    help=("If set, ignore the optional paths in input_path_2."),
)
def difference(
    input_path_1: Path,
    input_path_2: Path,
    output: Path | None,
    ignore_optional_paths: bool,
):
    """Checks which criteria in input_path_1 are not satisfied by input_path_2 and
    prints a leftover interface of input_path_1 of all the unsatisfied criteria. This
    result is saved in output_path if this path is provided.

    For simplicity, path indexing is ignored.

    \b
    Args:
    \b
    input_path_1: absolute or relative path to YAML file.
    input_path_2: absolute or relative path to YAML file.

    ------------------------ Examples ------------------------

    \b
    To compute the difference
        $imas-interfaces difference output_nice_imas_inv.yaml input_torax.yaml

    \b
    Ignore the optional paths
        $imas-interfaces difference --ignore_optional_paths output.yaml input.yaml

    \b
    Save to file
        $imas-interfaces difference -o output.yaml output_nice.yaml input_torax.yaml

    """

    exit_code = compute_difference(
        input_path_1, input_path_2, output, ignore_optional_paths
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
