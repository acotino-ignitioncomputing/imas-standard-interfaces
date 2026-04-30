"""Script for validating interface definitions against JSON Schema and IMAS Data
Dictionary"""

import jsonschema
from imas import IDSFactory, util
import re


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
        print(f"\t{error.message}\n")

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
    import json
    import yaml

    schema_path = Path(__file__).parents[0] / "json_schema.json"
    with open(schema_path) as file:
        schema_dict = json.load(file)

    folder = Path(__file__).parents[1] / "example_definitions"

    incorrect_definitions = []

    # for file_path in sorted(folder.glob("**/*.yaml")):
    folder_tmp = Path(__file__).parents[1] / "tmp_defs"
    for file_path in sorted(folder_tmp.glob("**/*.yaml")):
        with open(file_path) as file:
            definition_dict = yaml.safe_load(file)

        print(f"\nValidating {file_path.name}...")

        # Correctness with respect to JSON Schema
        if not validate_against_schema(definition_dict, schema_dict):
            incorrect_definitions.append(file_path.name)
            continue

        #  Check IDS names are in Data Dictionary
        if not check_ids_name(definition_dict):
            incorrect_definitions.append(file_path.name)
            continue

        # Check IDS paths are in Data Dictionary
        if not check_ids_paths_in_dd(definition_dict):
            incorrect_definitions.append(file_path.name)
            continue

        print("\tAll checks passed")

    if incorrect_definitions:
        print("\nIssues were found in the following file(s)")
        print("\n\t" + "\n\t".join(incorrect_definitions))
    else:
        print("\nNo issues found")
