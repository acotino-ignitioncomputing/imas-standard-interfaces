import subprocess
from pathlib import Path

from tools.constants import REPOSITORY_PATH, SCHEMA_PATH, EXAMPLE_DEFINITIONS_FOLDER

COMMIT_MESSAGE = "Github Actions: updated schema and definitions with new DOI URL"


def check_return_code(return_code: int, message: str):
    if return_code != 0:
        raise Exception("\n\t" + message)


def commit_schema_to_git():
    """Check if both the JSON schema and all the example interface definitions are
    changed, then commit these files and push them onto the current branch.
    """

    # Check if username is configured in git

    process = subprocess.run(["git", "config", "user.name"], capture_output=True)

    if process.stdout == b"":
        raise Exception(
            "No username has been set. Ensure\n\t"
            + "git config user.name\n"
            + "is run correctly"
        )

    # Check if schema and definitions are updated

    file_path_list = [
        file_path for file_path in EXAMPLE_DEFINITIONS_FOLDER.glob("**/*.yaml")
    ]
    file_path_list += [SCHEMA_PATH]

    process = subprocess.run(["git", "diff", "--name-only"], capture_output=True)
    updated_files = process.stdout.decode().strip("\n").split("\n")
    updated_files_paths = [
        REPOSITORY_PATH / Path(file_path) for file_path in updated_files
    ]

    for file_path in file_path_list:
        if file_path not in updated_files_paths:
            raise Exception(
                "Cannot commit schema and example definitions since the following"
                + f" file was not updated: \n\t{file_path}"
            )

    # Stage and commit updated schema & definitions
    process = subprocess.run(
        ["git", "add", SCHEMA_PATH, EXAMPLE_DEFINITIONS_FOLDER], capture_output=True
    )

    check_return_code(
        process.returncode,
        "Something went wrong with staging schema and example definitions:\n\t"
        + process.stderr.decode(),
    )

    process = subprocess.run(
        ["git", "commit", "-m", COMMIT_MESSAGE], capture_output=True
    )

    check_return_code(
        process.returncode,
        "Something went wrong with commiting schema and example definitions:\n\t"
        + process.stderr.decode(),
    )

    # Push commit to current branch
    process = subprocess.run(["git", "push"], capture_output=True)

    check_return_code(
        process.returncode,
        "Something went wrong with pushing the schema and example definitions:\n\t"
        + process.stderr.decode(),
    )
