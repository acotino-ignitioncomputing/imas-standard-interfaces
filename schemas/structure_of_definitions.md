# Structure of interface definitions

This document outlines the structure of interface definitions that describe
input and output datasets for simulation code using IMAS. These definitions are
written in YAML and use references to the IDS's in the IMAS Data Dictionary.
The structure of these definitions is formally described in the JSON Schema
`schemas/json_schema.yaml`.

In each file at least the following two top level mapping keys must be
present:

- `dd_version`
- [`paths`](#paths)

The key `dd_version` specifies the version of the IMAS Data Dictionary that the
definition targets (e.g. `4.1.0`).

The key [`paths`](#paths) contains  sets of IDS paths that must be present in
the dataset.

Optionally, a [`constraint`](#constraints) key may be present at the top level,
specifying any constraints on the data arrays at the specified IDS paths.

Each string representing an IDS path of a certain IDS is build-up by appending
the IDS name with the IDS path.
The IDS paths follow the [IMAS IDS path
convention](https://imas-data-dictionary.readthedocs.io/en/latest/IDS-path-syntax.html)
with the exception of the criterium that the index specifier is mandatory for
array of structures: the forward slashes `/` seperate nested structures, and the
index and ranges of arrays can be given between round brackets `()` just after
the array name.

For example

```yaml
- pf_active/coil/resistance # all coils
- pf_passive/loop/element(1)/geometry/geometry_type # first element of each coil
- pulse_schedule/density_control/ion/element(3:7)/z_n # elements 3 until 7 
```

In order to increase readability of the interface definitions, it is recommended
to sort any sequence of IDS paths in alphabetical order (ignoring index and
ranges in round brackets) and to write lists of integers as much as possible in
'YAML flow style' (see [example 2](@example-2)).

For more example interface definitions, see the YAML files in the folder `example_definitions` of this repository.

## Paths

The mapping key `paths` maps to a sequence of mappings consisting of exactly one
of the following keys:

- `all_of`: maps to a sequence of IDS paths that must be present in the
dataset.
- `all_or_none`: maps to a sequence of IDS paths of which either all paths must
be present in the dataset or all must be absent.
- `any_of`: indicates that at least one of the listed (sets of) IDS paths must
be present. It maps to a sequence of strings (for a single IDS path), a sequence
of mapping keys `all_of` (for a set of IDS paths) or a sequence consisting of a
combination of the two. See [example 1](#example-1).

The following additional requirements are imposed to prevent different
descriptions of the same input / output dataset:

- Under `paths` there can be at most one occurence of the key `all_of`. The key
  `any_of` may hold multiple occurences of `all_of`.
- The sequence under `all_or_none` and `any_of` must have 2 or more entries.
- Under `any_of`, every occurence of `all_of` must map to a sequence of 2 or
  more entries.
- The sequence of IDS paths under each occurence of `all_of` and `all_or_none`
  must not have duplicate IDS paths.

### Example 1

```yaml
dd_version: 4.0.0

paths:
- all_of:
  - equilibrium/time(1)
  - equilibrium/time_slice(1)/global_quantities/ip
  - equilibrium/vacuum_toroidal_field/b0

- all_or_none:
  - iron_core/ids_properties/version_put/data_dictionary
  - iron_core/segment/b_field
  - iron_core/segment/geometry/outline/r
  - iron_core/segment/geometry/outline/z
  - iron_core/segment/permeability_relative

- any_of:
  - all_of:
    - wall/description_2d(1)/vessel/unit(1:2)/annular/centreline/r
    - wall/description_2d(1)/vessel/unit(1:2)/annular/centreline/z
    - wall/description_2d(1)/vessel/unit(1:2)/annular/thickness
  - all_of:
    - wall/description_2d(1)/vessel/unit(1:2)/annular/outline_inner/r
    - wall/description_2d(1)/vessel/unit(1:2)/annular/outline_inner/z
    - wall/description_2d(1)/vessel/unit(1:2)/annular/outline_outer/r
    - wall/description_2d(1)/vessel/unit(1:2)/annular/outline_outer/z

- any_of:
  - equilibrium/time_slice/profiles_1d/gm9
  - all_of:
    - equilibrium/time_slice/profiles_1d/r_inboard
    - equilibrium/time_slice/profiles_1d/r_outboard
```

## Constraints

Each entry in `constraints` describes which constraints are enforced on the data
array of the specified IDS path. Listing an IDS path under this key does not
imply that its presence is required.

The following mapping keys are allowed:

- `allowed_values`: maps to a sequence of mappings having the IDS path as key,
  which maps to a sequence of values (integer, float or string) that are allowed
  to be present in the data array at the IDS path. When specified, the data
  array must only consist of the listed values.
- `value_range`: maps to a sequence of mappings having the IDS path as key,
  which maps to a length-2 sequence of integers representing a closed interval.
  The values of the data array at the IDS path must fall within this interval.
  The value `null` can be used to indicate + / - infinity.
- `has_shape`: maps to a sequence of mappings having the IDS path as key, which
  maps to a list of integers describing the shape of the data array at the IDS
  path. The i-th integer in this list corresponds with the i-th axis of the data
  array.
- `same_shape`: maps to a sequence of mappings with the `all_of` key. The data
  arrays at the IDS paths listed under the `all_of` key must have the same
  shape.

### Example 2

```yaml

constraints:
  allowed_values:
  - equilibrium/time_slice/profiles_2d/grid_type/index: [1]

  value_range:
  - equilibrium/time_slice(1)/profiles_1d/psi: [0.0, 1.0]
  - equilibrium/time_slice(1)/global_quantities/ip: [null, 1000000000.0]

  has_shape:
  - pf_active/coil/element(1)/geometry/outline/r: [5]
  - pf_active/coil/element(1)/geometry/outline/z: [5]

  same_shape:
  - all_of:
    - core_sources/source(1)/profiles_1d(1)/electrons/energy
    - core_sources/source(1)/profiles_1d(1)/total_ion_energy
  - all_of:
    - pulse_schedule/ec/power/reference/data
    - pulse_schedule/ic/power/reference/data
```
