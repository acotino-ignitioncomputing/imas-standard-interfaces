# Standard Interfaces

This repository provides standardized schemas and interfaces for scientific data
formats used in IMAS (Integrated Modelling & Analysis Suite). Interface
definitions are written in YAML and reference IDS's in the IMAS Data Dictionary.

## Repository structure

```text
standard_interfaces/
├── example_definitions/
│   ├── Data_Dictionary_v_3.39.0/
│   │   ├── CHEASE/
│   │   └── DINA/
│   ├── Data_Dictionary_v_3.42.0/
│   │   ├── HELENA/
│   │   └── efit++/
│   ├── Data_Dictionary_v_4.0.0/
│   │   ├── LIGKA/
│   │   ├── NICE/
│   │   └── torax/
├── example_datasets/
│   ├── example.md
│   ├── valid_pf_passive.cdl
│   ├── invalid_1_pf_passive.cdl
│   └── invalid_2_pf_passive.cdl
├── schemas/
│   ├── json_schema.json
│   ├── validate_definitions.py
│   └── structure_of_definitions.md
```

### `example_definitions/`

Example interface definitions organised by Data Dictionary version and
simulation code. Each code folder contains YAML files describing the input
and/or output interfaces of that code.

### `example_datasets/`

CDL files describing netCDF datasets containing dummy data for the IDS
`pf_passive`. These datasets illustrate how to interpret the interface
definitions. See `example_datasets/example.md` for instructions on generating
netCDF datasets from these CDL files.

### `schemas/`

Schemas and tooling for validating interface definitions:

- `json_schema.json` — JSON Schema describing the structure of interface
  definitions.
- `validate_definitions.py` — Python script for validating definitions against
  the schema and the IMAS Data Dictionary.
- `structure_of_definitions.md` for a description of the definition format in plain text.
