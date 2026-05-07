"""Script for validating interface definitions against JSON Schema and IMAS Data
Dictionary"""

import jsonschema
from imas import IDSFactory, util
import re
from pathlib import Path
import click
import json
import yaml

# Global parameters used for consistent amount of spacing, independent of user config
SPACING_2 = "  "
SPACING_4 = "    "


def print_nice_error_message(error: jsonschema.exceptions.ValidationError):
    # Error messages from the JSON Schema validator can be difficult to interpret.
    # This functions tries to improve the message based on 'schema/jason_schema.json'

    json_path = error.json_path

    print(f"{SPACING_2}Error at YAML path {json_path}\n")

    if error.schema["type"] == "array" and error.validator == "uniqueItems":
        # Duplicate IDS paths in sequence

        # Get list of paths
        list_of_paths = error.instance

        # Collect duplicate paths
        duplicate_paths = []
        for IDS_path in list_of_paths:
            if list_of_paths.count(IDS_path) > 1 and IDS_path not in duplicate_paths:
                duplicate_paths.append(IDS_path)

        print(f"{SPACING_2}The following IDS paths were duplicated in the sequence:")
        print(f"\n{SPACING_4}" + f"\n{SPACING_4}".join(duplicate_paths) + "\n")

    elif error.schema["type"] == "array" and error.validator == "minItems":
        # Certain sequences must have length 2 or greater
        print(f"{SPACING_4}This sequence must have 2 or more entries\n")

    elif (
        json_path == "$.paths"
        and error.validator == "not"
        and "Allow at most one occurence of the 'all_of'-key under 'paths'"
        == error.validator_value["description"]
    ):
        # Only one 'all_of' key is allowed under 'paths'
        print(
            f"{SPACING_4}Multiple 'all_of' keys are present directly under 'paths', but at most"
            + " one is allowed.\n"
        )

    else:
        print(f"{SPACING_4}" + error.message + "\n")


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


def extract_paths(definition: dict) -> list:
    # Collect all IDS paths
    path_list = []

    for criterium_dict in definition["paths"]:
        # Extract paths from string(s) or dictionaries
        for string_or_dict in criterium_dict.values():
            for entry in string_or_dict:
                if type(entry) is str:
                    path_list.append(entry)
                elif type(entry) is dict:
                    for _, sublist in entry.items():
                        path_list += sublist
                else:
                    raise (
                        Exception(
                            f"Invalid entry \n{SPACING_2}'{entry}'\n in {criterium_dict}"
                        )
                    )
    return sorted(path_list)


def check_ids_name(definition: dict) -> bool:
    """Only allow IDS names that are in the Data Dictionary."""

    dd_version = definition["dd_version"]

    ids_names_list = IDSFactory(dd_version).ids_names()

    correct_ids_names = True

    # Collect all IDS paths
    path_list = extract_paths(definition)

    for ids_path in path_list:
        ids_name = ids_path.split("/")[0]
        if ids_name not in ids_names_list:
            print(
                f"{SPACING_2}IDS name '{ids_name}' is not in Data Dictionary version {dd_version}"
            )
            correct_ids_names = False

    return correct_ids_names


def check_ids_paths_in_dd(definition: dict) -> bool:
    """Each IDS path must be present in the provided version of Data Dictionary."""
    dd_version = definition["dd_version"]

    all_paths_valid = True

    # Collect all IDS paths
    path_list = extract_paths(definition)

    for full_ids_path in path_list:
        # Extract IDS name and path
        ids_name = full_ids_path.split("/")[0]
        ids_path = full_ids_path.replace(f"{ids_name}/", "")

        # Create empty IDS to extract valid paths
        ids_instance = IDSFactory(dd_version).new(ids_name)

        valid_paths_list = util.find_paths(ids_instance, "")

        if ids_path not in valid_paths_list:
            print(
                f"{SPACING_2}IDS path {ids_path} is not in IDS {ids_name} for "
                + f"Data Dictionary version {dd_version}."
            )
            all_paths_valid = False

    return all_paths_valid


@click.command()
@click.argument("input_path")
def main(input_path: str):
    """Validate the syntax of the provided YAML files with respect to the
    JSON Schema. Also checks the correctness of the IDS names and paths
    with respect to provided Data Dictionary version.

    Arguments:\n
    INPUT_PATH  absolute or relative path to YAML file or to folder containing YAML
    files at some depth-level.
    """

    # Load schema
    schema_path = Path(__file__).parents[0] / "json_schema.json"
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
            print(f"Searching for YAML files in folder {input_path.name}")
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

        print(f"\nValidating {file_path.name}...")

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

        print(f"{SPACING_2}All checks passed")

    if incorrect_definitions:
        print("\nIssues were found in the following file(s)")
        print(f"\n{SPACING_2}" + f"\n{SPACING_2}".join(incorrect_definitions))
    else:
        print("\nNo issues found")


if __name__ == "__main__":
    main()
