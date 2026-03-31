from pydantic import BaseModel, ConfigDict, model_validator, TypeAdapter, ValidationError
from imas import IDSFactory

# Define type hint for required IDS paths and the constraints on them  
type IDS_PATH = dict[str, IDS_PATH | list[int | str] | None]


class InterfaceDefinition(BaseModel):
    # Version of IMAS Data Dictionary to target
    dd_version: str | None = None

    # List of paths of other interface definitions to include
    include: list[str] = []

    # IDS's are stored in self.__pydantic_extra__. Their type is checked afterwards
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def check_non_empty_definition(self):
        """Enforce that at least one IDS or one include-path is provided 

        Raises:
            ValueError

        Returns:
            self
        """
        if self.include is not None or self.__pydantic_extra__:
            return self
        
        raise ValueError("At least one IDS or include-path must be provided" ) 
    
    
    @model_validator(mode="after")
    def check_ids_name(self):
        """Only allow IDS names that are in the Data Dictionary

        Raises:
            ValueError

        Returns:
            self
        """
        ids_names_list = IDSFactory(self.dd_version).ids_names()

        for key in self.__dict__.keys():
            if key != "dd_version" and key != "include" and key not in ids_names_list:
                message = f"IDS name '{key}' is not in Data Dictionary"
                message += (
                    f" version {self.dd_version}"
                    if self.dd_version is not None
                    else " (version not provided)"
                )
                raise ValueError(message)
        return self
    
    # 
    @model_validator(mode="after")
    def check_ids_type(self):
        """Check type hint of provided IDS

        Raises:
            ValueError

        Returns:
            self
        """
        adapter =  TypeAdapter(IDS_PATH)
        for key, value in self.__pydantic_extra__.items():
            try:
               adapter.validate_python(value)
            except Exception:
                raise ValueError(
                    f"Format of IDS '{key}' does not comply with standard"
                    )
        return self


if __name__ == "__main__":
    # Validate interface definitions in folder 'definitions/efit++' against Pydantic
    # model InterfaceDefinition
    
    import yaml
    from pathlib import Path

    folder = Path(__file__).parents[1] / Path("definitions/efit++")

    for file_path in folder.glob("*"):
        print("\nCheck " + file_path.name)

        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        try:
            magn = InterfaceDefinition.model_validate(data)
            print("\tSUCCESS")
        except ValidationError as err:
            print("\tVALIDATION FAILED")
            print(err)
        except Exception as e:
            print("\tVALIDATION FAILED")
            print(e)

