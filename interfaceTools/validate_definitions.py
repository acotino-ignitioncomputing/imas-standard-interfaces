"""Script for validating interface definitions against JSON Schema and IMAS Data
Dictionary"""

import difflib
import logging
from pathlib import Path

import jsonschema
from imas import IDSFactory, setup_logging, util

from .utilities import (
    VALID_DD_VERSIONS,
    split_ids_path,
    extract_paths,
    get_schema_dict,
    load_interface_dict,
    SPACING_2,
    SPACING_4,
)

logger = logging.getLogger("validateLogger")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


VALID_CONSTRAINTS = ["allowed_values", "value_range", "same_shape_as"]


def print_nice_error_message(error: jsonschema.exceptions.ValidationError):
    """Error messages from the JSON Schema validator can be difficult to interpret, so
    this function tries to improve these messages based on `schema/jason_schema.json`.

    Args:
        error: Instance of `ValidationError` returned by a jsonschema validator
    """

    if (
        "type" in error.schema
        and error.schema["type"] == "array"
        and error.validator == "uniqueItems"
    ):
        # Duplicate IDS paths in sequence

        # Get list of paths and dictionaries
        list_of_entries: list[str | dict] = error.instance

        # Collect duplicate paths and dictionaries
        duplicate_paths = []
        duplicate_dict = []
        for entry in list_of_entries:
            if isinstance(entry, str) or (
                isinstance(entry, dict)
                and "all_or_none" not in entry
                and "any_of" not in entry
            ):
                # entry represents an IDS path.
                IDS_path = list(entry.keys())[0] if isinstance(entry, dict) else entry
                if list_of_entries.count(entry) > 1 and IDS_path not in duplicate_paths:
                    duplicate_paths.append(IDS_path)
            else:
                # entry is any_of- or all_or_none-block
                if list_of_entries.count(entry) > 1 and entry not in duplicate_dict:
                    duplicate_dict.append(entry)

        logger.warning(
            f"{SPACING_2}The following IDS paths were duplicated in the sequence:"
        )
        if duplicate_paths:
            logger.warning(
                f"\n{SPACING_4}" + f"\n{SPACING_4}".join(duplicate_paths) + "\n"
            )

        if duplicate_dict:
            logger.warning(
                f"\n{SPACING_4}"
                + f"\n{SPACING_4}".join(extract_paths(duplicate_dict))
                + "\n"
            )

    elif (
        "type" in error.schema
        and error.schema["type"] == "array"
        and error.validator == "minItems"
    ):
        # Certain sequences must have length 2 or greater
        logger.warning(f"{SPACING_4}This sequence must have 2 or more entries\n")

    else:
        logger.warning(f"{SPACING_4}" + error.message + "\n")


def validate_against_schema(definition: dict, schema: dict) -> bool:
    """
    Check correctness of the layout of definition with respect to JSON Schema

    Args:
        definition: dictionary-representation of a YAML file
        schema: dictionary-representation of the JSON schema

    Returns:
        bool: whether the definition is correct with respect to the schema
    """

    validator = jsonschema.Draft202012Validator(schema)

    found_errors = validator.iter_errors(definition)

    validation_correct = True
    for error in sorted(found_errors, key=str):
        validation_correct = False

        json_path: str = error.json_path

        logger.warning(f"{SPACING_2}Error at YAML path {json_path}\n")

        # In case error is raised by an anyOf-subschema, re-validate with that
        # subschema to get more detailed error messages
        if "anyOf" in error.schema:
            if isinstance(error.instance, str) and "all" in error.instance:
                tmp_schema = error.schema["anyOf"][1]

                # Add 'subschema_for_constraint_IDS_path' since it is referenced in
                # subschema error.schema["anyOf"][1].
                tmp_schema["$defs"] = schema["$defs"]

                validator_2 = jsonschema.Draft202012Validator(tmp_schema)
            else:
                validator_2 = jsonschema.Draft202012Validator(
                    schema["$defs"]["subschema_for_constraint_IDS_path"]
                )

            found_errors_2 = validator_2.iter_errors(error.instance)
            for error_2 in found_errors_2:
                print_nice_error_message(error_2)
        else:
            print_nice_error_message(error)

    return validation_correct


def check_ids_name(definition: dict, show_suggestions: bool) -> bool:
    """Check that only valid IDS names appear in the definition.

    Args:
        definition: dictionary-representation of YAML file satisfying the schema

    Returns:
        bool: whether any IDS name was invalid
    """

    dd_version = definition["dd_version_interface"]

    correct_ids_names = True

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

            if show_suggestions:
                logger.warning(
                    f"{SPACING_2}Perhaps you meant:"
                    + f"\n{SPACING_4}"
                    + f"\n{SPACING_4}".join(
                        difflib.get_close_matches(
                            ids_name, ids_names_list, n=3, cutoff=0.6
                        )
                    )
                )

    return correct_ids_names


def check_ids_path_in_dd_version(full_IDS_path: str, dd_version: str) -> bool:
    """Checks if the provided IDS path is present in the provided version of the Data
    Dictionary.

    Args:
        full_IDS_path: IDS path of the form IDS_name/IDS_node_path
        dd_version: version of Data Dictionary to use

    Returns:
        True if full_IDS_path is present in Data Dictionary, False otherwise
    """
    # Extract IDS name and path
    IDS_name, IDS_path = split_ids_path(full_IDS_path)

    # Create empty IDS to extract valid paths
    ids_instance = IDSFactory(dd_version).new(IDS_name)
    valid_paths_list = util.find_paths(ids_instance, "")

    return IDS_path in valid_paths_list


