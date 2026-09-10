# Standard Interfaces

This repository provides standardized schemas and interfaces for scientific data
formats used in IMAS (Integrated Modelling & Analysis Suite). Interface
definitions are written in YAML and reference IDS's in the IMAS Data Dictionary.

## Repository structure

```text
standard_interfaces/
├── interfaces/
├── example_datasets/
├── schemas/
│   ├── json_schema.json
│   └── structure_of_definitions.md
├── interfaceTools/
└── pyproject.toml
```

### `interfaces/`

Interface definitions organised by simulation code. Each code folder contains
`input_interfaces/` and/or `output_interfaces/` subdirectories with YAML files
describing the interfaces of that code against a specific Data Dictionary
version.

### `example_datasets/`

CDL files describing netCDF datasets containing dummy data for the EFIT++ input
interface. These datasets illustrate how to interpret the interface definitions.
See `example_datasets/example.md` for instructions on generating netCDF datasets
from the CDL files.

### `schemas/`

Schemas for validating interface definitions:

- `json_schema.json` — JSON Schema describing the structure of interface
  definitions.
- `structure_of_definitions.md` — description of the definition format in plain
  text.

### `interfaceTools/`

Python package providing the `imas-interfaces` CLI and supporting modules:

- `cli.py` — Click-based command line interface (entry point: `imas-interfaces`).
- `validate_definitions.py` — validates YAML definitions against the JSON Schema
  and the IMAS Data Dictionary.
- `check_dataset.py` — checks whether an IMAS dataset complies with a given
  interface definition.
- `compute_difference.py` - computes difference of two interfaces.
- `translate_definition.py` - translares an interface definition to a differnt
  version of the Data Dictionary.
- `utilities.py` — shared helper functions.

## Installation

Requires Python >= 3.10. Install with [uv](https://docs.astral.sh/uv/) or pip:

```bash
uv sync          # using uv (recommended)
pip install .    # or using pip
```

## Usage of tools

### Validate interface definitions

```bash
# Validate a single YAML file
imas-interfaces validate interfaces/NICE/input_interfaces/input_nice_imas_inv_dd_4.0.0.yaml

# Validate all YAML files in a directory
imas-interfaces validate interfaces/

# Read from stdin
cat definition.yaml | imas-interfaces validate
```

Use `--show_suggestions` to get suggestions for incorrect IDS paths (much slower!).

### Check a dataset against an interface

```bash
# Check a netCDF dataset against an interface definition
imas-interfaces check_dataset dataset.nc interface.yaml

# Check a HDF5 dataset
imas-interfaces check_dataset imas:hdf5?path=dataset interface.yaml

# Read the interface from stdin
cat interface.yaml | imas-interfaces check_dataset dataset.nc
```

### Convert an interface to a different Data Dictionary version

```bash
# Convert to Data Dictionary version 4.0.0
imas-interfaces convert interface.yaml 4.0.0

# Save output to file
imas-interfaces convert -o output.yaml interface.yaml 4.0.0
```

### Compare two interfaces and obtain a leftover interface

```bash
# Compare an output interface with an input interface
imas-interfaces difference output_nice_inv.yaml input_torax.yaml

# Check whether a source dataset is suited for a chain of simulation codes
imas-interfaces difference output_nice_inv.yaml input_torax.yaml | \
imas-interfaces imas-interfaces check_dataset imas:hdf5?path=dataset
```

## Creating interfaces

The tool `imas-interface validate` with the flag `--show_suggestions` can be
usefull when creating interfaces manually.

The prompt in `PROMPT.md` can be used for generating interfaces via a Large
Language Model. Make sure the strings 'PATH_TO_REPO' and 'NAME_OF_CODE' are
replaced with the proper values.
