"""Pydantic v2 model for IMAS interface definition YAML files."""

from pydantic import BaseModel, ConfigDict, model_validator


class PathConstraints(BaseModel):
    """Constraints on the data array of an IDS path."""

    allowed_values: list[int]


class IDSPath(BaseModel):
    """Definition of required paths for a single IDS."""

    required: list[str | dict[str, PathConstraints]]
    model_config = ConfigDict(extra="forbid")


class InterfaceDefinition(BaseModel):
    """Top-level model for an IMAS interface definition YAML file."""

    dd_version: str | None = None
    include: list[str] | None = None
    ids: dict[str, IDSPath] | None = None

    model_config = ConfigDict(extra="forbid")

    # Enforce that at least one IDS or one include-path is provided
    @model_validator(mode="after")
    def check_non_empty_definition(self):
        if self.include is None and self.ids is None:
            raise ValueError("At least one IDS or include-path must be provided")


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
