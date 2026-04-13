# Structure of interface definitions

This document outlines the structure of interface definitions that describe
input and output datasets for simulation code using IMAS. These definitions are
written in YAML and use references to the IDS's in the IMAS Data Dictionary.
The structure of these definitions is formally described by the LinkML schema
`schemas/LinkML_schema.yaml`.

In each file at least one of the following two top level mapping keys must be
present:

- [`ids`](#specifying-ids-paths)
- [`include`](#including-other-definitions)

Optionally, a `dd_version` key may be present at the top level, specifying the
version of the IMAS Data Dictionary that the definition targets (e.g.
`4.1.0`).

## Specifying IDS paths

The key `ids` maps to a sequence of IDS entries. Each entry is a mapping with
the following keys:

- `ids_name`: The name of an IDS in the [IMAS Data
  Dictionary](https://imas-data-dictionary.readthedocs.io/en/latest/reference_ids.html).
- `required_paths`: A sequence of IDS paths that must be present in the dataset
  and whose data array must be non-empty.
- `constraints` (optional): A sequence of constraints applied to specific IDS
  paths.

### Required paths

Each entry in `required_paths` is a string representing an IDS path. These paths
follow the [IMAS IDS path
convention](https://imas-data-dictionary.readthedocs.io/en/latest/IDS-path-syntax.html)
where the forward slashes `/` seperate nested structures and index of arrays
can be given between round brackets `()` just after the array name.

### Constraints

Each entry in `constraints` describes which constraints are enforced on the data
array of the specified IDS path. The only mandatory key for this mapping is
`path`, which maps to a list of one or several IDS paths to which the constraint in question
applies. The paths listed here must also be present in the dataset. Other optional mapping keys are:

- `allowed_values`: A list of values (integer, float or string) that are allowed
  to be present in the data array at the IDS path. When specified, the data
  array must only consist of the listed values.
- `value_range`: A list of length 2 with floats describing a closed interval.
  When specified, the data array must only consist of values that fall
  within that interval.
- `has_shape`: A list of integers describing the shape of the data array at the IDS path. The i-th integer in this list corresponds with the i-th axis of the data array. When specified, the data array must have the indicated shape.
- `same_shape`: None. When specified, the data arrays at the IDS paths listed in `path` must have the same shape.
- `at_least_one_present`: None. When specified, at least one of the paths listed
  in key `paths` must be present in the dataset.

  Note: as it is demanded that the IDS path in `path` is present in the dataset,
  it is allowed to omit this path in the sequence `required_paths`.

### Example 1

```yaml
ids:
  - ids_name: pf_passive
    required_paths: # sequence of IDS paths
    - loop(i1)/name
    - loop(i1)/element(i2)/turns_with_sign
    - loop(i1)/current

    constraints:
    - path: loop(i1)/element(i2)/geometry/geometry_type
      allowed_values: [2,3,5,6] # rectangle, oblique, annulus and thick line are allowed
    - path: ids_properties/homogeneous_time
      allowed_values: [0,1]
```

## Including other definitions

The mapping with key `include` maps to a sequence of relative file paths, where
each path points to a YAML-file having the same structure as described in this
document.

Including YAML-files in this fashion is equivalent to concatenating the lists of
the mappings with keys `include` and `ids`. See the two examples below, where
the first example uses only this include statement and the second example lists the
IDS entries for each of the files under the include-key. These are
equivalent interface definitions according to this document.

### Example 2

```yaml
include: # sequence of relative paths to interface definitions
- efit++/magnetics.yaml
- efit++/pf_active.yaml
- efit++/pf_passive.yaml
- efit++/tf.yaml
- efit++/wall.yaml
```

### Example 3

```yaml
ids:
  - ids_name: magnetics
    required_paths:
    - b_field_pol_probe(i1)/name
    - b_field_pol_probe(i1)/position/r
    - b_field_pol_probe(i1)/position/phi
    - b_field_pol_probe(i1)/position/z
    - b_field_pol_probe(i1)/poloidal_angle
    - b_field_pol_probe(i1)/toroidal_angle
    - b_field_pol_probe(i1)/area
    - b_field_pol_probe(i1)/length
    - b_field_pol_probe(i1)/turns
    - b_field_pol_probe(i1)/field/data
    - flux_loop(i1)/name
    - flux_loop(i1)/position(i2)/r
    - flux_loop(i1)/position(i2)/phi
    - flux_loop(i1)/position(i2)/z
    - flux_loop(i1)/flux/data
    - ip(i1)/data
    - diamagnetic_flux(i1)/data

    constraints:
    - path: ids_properties/homogeneous_time
      allowed_values: [0,1]

  - ids_name: pf_active
    required_paths:
    - coil(i1)/name
    - coil(i1)/element/turns_with_sign
    - circuit(i1)/connections
    - circuit(i1)/current/data
    - supply(i1)/name

    constraints:
    - path: coil(i1)/element(i2)/geometry/geometry_type
      allowed_values: [2,3,5,6]
    - path: ids_properties/homogeneous_time
      allowed_values: [0,1]

  - ids_name: pf_passive
    required_paths:
    - loop(i1)/name
    - loop(i1)/element(i2)/turns_with_sign
    - loop(i1)/current

    constraints:
    - path: loop(i1)/element(i2)/geometry/geometry_type
      allowed_values: [2,3,5,6]
    - path: ids_properties/homogeneous_time
      allowed_values: [0,1]

  - ids_name: tf
    required_paths:
    - b_field_phi_vacuum_r/data

    constraints:
    - path: ids_properties/homogeneous_time
      allowed_values: [0,1]

  - ids_name: wall
    required_paths:
    - description_2d(i1)/limiter/unit(i2)/outline/r
    - description_2d(i1)/limiter/unit(i2)/outline/z

```
