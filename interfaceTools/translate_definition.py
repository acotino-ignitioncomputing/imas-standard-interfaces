"""Script for translating the IDS paths in an interface to a different DD version"""

import difflib
import logging
from pathlib import Path

from imas import IDSFactory, util
from imas.ids_convert import dd_version_map_from_factories
import yaml

from .utilities import (
    VALID_DD_VERSIONS,
    split_ids_path,
    get_schema_dict,
    load_interface_dict,
    SPACING_2,
)

from .validate_definitions import validate_definitions_dict

# TODO: Fix general logger with formatter
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def translate_path(
    IDS_name: str, IDS_path: str, current_dd_version: str, new_dd_version: str
) -> str:
    """Attempts to translate the provided IDS path to the provided new version of the
    Data Dictionary. Returns an empty string if provided has no corresponding path
    in new_dd_version

    Args:
        IDS_name: Name of the IDS
        IDS_path: IDS path that will be translated
        current_dd_version: Version of the Data Dictionary corresponding with IDS_path
        new_dd_version: Version of the Data Dictionary that IDS_path will be translated
            to.

    Returns:
        The translated IDS path, or an empty string if no translation exists.
    """

    # Create class holding mapping between DD versions
    current_factory = IDSFactory(current_dd_version)
    new_factory = IDSFactory(new_dd_version)
    version_map_class, current_is_lower_version = dd_version_map_from_factories(
        IDS_name, current_factory, new_factory
    )

    # Retrieve dictiontary holding changed paths
    if current_is_lower_version:
        translate_dict = version_map_class.old_to_new
    else:
        translate_dict = version_map_class.new_to_old

    if IDS_path in translate_dict:
        return translate_dict.path[IDS_path]
    else:
        return ""


def translate_block(
    block: dict[str, list], current_dd_version: str, new_dd_version: str
) -> dict[str, list]:
    """Given an all-, all_or_none- or any-block as described by the JSON Schema. This
    functions attempts to translate each IDS path under this block to the provided
    new version of the Data Dictionary.

    Any IDS path without a translation will be mitted.
    The translation does not transfer any path indexing that may be present in the
    IDS paths.

    Args:
        block: An all-, all_or_none- or any-block as described by the JSON Schema.
        current_dd_version: Version of the Data Dictionary corresponding with IDS_path
        new_dd_version: Version of the Data Dictionary that each IDS_path will be
            translated to.
    Returns:
        A copy of provided block where each IDS path is either omitted or translated to
        the new version of the Data Dictionary.
    """

    non_transferable_paths = []
    block_name = tuple(block.keys())[0]

    new_block = {block_name: []}

    # Define dictionary for containing valid paths for each IDS in new DD version
    new_valid_paths: dict[str, list] = {}

    for entry in block[block_name]:
        if isinstance(entry, dict) and "all" in entry:
            # entry is all-block. Update this block
            tmp_block, tmp_non_transf_paths = translate_block(
                entry, current_dd_version, new_dd_version
            )
            new_block[block_name].append(tmp_block)
            non_transferable_paths += tmp_non_transf_paths

        else:
            # entry represents IDS path
            constraints = {}

            if isinstance(entry, str):
                full_IDS_path = entry
            else:
                full_IDS_path = tuple(entry.keys())[0]
                constraints = entry[full_IDS_path]

            IDS_name, IDS_path = split_ids_path(full_IDS_path)

            # Extend new_valid_paths if necessary
            if IDS_name not in new_valid_paths:
                ids_instance = IDSFactory(new_dd_version).new(IDS_name)
                new_valid_paths[IDS_name] = util.find_paths(ids_instance, "")

            # Add IDS_path as is if it is in new DD version
            if IDS_path in new_valid_paths[IDS_name]:
                new_block[block_name].append(entry)
                continue

            # Attempt to translate
            new_IDS_path: str = translate_path(
                IDS_name, IDS_path, current_dd_version, new_dd_version
            )

            if new_IDS_path:
                new_full_IDS_path = f"{IDS_name}/{new_IDS_path}"
                # Replace old IDS path with translated path
                if constraints:
                    path_with_constraints = {new_full_IDS_path: constraints}
                    new_block[block_name].append(path_with_constraints)
                else:
                    new_block[block_name].append(new_full_IDS_path)
            else:
                non_transferable_paths.append(full_IDS_path)

    return new_block, non_transferable_paths


def translate_definition(
    input_path: Path, new_dd_version: str, output_path: Path | None
) -> int:
    """Translate each IDS path in the interface definition to the provided new version
    of the Data Dictionary. If an output_path is provided then the result will be stored
    at that path, otherwise the result is printed to screen.

    Args:
        input_path: absolute or relative path to a YAML file.
        new_dd_version: Version of the Data Dictionary that each IDS_path will be
            translated to.
        output_path: absolute or relative path to store the result in.

    Returns:
        integer representing exit code, where 0 is success and 1 is fail.
    """
    # Load schema
    schema_dict = get_schema_dict()

    # Load interface definition.
    interface_dict = load_interface_dict(input_path)

    # Ensure interfaces validate against schema
    if validate_definitions_dict(interface_dict, schema_dict, True, False) != 0:
        logger.warning(f"Interface '{input_path}' does not validate against schema.")
        return 1

    current_dd_version = interface_dict["dd_version_interface"]

    if current_dd_version == new_dd_version:
        logger.warning(
            f"Interface '{input_path}' does already target DD version {new_dd_version}"
        )
        return 0

    if new_dd_version not in VALID_DD_VERSIONS:
        logger.warning(
            f"Provided DD version {new_dd_version} is not valid. Perhaps you meant"
            + SPACING_2
            + SPACING_2.join(
                difflib.get_close_matches(
                    new_dd_version, VALID_DD_VERSIONS, n=5, cutoff=0.5
                )
            )
        )
        return 0

    # Update key 'dd_version_interface'
    interface_dict["dd_version_interface"] = new_dd_version

    all_non_transferable_paths = []

    for position, block in enumerate(interface_dict["paths"]):
        new_block, non_transferable_paths = translate_block(
            block, current_dd_version, new_dd_version
        )

        interface_dict["paths"][position] = new_block

        all_non_transferable_paths += non_transferable_paths

    # Convert dictionary and list of non-transferable paths to string
    yaml_output = yaml.safe_dump(
        interface_dict, sort_keys=False, default_flow_style=False
    )
    if all_non_transferable_paths:
        yaml_output += "\n# IDS paths that could not be transfered"
        for path in all_non_transferable_paths:
            yaml_output += f"# {path}\n"

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml_output, encoding="utf-8")
        logger.warning(f"Written to file {output_path.name}")
    else:
        print(yaml_output)

    return 0
