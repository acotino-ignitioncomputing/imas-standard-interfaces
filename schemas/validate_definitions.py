"""Script for validating interface definitions against JSON Schema and IMAS Data
Dictionary"""

import jsonschema
from imas import IDSFactory, util
import re


def print_nice_error_message(message: str):
    # Error messages from the JSON Schema validator can be difficult to interpret.
    # This functions tries to improve the message based on 'schema/jason_schema.json'

    if "has non-unique elements" in message:
        # Duplicate IDS paths in sequence

        # Extract paths from error message instead of using function 'extract_paths'
        # since it is not yet verified that the input YAML file follows the JSON Schema
        list_of_paths = (
            re.match(r"\[.{1,}\]", message)
            .group()
            .replace("[", "")
            .replace("]", "")
            .replace(" ", "")
            .split(",")
        )
        # Collect duplicate paths
        duplicate_paths = []
        for IDS_path in list_of_paths:
            if list_of_paths.count(IDS_path) > 1 and IDS_path not in duplicate_paths:
                duplicate_paths.append(IDS_path)

        print("\tThe following IDS paths were duplicated in the sequence:")
        print("\n\t\t" + "\n\t\t".join(duplicate_paths) + "\n")

    elif "is too short" in message:
        # Certain sequences must have length 2 or greater
        print("\t\tThis sequence has only 1 entry, but must have 2 or more")

    elif "Allow at most one occurence of the" in message:
        # Only one 'all_of' key is allowed under 'paths'
        print(
            "\t\tMultiple 'all_of' keys are present directly under 'paths', but at most"
            + " one is allowed.\n"
        )

    else:
        print("\t\t" + message + "\n")


def validate_against_schema(definition: dict, schema: dict) -> bool:
    """
    Check correctness of the layout of definition with respect to JSON Schema
    """

    validator = jsonschema.Draft202012Validator(schema)

    found_errors = validator.iter_errors(definition)

    validation_correct = True
    for error in sorted(found_errors, key=str):
        validation_correct = False
        print(f"\tError at JSON path {error.json_path}\n")
        print_nice_error_message(error.message)

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
                        Exception(f"Invalid entry \n\t'{entry}'\n in {criterium_dict}")
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
                f"\tIDS name '{ids_name}' is not in Data Dictionary version {dd_version}"
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
        # Extract IDS name and path, and remove any index notation
        ids_name = full_ids_path.split("/")[0]
        ids_path = full_ids_path.replace(f"{ids_name}/", "")
        ids_path = re.sub(r"\(.{1,6}\)", "", ids_path)

        # Create empty IDS to extract valid paths
        ids_instance = IDSFactory(dd_version).new(ids_name)

        valid_paths_list = util.find_paths(ids_instance, "")

        if ids_path not in valid_paths_list:
            print(
                f"\tIDS path {ids_path} is not in IDS {ids_name} for "
                + f"Data Dictionary version {dd_version}."
            )
            all_paths_valid = False

    return all_paths_valid


# Check IDS paths are in DD


if __name__ == "__main__":
    from pathlib import Path
    import argparse
    import json
    import yaml

    # Load schema
    schema_path = Path(__file__).parents[0] / "json_schema.json"
    with open(schema_path) as file:
        schema_dict = json.load(file)

    # From input, get path of YAML-file or folder
    parser = argparse.ArgumentParser(
        prog="validate_definitions",
        description=(
            "Validate the syntax of the provided YAML files with respect to the"
            + " JSON Schema. Also checks the correctness of the IDS names and paths"
            + " with respect to provided Data Dictionary version."
        ),
    )
    parser.add_argument(
        "input_path",
        help=(
            "absolute or relative path to YAML file or to folder containing YAML "
            + " files at some depth-level."
        ),
    )
    args = parser.parse_args()
    input_path = Path(args.input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            "Provided path does not point to an existing file or directory: "
            + f"\n\t{input_path.name}"
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

        print("\tAll checks passed")

    if incorrect_definitions:
        print("\nIssues were found in the following file(s)")
        print("\n\t" + "\n\t".join(incorrect_definitions))
    else:
        print("\nNo issues found")
