"""Script for computing the difference between two interfaces"""

import logging
from pathlib import Path
import yaml

from .utilities import (
    strip_path_indexing,
    get_schema_dict,
    load_interface_dict,
    SPACING_2,
)

from .validate_definitions import validate_definitions_dict

# TODO: Fix general logger with formatter
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_paths_list(
    interface_dict: dict, ignore_optional_paths: bool
) -> list[str | dict]:
    """From the paths-block in interface_dict, retrieve all the IDS paths and return
    them in a single list.

    For simplification of comparing two interfaces, path indexing is removed.

    Args:
        interface_dict: dictionary-representation of YAML file satisfying the schema.
        ignore_optional_paths: If True, also consider the optional paths in
            interface_dict. Otherwise only consider the IDS paths under the key 'all'
            directly under 'paths'.

    Returns:
        A list of IDS paths as described by the subschema
        subschema_for_constraint_IDS_path in the JSON Schema.
    """

    # First collect the IDS paths
    present_paths_list: list[str | dict] = []
    for entry in interface_dict["paths"]:
        if "all" in entry:
            present_paths_list += entry["all"]

        if not ignore_optional_paths:
            if "all_or_none" in entry:
                present_paths_list += entry["all_or_none"]

            if "any" in entry:
                for any_entry in entry["any"]:
                    if isinstance(any_entry, dict) and "all" in any_entry:
                        present_paths_list += any_entry["all"]
                    else:
                        present_paths_list.append(any_entry)

    # Remove path indexing
    return [strip_path_indexing(path) for path in present_paths_list]


def is_path_satisfied(
    IDS_path_with_constraints: str | dict, paths_list: list[str | dict]
) -> bool:
    """Checks if IDS_path_with_constraints is present in paths_list and whether its
    constraints are also satisfied by the corresponding IDS path in paths_list.

    For simplicity, path indexing is ignored.

    Args:
        IDS_path_with_constraints: An IDS path as described by the subschema
            subschema_for_constraint_IDS_path in the JSON Schema.
        paths_list: a list of IDS paths as described by the subschema
            subschema_for_constraint_IDS_path.

    Returns:
        In case IDS_path_with_constraints is a str, returns True if it coincides with a
        str or dictionary key in paths_list.
        In case IDS_path_with_constraints is a dict, returns True if its key coincides
        with a dictionary key in paths_list and the values of its constraints fall
        within the values of the corresponding dict.
    """
    full_IDS_path: str
    constraints: dict = {}

    # First, extract contraints and full_IDS_path
    if isinstance(IDS_path_with_constraints, str):
        full_IDS_path = strip_path_indexing(IDS_path_with_constraints)
    else:
        full_IDS_path = tuple(IDS_path_with_constraints.keys())[0]
        constraints = IDS_path_with_constraints[full_IDS_path]
        full_IDS_path = strip_path_indexing(full_IDS_path)

    # Next, check presence and collect corresponding path
    corresponding_path = None
    for path in paths_list:
        if isinstance(path, str):
            path_string = strip_path_indexing(path)
        else:
            path_string = strip_path_indexing(tuple(path.keys())[0])

        if path_string == full_IDS_path:
            corresponding_path = path
            break

    if corresponding_path is None:
        return False

    # Collect constraints of corresponding path in path_list
    corresponding_constraints = {}
    if isinstance(corresponding_path, dict):
        corresponding_path_string = strip_path_indexing(
            tuple(corresponding_path.keys())[0]
        )
        corresponding_constraints = corresponding_path[corresponding_path_string]

    # Compare constraints
    if not set(constraints.keys()).issubset(corresponding_constraints.keys()):
        # IDS_path_with_constraints has more constraints than corresponding_path
        return False

    if "allowed_values" in constraints and not set(
        constraints["allowed_values"]
    ).issubset(set(corresponding_constraints["allowed_values"])):
        # List of allowed values under IDS_path_with_constraints is not contained in
        # list of allowed values under the corresponding_path
        return False

    # TODO: check for value_range

    if (
        "has_same_shape_as" in constraints
        and constraints["has_same_shape_as"]
        != corresponding_constraints["has_same_shape_as"]
    ):
        return False

    return True


def check_all_block(block: dict, present_paths_list: list[str | dict]) -> dict:
    """Checks if every entry in all-block is satisfied by interface_dict. Returns a dict
    containing the entries that are not satisfied.

    For simplicity, path indexing is ignored.
    Args:

        block: An all-block as described by the JSON Schema.
        present_path_list: A list of IDS paths as described by the subschema
                subschema_for_constraint_IDS_path in the JSON Schema.

    Returns:
        An all-block as described by the JSON Schema. Possibly empty.
    """
    # For each IDSpath, check if it is present and if its conditions are satisfied
    leftover_block = {"all": []}
    for full_IDS_path in block["all"]:
        if is_path_satisfied(full_IDS_path, present_paths_list):
            continue
        else:
            leftover_block["all"].append(full_IDS_path)

    return leftover_block


