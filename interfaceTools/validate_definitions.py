"""Script for validating interface definitions against JSON Schema and IMAS Data
Dictionary"""

import jsonschema
from imas import dd_zip, IDSFactory, util
from pathlib import Path
from packaging.version import Version
import click
import json
import logging
import sys
import yaml

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "

VALID_DD_VERSIONS = dd_zip.dd_xml_versions()


def print_nice_error_message(error: jsonschema.exceptions.ValidationError):
    # Error messages from the JSON Schema validator can be difficult to interpret.
    # This functions tries to improve the message based on 'schema/jason_schema.json'

    json_path = error.json_path

    logger.warning(f"{SPACING_2}Error at YAML path {json_path}\n")

    if error.schema["type"] == "array" and error.validator == "uniqueItems":
        # Duplicate IDS paths in sequence

        # Get list of paths
        list_of_paths = error.instance

        # Collect duplicate paths
        duplicate_paths = []
        for IDS_path in list_of_paths:
            if list_of_paths.count(IDS_path) > 1 and IDS_path not in duplicate_paths:
                duplicate_paths.append(IDS_path)

        logger.warning(
            f"{SPACING_2}The following IDS paths were duplicated in the sequence:"
        )
        logger.warning(f"\n{SPACING_4}" + f"\n{SPACING_4}".join(duplicate_paths) + "\n")

    elif error.schema["type"] == "array" and error.validator == "minItems":
        # Certain sequences must have length 2 or greater
        logger.warning(f"{SPACING_4}This sequence must have 2 or more entries\n")

    elif (
        json_path == "$.paths"
        and error.validator == "not"
        and "Allow at most one occurence of the 'all_of'-key under 'paths'"
        == error.validator_value["description"]
    ):
        # Only one 'all_of' key is allowed under 'paths'
        logger.warning(
            f"{SPACING_4}Multiple 'all_of' keys are present directly under 'paths', but at most"
            + " one is allowed.\n"
        )

    else:
        logger.warning(f"{SPACING_4}" + error.message + "\n")


def validate_against_schema(definition: dict, schema: dict) -> bool:
    """
    Check correctness of the layout of definition with respect to JSON Schema
    """

    validator = jsonschema.Draft202012Validator(schema)

    found_errors = validator.iter_errors(definition)

    validation_correct = True
    for error in sorted(found_errors, key=str):
        validation_correct = False
        print_nice_error_message(error)

    return validation_correct


def extract_paths(paths: list) -> list:
    # Collect all IDS paths from list of strings and dictionaries
    path_list = []

    for string_or_dict in paths:
        # Extract paths from string(s) or dictionaries
        if isinstance(string_or_dict, str):
            path_list.append(string_or_dict)
        elif isinstance(string_or_dict, dict):
            key = list(string_or_dict.keys())[0]
            if key not in ["all_or_none", "any_of", "all_of"]:
                # Only key of dictionary is an IDS path
                path_list.append(key)
            else:
                path_list += extract_paths(string_or_dict[key])
        else:
            raise (
                Exception(
                    f"Invalid entry \n{SPACING_2}'{string_or_dict}'\n in {string_or_dict}"
                )
            )
    return sorted(path_list)


def get_valid_dd_versions(definition: dict) -> list:
    min_version_str, max_version_str = definition["dd_version_range"]
    min_version, max_version = Version(min_version_str), Version(max_version_str)

    valid_dd_versions = [
        version_str
        for version_str in VALID_DD_VERSIONS
        if Version(version_str) >= min_version and Version(version_str) <= max_version
    ]

    if not valid_dd_versions:
        logger.warning(
            f"{SPACING_2}No valid versions of the Data Dictionary fall within the"
            + f" provided range {definition['dd_version_range']}"
        )

    return valid_dd_versions


