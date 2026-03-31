"""Pydantic v2 model for IMAS interface definition YAML files."""

from pydantic import BaseModel, ConfigDict, model_validator
from imas import IDSFactory


class PathConstraints(BaseModel):
    """Constraints on the data array of an IDS path."""

    allowed_values: list[int | str]


class IDSPath(BaseModel):
    """Definition of required paths for a single IDS."""

    required: list[str | dict[str, PathConstraints]]
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def check_length_dictionaries(self):
        """Dictionaries must have length 1

        Raises:
            ValueError

        Returns:
            self
        """

        for path in self.required:
            if isinstance(path, dict) and len(path) != 1:
                raise ValueError(
                    "The following paths must be on a single list entry (prepend '-'):"
                    + "\n\t".join(path.keys())
                )


class InterfaceDefinition(BaseModel):
    """Top-level model for an IMAS interface definition YAML file."""

    dd_version: str | None = None
    include: list[str] = []
    ids: dict[str, IDSPath] = {}

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