def check_ids_paths_in_dd(definition: dict, show_suggestions: bool) -> bool:
    """Check if each IDS path is present in the provided version of the Data Dictionary.

    Args:
        definition: dictionary-representation of YAML file satisfying the schema

    Returns:
        False if any IDS path was invalid, True otherwise
    """

    dd_version = definition["dd_version_interface"]

    all_paths_valid = True

    # Collect all IDS paths
    path_list = extract_paths(definition["paths"])

    for full_IDS_path in path_list:

        if not check_ids_path_in_dd_version(full_IDS_path, dd_version):
            IDS_name, IDS_path = split_ids_path(full_IDS_path)
            logger.warning(
                f"{SPACING_2}IDS path {IDS_path} is not in IDS {IDS_name} for "
                + f"Data Dictionary version {dd_version}.\n"
            )
            all_paths_valid = False

            if show_suggestions:
                # First check if path appears in other DD versions
                dd_versions_with_path = [
                    vers
                    for vers in VALID_DD_VERSIONS
                    if check_ids_path_in_dd_version(full_IDS_path, vers)
                ]
                if dd_versions_with_path:
                    logger.warning(
                        f"{SPACING_2}It is present in version(s)"
                        + f"\n{SPACING_4}"
                        + f"\n{SPACING_4}".join(dd_versions_with_path)
                        + f"\n{SPACING_4}"
                    )
                    continue

                # Next, check for a typo in IDS_path
                ids_instance = IDSFactory(dd_version).new(IDS_name)
                valid_paths_list = util.find_paths(ids_instance, "")
                alternative_paths = difflib.get_close_matches(
                    IDS_path, valid_paths_list, n=3, cutoff=0.6
                )
                if alternative_paths:
                    logger.warning(
                        f"{SPACING_2}Perhaps you meant"
                        + f"\n{SPACING_4}"
                        + f"\n{SPACING_4}".join(alternative_paths)
                        + f"\n{SPACING_4}"
                    )

    return all_paths_valid


def validate_definitions_dict(
    definition_dict: dict, schema_dict: dict, silent: bool, show_suggestions: bool
) -> int:
    """Validate the dictionary representation of a YAML file with respect to the
    JSON Schema. Also check the correctness of the IDS names and paths with respect
    respect to Data Dictionary version mentioned in the YAML file.

    Args:
        definition_dict: dictionary representation of a YAML file.
        schema_dict: dictionary representation of the JSON Schema.
        silent: If set to True, surpress all log messages.
        show_suggestions: if True, provide suggestions for the incorrect paths.

    Returns:
        0 if no issues were found, 1 otherwise
    """

    # Set log level to ERROR in silent-mode
    if silent:
        logger.setLevel(logging.ERROR)

        # imas logger
        setup_logging.logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

        # imas logger
        setup_logging.logger.setLevel(logging.WARNING)

    # Correctness with respect to JSON Schema
    if not validate_against_schema(definition_dict, schema_dict):
        return 1
    #  Check if IDS names are in Data Dictionary
    if not check_ids_name(definition_dict, show_suggestions):
        return 1

    # Check if IDS paths are in Data Dictionary
    if not check_ids_paths_in_dd(definition_dict, show_suggestions):
        return 1

    return 0


def validate_definitions(input_path: Path, silent: bool, show_suggestions: bool) -> int:
    """Validate the syntax of the provided YAML files with respect to the
    JSON Schema. Also checks the correctness of the IDS names and paths
    with respect to Data Dictionary version mentioned in each YAML file.

    Args:
        input_path:  absolute or relative path to YAML file or to folder containing YAML
            files at some depth-level.
        silent: if True, then all log messages are suppressed.
        show_suggestions: if True, provide suggestions for the incorrect paths.

    Returns:
        int: representing exit code, where 0 is success and 1 is fail
    """
    # Set log level to ERROR in silent-mode
    if silent:
        logger.setLevel(logging.ERROR)

        # imas logger
        setup_logging.logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)

        # imas logger
        setup_logging.logger.setLevel(logging.WARNING)

    # Load schema
    schema_dict = get_schema_dict()

    # Get list of YAML file(s)
    if input_path.is_dir():
        # Search for YAML files in subfolders of directory
        list_of_files = sorted(input_path.glob("**/*.yaml"))
        if not list_of_files:
            raise Exception(
                f"The folder '{input_path}' seems to contain no YAML files at any level"
            )
        else:
            logger.info(f"Searching for YAML files in folder {input_path.name}")
    elif input_path.is_file() or input_path == Path("-"):
        # input_path points to single YAML file or represents input stream ('-')
        list_of_files = [input_path]
    else:
        raise Exception(
            f"Provided path '{input_path}' does not point to a file or folder."
        )

    # Validate each YAML file and collect which were incorrect
    incorrect_definitions = []
    for file_path in list_of_files:
        definition_dict = load_interface_dict(file_path)

        file_path_name = file_path.name if file_path != Path("-") else "input stream"
        logger.info(f"\nValidating {file_path_name}...")

        if (
            validate_definitions_dict(
                definition_dict, schema_dict, silent, show_suggestions
            )
            != 0
        ):
            incorrect_definitions.append(file_path.name)
            continue

        logger.info(f"{SPACING_2}All checks passed")

    if incorrect_definitions:
        logger.warning(
            "\nIssues were found in the following file(s)"
            + f"\n{SPACING_2}"
            + f"\n{SPACING_2}".join(incorrect_definitions)
        )

        return 1
    else:
        logger.info("\nNo issues found")

        return 0
