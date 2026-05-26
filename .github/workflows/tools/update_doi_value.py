import json

from tools.constants import SCHEMA_PATH, SCHEMA_VERSION_KEY, EXAMPLE_DEFINITIONS_FOLDER


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
    schema_dict = json.loads(SCHEMA_PATH.read_text())

    schema_dict["properties"][SCHEMA_VERSION_KEY]["const"] = new_doi

    SCHEMA_PATH.write_text(json.dumps(schema_dict, indent=4))

    # Next, update each YAML file in folder example_definitions
    for yaml_file_path in EXAMPLE_DEFINITIONS_FOLDER.glob("**/*.yaml"):
        with open(yaml_file_path, "r") as yaml_file:
            # Only edit line with key 'schema_version' to preserve newlines & spacing
            lines = yaml_file.readlines()

        updated_lines = [
            (
                f"{SCHEMA_VERSION_KEY}: {new_doi}\n"
                if SCHEMA_VERSION_KEY in line
                else line
            )
            for line in lines
        ]

        with open(yaml_file_path, "w") as yaml_file:
            yaml_file.writelines(updated_lines)


if __name__ == "__main__":
    from tools.constants import CITATION_PATH

    citation_dict = json.loads(CITATION_PATH.read_text())
    new_doi = citation_dict["doi"]

    update_doi_value(new_doi)