def check_all_or_none_block(block: dict, present_paths_list: list[str | dict]) -> dict:
    """Checks if either all entries in all_or_none-block are satisfied by interface_dict
    or none are. In case all entries or no entries are satisfied an empty dict is
    returned. Otherwise the entire block is returned.

    For simplicity, path indexing is ignored.
    Args:

        block: An all_or_none-block as described by the JSON Schema.
        present_path_list: A list of IDS paths as described by the subschema
            subschema_for_constraint_IDS_path in the JSON Schema.

    Returns:
        Either an empty dict or the input dict 'block'.
    """
    # Check if either every path is satisfied or non is
    path_satisfied = [
        is_path_satisfied(full_IDS_path, present_paths_list)
        for full_IDS_path in block["all_or_none"]
    ]
    if all(path_satisfied) != any(path_satisfied):
        return block
    else:
        return {}


def check_any_block(block: dict, present_paths_list: list[str | dict]) -> dict:
    """Checks if some entry in the any-block is satisfied by interface_dict. If so, an
    empty dict is returned. Otherwise the entire block is returned.

    For simplicity, path indexing is ignored.
    Args:

        block: An any-block as described by the JSON Schema.
        present_path_list: A list of IDS paths as described by the subschema
            subschema_for_constraint_IDS_path in the JSON Schema.

    Returns:
        Either an empty dict or the input dict 'block'.
    """
    # Check each entry in any-block and terminate loop if one is satisfied.
    some_entry_satisfied = False
    for entry in block["any"]:
        if isinstance(entry, dict) and "all" in entry:
            if not check_all_block(entry, present_paths_list):
                some_entry_satisfied = True
                break
            else:
                continue

        if is_path_satisfied(entry, present_paths_list):
            some_entry_satisfied = True
            break

    if some_entry_satisfied:
        return {}
    else:
        return block


def compute_difference(
    interface_1: Path,
    interface_2: Path,
    output_path: Path | None,
    ignore_optional_paths: bool,
) -> int:
    """Checks which criteria in interface_1 are not satisfied by interface_2 and prints
    a leftover interface of interface_1 of all the unsatisfied criteria. This result is
    saved in output_path if this path is provided.

    For simplicity, path indexing is ignored.

    Args:
        interface_1: absolute or relative path to a YAML file.
        interface_2: absolute or relative path to a YAML file.
        output_path: absolute or relative path to store the result in.
        ignore_optional_paths: If True, also consider all the optional paths in
            interface_2. Otherwise only consider the IDS paths under the key 'all'
            directly under 'paths'.

    Returns:
        integer representing exit code, where 0 is success and 1 is fail.
    """
    # Load schema
    schema_dict = get_schema_dict()

    # Load interface definition.
    interface_dict_1 = load_interface_dict(interface_1)
    interface_dict_2 = load_interface_dict(interface_2)

    # Ensure interfaces validate against schema
    if validate_definitions_dict(interface_dict_1, schema_dict, True, False) != 0:
        logger.warning(
            f"The first interface '{interface_1}' does not validate against schema."
        )
        return 1
    if validate_definitions_dict(interface_dict_2, schema_dict, True, False) != 0:
        logger.warning(
            f"The second interface '{interface_2}' does not validate against schema."
        )
        return 1

    # Gather every (mandatory) IDS paths from interface_dict_2
    present_paths_list = get_paths_list(interface_dict_2, ignore_optional_paths)

    logger.warning("Computing difference of interfaces...")

    leftover_interface = interface_dict_1.copy()
    leftover_interface["paths"] = []

    for block in interface_dict_1["paths"]:
        # Retrieve leftover block containing criteria that are not satisfied by
        # interface_2
        if "all" in block:
            leftover_block = check_all_block(block, present_paths_list)
        elif "all_or_none" in block:
            leftover_block = check_all_or_none_block(block, present_paths_list)
        else:
            leftover_block = check_any_block(block, present_paths_list)

        # Add block to leftover_interface if it is non-empty
        if leftover_block:
            leftover_interface["paths"].append(leftover_block)

    # Convert dictionary to string
    yaml_output = yaml.safe_dump(
        leftover_interface, sort_keys=False, default_flow_style=False
    )

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml_output, encoding="utf-8")
        logger.warning(f"Written to file {output_path.name}")
    else:
        print(yaml_output)

    return 0


# if __name__ == "__main__":

#     from utilities import (
#         strip_path_indexing,
#         get_schema_dict,
#         load_interface_dict,
#         SPACING_2,
#     )

#     from validate_definitions import validate_definitions_dict

#     abc1 = Path(
#         "/home/alan/projects/imas-standard-interfaces/interfaceTools/test_example_efit++IMAS_input_1.yaml"
#     )
#     abc2 = Path(
#         "/home/alan/projects/imas-standard-interfaces/interfaceTools/test_example_efit++IMAS_input_2.yaml"
#     )

#     output = Path(
#         "/home/alan/projects/imas-standard-interfaces/interfaceTools/out.yaml"
#     )

#     compute_difference(abc1, abc2, output, False)
