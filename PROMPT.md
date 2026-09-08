Consider the YAML files in the subfolder of the folder 'interfaces', which
follow the format described in the JSON Schema 'schemas/json_schema.json' and
the markdown file 'schemas/structure_of_definitions.md'.

Create a similar YAML file for each IMAS-related executable inside the
repository PATH_TO_REPO of the the simulation code NAME_OF_CODE. Create a
seperate YAML file for the input IDS paths and the output IDS paths. Place these
YAML files in the top of the repository of this simulation code.

Verify the syntax of the YAML files using the python script
'interfaceTools/validate_definitions.py' and solve any issues with the YAML
file.