def check_ids_name(definition: dict) -> bool:
    """Only allow IDS names that are in the Data Dictionary."""

    dd_versions_to_check = get_valid_dd_versions(definition)

    if not dd_versions_to_check:
        return False

    correct_ids_names = True
    for dd_version in dd_versions_to_check:

        ids_names_list = IDSFactory(dd_version).ids_names()

        # Collect all IDS paths
        path_list = extract_paths(definition["paths"])

        for ids_path in path_list:
            ids_name = ids_path.split("/")[0]
            if ids_name not in ids_names_list:
                logger.warning(
                    f"{SPACING_2}IDS name '{ids_name}' is not in Data Dictionary"
                    + f" version {dd_version}\n"
                )
                correct_ids_names = False

    return correct_ids_names


def check_ids_paths_in_dd(definition: dict) -> bool:
    """Each IDS path must be present in the provided version of Data Dictionary."""

    dd_versions_to_check = get_valid_dd_versions(definition)

    if not dd_versions_to_check:
        return False

    all_paths_valid = True

    for dd_version in dd_versions_to_check:

        # Collect all IDS paths
        path_list = extract_paths(definition["paths"])

        for full_ids_path in path_list:
            # Extract IDS name and path
            ids_name = full_ids_path.split("/")[0]
            ids_path = full_ids_path.replace(f"{ids_name}/", "")

            # Create empty IDS to extract valid paths
            ids_instance = IDSFactory(dd_version).new(ids_name)

            valid_paths_list = util.find_paths(ids_instance, "")

            if ids_path not in valid_paths_list:
                logger.warning(
                    f"{SPACING_2}IDS path {ids_path} is not in IDS {ids_name} for "
                    + f"Data Dictionary version {dd_version}.\n"
                )
                all_paths_valid = False

    return all_paths_valid


def validate_definitions(input_path: str, silent: bool):
    """Validate the syntax of the provided YAML files with respect to the
    JSON Schema. Also checks the correctness of the IDS names and paths
    with respect to provided Data Dictionary version.

    Arguments:\n
    INPUT_PATH  absolute or relative path to YAML file or to folder containing YAML
    files at some depth-level.
    """

    # Set log level to ERROR in silent-mode
    if silent:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.WARNING)

    # Load schema
    schema_path = Path(__file__).parents[1] / "schemas" / "json_schema.json"
    with open(schema_path) as file:
        schema_dict = json.load(file)

    # From input, get path of YAML-file or folder
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            "Provided path does not point to an existing file or directory: "
            + f"\n{SPACING_2}{input_path.name}"
        )

    # Get list of YAML file(s)
    if input_path.is_dir():
        list_of_files = sorted(input_path.glob("**/*.yaml"))
        if not list_of_files:
            raise Exception(
                f"The folder '{input_path}' seems to contain no YAML files at any level"
            )
        else:
            logger.warning(f"Searching for YAML files in folder {input_path.name}")
    elif input_path.is_file():
        list_of_files = [input_path]
    else:
        raise Exception(
            f"Provided path '{input_path}' does not point to a file or folder."
        )

    # Validate each YAML file and collect which were incorrect
    incorrect_definitions = []
    for file_path in list_of_files:
        with open(file_path) as file:
            definition_dict = yaml.safe_load(file)

        logger.warning(f"\nValidating {file_path.name}...")

        # Correctness with respect to JSON Schema
        if not validate_against_schema(definition_dict, schema_dict):
            incorrect_definitions.append(file_path.name)
            continue

        #  Check if IDS names are in Data Dictionary
        if not check_ids_name(definition_dict):
            incorrect_definitions.append(file_path.name)
            continue

        # Check if IDS paths are in Data Dictionary
        if not check_ids_paths_in_dd(definition_dict):
            incorrect_definitions.append(file_path.name)
            continue

        logger.warning(f"{SPACING_2}All checks passed")

    if incorrect_definitions:
        if silent:
            # Ensure exiting with non-zero exit code
            sys.exit(1)

        logger.warning(
            "\nIssues were found in the following file(s)"
            + f"\n{SPACING_2}"
            + f"\n{SPACING_2}".join(incorrect_definitions)
        )

        sys.exit(1)
    else:
        logger.warning("\nNo issues found")


@click.command()
@click.argument("input_path")
@click.option("-s", "--silent", is_flag=True, help="If set, supress any log messages")
def main(input_path: str, silent: bool):
    validate_definitions(input_path, silent)


if __name__ == "__main__":
    main()
