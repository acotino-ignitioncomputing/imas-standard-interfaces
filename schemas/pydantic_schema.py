"""Pydantic v2 model for IMAS interface definition YAML files."""

from pydantic import BaseModel, ConfigDict, model_validator
from imas import IDSFactory, util
import re


class PathConstraints(BaseModel):
    """Constraints on the data array of an IDS path."""

    allowed_values: list[int | str]


class InterfaceDefinition(BaseModel):
    """Top-level model for an IMAS interface definition YAML file."""

    dd_version: str | None = None
    include: list[str] = []
    ids: dict[str, list[str | dict[str, PathConstraints]]] = {}

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_non_empty_definition(self):
        """Enforce that at least one IDS or one include-path is provided

        Raises:
            ValueError

        Returns:
            self
        """
        if self.include is None and self.ids is None:
            raise ValueError("At least one IDS or include-path must be provided")
        return self

    @model_validator(mode="after")
    def check_length_dictionaries(self):
        """Dictionaries on a list entry must be of length 1.

        Raises:
            ValueError

        Returns:
            self
        """
        for _, path_list in self.ids.items():
            for path in path_list:
                if isinstance(path, dict) and len(path) != 1:
                    raise ValueError(
                        "The following paths must be on a single list entry (prepend '-'):"
                        + "\n\t"
                        + "\n\t".join(path.keys())
                        + "\n\t"
                    )
        return self

    @model_validator(mode="after")
    def check_ids_name(self):
        """Only allow IDS names that are in the Data Dictionary

        Raises:
            ValueError

        Returns:
            self
        """
        ids_names_list = IDSFactory(self.dd_version).ids_names()

        for ids_name in self.ids.keys():
            if ids_name not in ids_names_list:
                message = f"IDS name '{ids_name}' is not in Data Dictionary"
                message += (
                    f" version {self.dd_version}"
                    if self.dd_version is not None
                    else " (version not provided)"
                )
                raise ValueError(message)
        return self

    @model_validator(mode="after")
    def check_ids_paths_in_dd(self):
        """Each IDS path must be present in the provided version of Data Dictionary.
        If no version is supplied, the latest version is used.

        Raises:
            ValueError

        Returns:
            self
        """

        for ids_name in self.ids:
            # Create empty IDS to extract valid paths from
            ids_instance = IDSFactory(self.dd_version).new(ids_name)

            # Convert paths to IMAS NetCDF convention
            """ 
            valid_paths_list = [
                path.replace("/", ".") for path in util.find_paths(ids_instance, "")
            ]
            """
            valid_paths_list = util.find_paths(ids_instance, "")

            for ids_path in self.ids[ids_name]:
                ids_path_string = (
                    list(ids_path)[0] if isinstance(ids_path, dict) else ids_path
                )
                # Remove index-notation (if present)
                ids_path_string = re.sub(r"\(.{1,6}\)", "", ids_path_string)

                if ids_path_string not in valid_paths_list:
                    raise ValueError(
                        f"Path {ids_path_string} is not in IDS {ids_name} for "
                        + f"Data Dictionary version {self.dd_version}"
                    )

        return self


if __name__ == "__main__":
    import yaml
    from pathlib import Path

    folder = Path(__file__).parents[1] / "definitions" / "efit++"

    for file_path in sorted(folder.glob("*.yaml")):
        print(f"\nValidating {file_path.name}...")
        with open(file_path) as f:
            data = yaml.safe_load(f)
        try:
            InterfaceDefinition.model_validate(data)
            print("  SUCCESS")
        except Exception as e:
            print(f"  FAILED: {e}")
