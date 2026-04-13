"""Script for validating interface definitions against LinkML model and
IMAS Data Dictionary"""

from linkml.validator import validate
from imas import IDSFactory, util
import re


def validate_against_schema(definition: dict, schema: dict) -> bool:
    """
    Check correctness of the layout of definition with respect to LinkML schema
    """

    report = validate(definition, schema, "InterfaceDefinition")

    if not report.results:
        return True
    else:
        for result in report.results:
            print(f"\t{result.message}")
        return False


def check_ids_name(definition: dict) -> bool:
    """Only allow IDS names that are in the Data Dictionary."""

    dd_version = definition["dd_version"]

    ids_names_list = IDSFactory(dd_version).ids_names()

    correct_ids_names = True
    for ids in definition["ids"]:
        ids_name = ids["name"]
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
    for ids_dict in definition["ids"]:
        ids_name = ids_dict["name"]

        # Create empty IDS to extract valid paths from
        ids_instance = IDSFactory(dd_version).new(ids_name)

        valid_paths_list = util.find_paths(ids_instance, "")

        # First check paths in key 'required_paths'
        if "required_paths" in ids_dict:
            for ids_path in ids_dict["required_paths"]:
                # Remove index-notation (if present)
                ids_path_string = re.sub(r"\(.{1,6}\)", "", ids_path)

                if ids_path_string not in valid_paths_list:
                    print(
                        f"\tIDS path {ids_path_string} is not in IDS {ids_name} for "
                        + f"Data Dictionary version {dd_version}."
                    )
                    all_paths_valid = False

        # Next, check paths in key 'constraints'
        if "constraints" in ids_dict:
            for constraint_dict in ids_dict["constraints"]:
                for ids_path in constraint_dict["path"]:
                    # Remove index-notation (if present)
                    ids_path_string = re.sub(r"\(.{1,6}\)", "", ids_path)

                    if ids_path_string not in valid_paths_list:
                        print(
                            f"\tIDS path {ids_path_string} is not in IDS {ids_name} for "
                            + f"Data Dictionary version {dd_version}."
                        )
                        all_paths_valid = False

    return all_paths_valid


# Check IDS paths are in DD


if __name__ == "__main__":
    from pathlib import Path
    import yaml

    schema_path = Path(__file__).parents[0] / "LinkML_schema.yaml"
    with open(schema_path) as file:
        schema_dict = yaml.safe_load(file)

    folder = Path(__file__).parents[1] / "definitions"

    for file_path in sorted(folder.glob("**/*.yaml")):
        with open(file_path) as file:
            definition_dict = yaml.safe_load(file)

        print(f"\nValidating {file_path.name}...")

        # Correctness with respect to LinkML
        if not validate_against_schema(definition_dict, schema_dict):
            continue

        #  Check IDS names are in Data Dictionary
        if "ids" in definition_dict and not check_ids_name(definition_dict):
            continue

        # Check IDS paths are in Data Dictionary
        if "ids" in definition_dict and not check_ids_paths_in_dd(definition_dict):
            continue

        print("\tAll checks passed")
