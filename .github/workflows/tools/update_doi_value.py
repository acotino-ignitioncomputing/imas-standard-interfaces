import json

from constants import SCHEMA_PATH, SCHEMA_VERSION_KEY, EXAMPLE_DEFINITIONS_FOLDER


def update_doi_value(new_doi: str):
    """Update the 'const'-value of key SCHEMA_VERSION_KEY in the JSON Schema along with
    the string-value of SCHEMA_VERSION_KEY in each YAML-file in
    EXAMPLE_DEFINITIONS_FOLDER to the 'new_doi'.

    Args:
        new_doi: string value of the new DOI URL. The value of key SCHEMA_VERSION_KEY
            will be updated to this value.
    """

    # TODO: Add proper error handling

    # First, update schema
    with open(SCHEMA_PATH, "r") as schema_file:
        schema_dict = json.load(schema_file)

    schema_dict["properties"][SCHEMA_VERSION_KEY]["const"] = new_doi

    with open(SCHEMA_PATH, "w") as schema_file:
        schema_file = json.dump(schema_dict, schema_file, indent=4)

    # Next, update each YAML file in folder example_definitions
    for yaml_file_path in sorted(EXAMPLE_DEFINITIONS_FOLDER.glob("**/*.yaml")):
        with open(yaml_file_path, "r") as yaml_file:
            # Only edit line with key 'schema_version' to preserve newlines & spacing
            lines = yaml_file.readlines()

        updated_lines = [
            (f"{SCHEMA_VERSION_KEY}: {new_doi}" if SCHEMA_VERSION_KEY in line else line)
            for line in lines
        ]

        with open(yaml_file_path, "w") as yaml_file:
            yaml_file.writelines(updated_lines)
