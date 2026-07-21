import sys
from pathlib import Path
import click

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
    files at some depth-level.

    ------------------------ Examples ------------------------

    \b
    To validate a single YAML file
        $imas-interfaces validate example_nice_inv_input.yaml

    \b
    To validate every YAML file inside a folder and its subfolders
        $imas-interfaces validate example_definitions/

    """
    exit_code = validate_definitions(input_path, silent)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
