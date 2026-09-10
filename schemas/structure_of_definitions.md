# Structure of interface definitions

This document outlines the structure of interface definitions that describe
input and output datasets for simulation code using IMAS. These definitions are
written in YAML and use references to the IDS's in the IMAS Data Dictionary.
The structure of these definitions is formally described in the JSON Schema
`schemas/json_schema.yaml`.

Each YAML file must contain the following nine top level mapping keys:

- `code_name`
- `executable_name`
- `url`
- `code_version`
- `interface_source_files`
- `schema_version`
- `dd_version_interface`
- [`paths`](#paths)

The string-value of the key `code-name` holds the name of the simulation code
base.

The string-value of the key `executable_name` holds the filename of the
executable that is targeted by the interface definition in question.

The string-value of the key `url` holds an URL to the repository of the
simulation code.

The string-value of the key `code_version` holds any string that indicates the
version of the simulation code. This may be a version string, a commit hash or
both.

The sequence `interface_source_files` contains a list of file paths that contain
the information captured in the interface definition.

The string-value of the key `schema_version` holds the version of the JSON
Schema that the interface definition follows. The format is in MAJOR.PATCH,
where the number MAJOR must coincide with the first number in the property
"version" of `schemas/json_schema.yaml`. The number PATCH may be arbitrary. The
JSON Schema checks the value of the `schema_version` key via pattern matching.

The key `dd_version_interface` holds a list of versions of the IMAS Data
Dictionary that the definition targets (e.g. `4.1.0`).

The key [`paths`](#paths) contains (sets of) IDS paths that must be present in
the dataset and whose data array must be non-empty. If an IDS path has child
paths then it is implied that each child path must be present and have non-empty
data array.

Each string representing an IDS path of a certain IDS is build-up by appending
the IDS name with the IDS path. The IDS paths follow the [IMAS IDS path
convention](https://imas-data-dictionary.readthedocs.io/en/latest/IDS-path-syntax.html),
where the forward slashes `/` seperate nested structures and path indexing
inside round brackets indicate specific elements of array of structures or
specific entries in the data array

For example

```yaml
- pf_active/coil/resistance
- pf_passive/loop/element/geometry/geometry_type 
- pulse_schedule/density_control/ion/element(3:7)/z_n
```

In order to increase readability of the interface definitions, it is recommended
to sort any sequence of IDS paths in alphabetical order, to only write down a
parent path if all child paths are present and to write lists of integers as
much as possible in 'YAML flow style' (see [example 2](#example-2)).

Lastly, the top level key `notes` may be present, which contains a sequence of
strings. This may be used to provide extra information about the interface that
cannot be captured by the interface format.

For more example interface definitions, see the YAML files in the subfolders
of the folder `interfaces`.

## Paths

The mapping key `paths` maps to a sequence of mappings consisting of exactly one
of the following keys:

- `all`: maps to a sequence of IDS paths that must be present in the dataset.
- `all_or_none`: maps to a sequence of IDS paths of which either all paths must
be present in the dataset or all must be absent.
- `any`: indicates that at least one of the listed (sets of) IDS paths must be
present. It maps to a sequence of IDS apths (for a single IDS path), a sequence
of mapping keys `all` (for a set of IDS paths) or a sequence consisting of a
combination of the two. See [example 1](#example-1).

The following additional requirements are imposed to prevent different
descriptions of the same requirements on the input / output dataset:

- The sequence under `all_or_none` and `any` must have 2 or more entries.
- Under `any`, every occurence of `all` must map to a sequence of 2 or
  more entries.
- Directly under `paths` there can be at most one key `all`.
- Any sequence of IDS paths under each occurence of `any`, `all_or_none` and
  `all` must not have duplicate IDS paths.
- No IDS path listed under the key `all` under `path` may appear elsewhere in
  the interface definition.

### Example 1

```yaml
code_name: EFIT
executable_name: efit++IMAS.exe
url: https://git.iter.org/projects/EQ/repos/efitpp/browse
code_version: a6506130d15ed5831ec8894b4890a5e37b5e1022
interface_source_files:
- "src/imas.cpp"

schema_version: "0.1"
dd_version_interface: 3.41.0

notes: 
- This is just an example and NOT an actual description of an interface 

paths:
-all:
  - equilibrium/time
  - equilibrium/time_slice/global_quantities/ip
  - equilibrium/vacuum_toroidal_field/b0
  - magnetics/flux_loop(1:4)/position/r

- all_or_none:
  - iron_core/ids_properties/version_put/data_dictionary
  - iron_core/segment/b_field
  - iron_core/segment/geometry/outline
  - iron_core/segment/permeability_relative

- any_of:
  - all_of:
    - wall/description_2d/vessel/unit/annular/centreline/r
    - wall/description_2d/vessel/unit/annular/centreline/z
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

## Constraints on IDS paths

Contraints can be imposed on the data arrays of the IDS paths by writing the
IDS path as a mapping containing at least one of the following keys

- `allowed_values`: maps to a sequence of values (integer, float or string) that
  are allowed to be present in the data array of the IDS path. When specified,
  the data array must only consist of the listed values.
- `same_shape_as`: maps to a string representing an IDS path whose data array
  must have the same shape as the data array of the IDS path in question.
  Although it is implied that the IDS path of this key must be present in the
  dataset, it is still recommended to explicitly include this IDS path somewhere
  in the interface definition.
- `value_range`: maps to a string representing an interval indicating a range of
  values that are allowed to be present in the data array of the IDS path.
  Infinity is indicated with `inf`, an open end of an interval with `(` or `)`
  and a closed end with `[` or `]` .

### Example 2

```yaml
code_name: EFIT
executable_name: efit++IMAS.exe
url: https://git.iter.org/projects/EQ/repos/efitpp/browse
code_version: a6506130d15ed5831ec8894b4890a5e37b5e1022
interface_source_files:
- "src/imas.cpp"

schema_version: "0.1"
dd_version_interface: 3.41.0

notes: 
- This is just an example and NOT an actual description of an interface 

paths:
- all:
  - equilibrium/time_slice(1)/global_quantities/ip:
      value_range: "(-inf, 1000000000.0]"
  - magnetics/flux_loop/position/z
  - magnetics/ids_properties/homogeneous_time:
      allowed_values: [0,1]
  - magnetics/ip/data
  - pf_active/circuit/connections
  - pf_active/circuit/current/data
  - pf_active/coil/element/geometry/geometry_type:
      allowed_values: [2, 3, 5, 6]
  - pulse_schedule/ic/power/reference/data
  - pulse_schedule/ec/power/reference/data:
      same_shape_as: pulse_schedule/ic/power/reference/data
```
