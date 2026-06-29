# Structure of interface definitions

This document outlines the structure of interface definitions that describe
input and output datasets for simulation code using IMAS. These definitions are
written in YAML and use references to the IDS's in the IMAS Data Dictionary.
The structure of these definitions is formally described in the JSON Schema
`schemas/json_schema.yaml`.

In each file at least the following three top level mapping keys must be
present:

- `schema_version`
- `dd_version`
- [`paths`](#paths)

The string-value of the key `schema_version` must be equal to the DOI URL of the
schema.

The key `dd_version` holds a list of versions of the IMAS Data Dictionary that
the definition targets (e.g. `4.1.0`).

The key [`paths`](#paths) contains (sets of) IDS paths that must be present in
the dataset and whose data array must be non-empty. If an IDS path has child
paths then it is implied that each child path must be present and have non-empty
data array.

Optionally, a [`constraint`](#constraints) key may be present at the top level,
specifying any constraints on the data arrays at the specified IDS paths.

Each string representing an IDS path of a certain IDS is build-up by appending
the IDS name with the IDS path.
The IDS paths follow the [IMAS IDS path
convention](https://imas-data-dictionary.readthedocs.io/en/latest/IDS-path-syntax.html), where the forward slashes `/` seperate nested structures.

For example

```yaml
- pf_active/coil/resistance
- pf_passive/loop/element/geometry/geometry_type 
- pulse_schedule/density_control/ion/element/z_n
```

In order to increase readability of the interface definitions, it is recommended
to sort any sequence of IDS paths in alphabetical order and to write lists of
integers as much as possible in 'YAML flow style' (see [example 2](#example-2)).

For more example interface definitions, see the YAML files in the folder `example_definitions` of this repository.

## Paths

The mapping key `paths` maps to a sequence of IDS path and / or mappings
consisting of exactly one of the following keys:

- `all_or_none`: maps to a sequence of IDS paths of which either all paths must
be present in the dataset or all must be absent.
- `any_of`: indicates that at least one of the listed (sets of) IDS paths must
be present. It maps to a sequence of strings (for a single IDS path), a sequence
of mapping keys `all_of` (for a set of IDS paths) or a sequence consisting of a
combination of the two. See [example 1](#example-1).

The following additional requirements are imposed to prevent different
descriptions of the same input / output dataset:

- The sequence under `all_or_none` and `any_of` must have 2 or more entries.
- Under `any_of`, every occurence of `all_of` must map to a sequence of 2 or
  more entries.
- Any sequence of IDS paths, either directly under `paths` or under each occurence
  of `any_of`, `all_or_none` and `all_of`, must not have duplicate IDS paths.

### Example 1

```yaml
schema_version: placeholder_doi

dd_version: [4.0.0]

paths:
- equilibrium/time
- equilibrium/time_slice/global_quantities/ip
- equilibrium/vacuum_toroidal_field/b0

- all_or_none:
  - iron_core/ids_properties/version_put/data_dictionary
  - iron_core/segment/b_field
  - iron_core/segment/geometry/outline
  - iron_core/segment/permeability_relative

- any_of:
  - all_of:
    - wall/description_2d(/vessel/unit/annular/centreline/r
    - wall/description_2d(/vessel/unit/annular/centreline/z
    - wall/description_2d/vessel/unit/annular/thickness
  - all_of:
    - wall/description_2d/vessel/unit/annular/outline_inner/r
    - wall/description_2d/vessel/unit/annular/outline_inner/z
    - wall/description_2d/vessel/unit/annular/outline_outer/r
    - wall/description_2d/vessel/unit/annular/outline_outer/z

- any_of:
  - equilibrium/time_slice/profiles_1d/gm9
  - all_of:
    - equilibrium/time_slice/profiles_1d/r_inboard
    - equilibrium/time_slice/profiles_1d/r_outboard
```

## Constraints

Each entry in `constraints` describes which constraints are enforced on the data
array of the specified IDS path. Listing an IDS path under this key **does not**
imply that its presence is required.

Currently, only the following mapping key is allowed:

- `allowed_values`: maps to a sequence of mappings having the IDS path as key,
  which maps to a sequence of values (integer, float or string) that are allowed
  to be present in the data array at the IDS path. When specified, the data
  array must only consist of the listed values.

### Example 2

```yaml

constraints:
  allowed_values:
  - equilibrium/time_slice/profiles_2d/grid_type/index: [1]
```
