# Standard Interfaces

This repository provides standardized schemas and interfaces for scientific data
formats.

## Repository structure

``` doctree
standard_interfaces/
├── definitions/
│   ├── efit++/
│   └── non-iron-core tokamak/
└── examples/
```

The folder `definitions` contains interface definitions, both modular and
tokamak specific. See `definitions/structure_of_definitions.md` for a
description of these definitions.

The folder `exmaples` contains CDL-files describing netCDF datasets containing
dummy data of the IDS `pf_passive`. These datasets are meant to further clarify
the interpretation of the interface definitions in the folder `definitions`. See
`examples/example.md` for a brief instruction on how to generate netCDF datasets
from these CDL-files
