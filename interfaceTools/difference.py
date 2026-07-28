from pathlib import Path
import click
import yaml

from validate_definitions import validate_definitions_dict


def difference(path_interface_A: Path, path_interface_B: Path):

    # Load interface paths
    with click.open_file(path_interface_A) as file:
        interface_A_dict = yaml.safe_load(file)

    with click.open_file(path_interface_B) as file:
        interface_B_dict = yaml.safe_load(file)

    # Ensure interfaces validate against schema
    if validate_definitions_dict(interface_A_dict, silent=True) != 0:
        raise Exception(
            f"Interface '{path_interface_A}' does not validate against schema."
        )

    if validate_definitions_dict(interface_B_dict, silent=True) != 0:
        raise Exception(
            f"Interface '{path_interface_B}' does not validate against schema."
        )

    # Get all mandatory paths from interface A (along with allowed values)
    mandatory_path_list_A = [
        entry
        for entry in interface_A_dict["paths"]
        if "all_or_none" not in entry and "any_of" not in entry
    ]

    # Copy interface B and set 'paths' to empty list
    leftover_interface_dict = interface_B_dict.copy()
    leftover_interface_dict["paths"] = []

    # Loop through entries of interface B and add to leftover_interface if they are
    #   missing in interface A
    for entry in interface_B_dict["paths"]:
        if isinstance(entry, str) and entry not in mandatory_path_list_A:
            # An IDS path
            leftover_interface_dict["paths"].append(entry)
            continue

        if isinstance(entry, dict) and (
            "all_or_none" not in entry and "any_of" not in entry
        ):
            # An IDS path with allowed_values criterium.
            if not check_allowed_values(entry, mandatory_path_list_A):
                leftover_interface_dict["paths"].append(entry)
                continue

        if isinstance(entry, dict) and "all_or_none" in entry:
            # An all_or_none block

            paths_to_check = entry["all_or_none"]

            path_is_present = []

            for path in paths_to_check:
                if isinstance(path, str):
                    # Check for matches in strings and dictionary keys
                    matches = [
                        path_in_A
                        for path_in_A in mandatory_path_list_A
                        if path in path_in_A
                    ]
                    path_is_present(len(matches) > 0)

                if isinstance(path, dict):
                    path_is_present(check_allowed_values(path, mandatory_path_list_A))

            # Check if not all paths were absent or present
            if all(path_is_present) != any(path_is_present):
                leftover_interface_dict["paths"].append(entry)
                continue

        if isinstance(entry, dict) and "any_of" in entry:
            # An any_of-block.

            # Check if one path or all_of-block is included in mandatory_path_list_A
            any_of_block = entry["any_of"]

            for any_of_entry in any_of_block:
                if (
                    isinstance(any_of_entry, str)
                    and any_of_entry in mandatory_path_list_A
                ):
                    # Path string
                    break
                if (
                    isinstance(any_of_entry, dict)
                    and "all_of" not in any_of_entry
                    and check_allowed_values(any_of_entry, mandatory_path_list_A)
                ):
                    # Allowed values criterium
                    break
                if isinstance(any_of_entry, dict) and "all_of" in path:
                    all_of_block = any_of_entry["all_of"]
                    all_present = True
                    for path in all_of_block:
                        if path not in mandatory_path_list_A:
                            all_present = False
                            break

                    if all_present:
                        break

            # All check failed for any_of-block
            leftover_interface_dict["paths"].append(entry)

    # Output leftover interface file
    click.echo(yaml.safe_dump(leftover_interface_dict))


def check_allowed_values(ids_path_dict, mandatory_path_list) -> bool:
    # Check if allowed values criterium in ids_path_dict is satisfied in mandatory list

    # Get IDS path and list of allowed values
    IDS_path = list(ids_path_dict.keys())[0]
    allowed_values = list(ids_path_dict.values())[0]["allowed_values"]

    # Check if IDS_path is in mandatory_path_list without allowed_values criterium
    if IDS_path in mandatory_path_list:
        return True

    # If IDS_path has allowed_values criterium in mandatory_path_list, compare values
    paths_with_allowed_values = [
        path_dict for path_dict in mandatory_path_list if IDS_path in path_dict
    ]
    if paths_with_allowed_values:
        # Assume len(paths_with_allowed_values)==1, else there are illegal duplicates
        other_allowed_values = list(paths_with_allowed_values[0].values())[0][
            "allowed_values"
        ]
        if set(other_allowed_values).issubset(set(allowed_values)):
            return True

    return False


@click.command()
@click.argument("path_interface_a", type=click.Path(exists=True, path_type=Path))
@click.argument("path_interface_b", type=click.Path(exists=True, path_type=Path))
def main(path_interface_a: Path, path_interface_b: Path):
    difference(path_interface_a, path_interface_b)


if __name__ == "__main__":
    main()
