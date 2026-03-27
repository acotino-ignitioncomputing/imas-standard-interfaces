from pydantic import BaseModel, ConfigDict, model_validator, ValidationError
from typing import Dict, Optional

# Define type hint for required IDS paths and the constraints on them  
type IDS_PATH = Dict[str, Optional[IDS_PATH | list[int]]]


class InterfaceDefinition(BaseModel):
    # Version of IMAS Data Dictionary to target
    dd_version: Optional[str] = None

    # List of paths of other interface definitions to include
    include: Optional[list[str]] = None

    # Allowed IDS
    equilibrium: Optional[IDS_PATH] = None
    iron_core: Optional[IDS_PATH] = None
    magnetics: Optional[IDS_PATH] = None
    pf_active: Optional[IDS_PATH] = None
    pf_passive: Optional[IDS_PATH] = None
    tf: Optional[IDS_PATH] = None
    wall: Optional[IDS_PATH] = None

    # No other fields are permitted
    model_config = ConfigDict(extra="forbid")

    # Enforce that at least one IDS or one include-path is provided 
    @model_validator(mode="after")
    def check_non_empty_definition(self):
        for key, value in self.__dict__.items():
            if key != "dd_version" and value is not None:
                return
        
        raise ValueError("At least one IDS or include-path must be provided" )



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
