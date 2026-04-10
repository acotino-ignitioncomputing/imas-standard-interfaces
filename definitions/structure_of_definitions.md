# Structure of interface definitions

This document outlines the structure of interface definitions that describe
input and output datasets for simulation code using IMAS. These definitions are
written in YAML and  are validated against the Pydantic model
`InterfaceDefinition` in `schemas/pydantic_schema.py`. They use references to the
IDS's in the IMAS Data Dictionary.

The Data Dictionary version is denoted in the optional top-level key:

- `dd_version`

In each file at least one of the following two top level mapping keys must be
present:

- [`ids`](#specifying-ids-paths)
- [`include`](#including-other-definitions)

## Specifying IDS paths

The mapping with key `ids` maps to a sequence of nested mappings, where the key
of each of these mappings is the name of an IDS in the [IMAS Data
Dictionary](https://imas-data-dictionary.readthedocs.io/en/latest/reference_ids.html
).

Each of these mappings maps to a sequence of IDS paths that must be
present in the dataset and whose data array must be non-empty. These paths
follow the [IMAS IDS path
convention](https://imas-data-dictionary.readthedocs.io/en/latest/IDS-path-syntax.html)
where the forward slashes `/` seperate nested structures and index of arrays
can be given between round brackets `()` just after the array name.

If there are no further constraints on the data array of an IDS path then the
path is encoded as a `string`. In case there are extra constraints imposed on
the data array, the IDS path is encoded as a mapping whose values are these
constraints.

Currently, the only constraint implemented is `allowed_values`, indicating which
values are allowed to be present in the data array.

### Example 1

```yaml
dd_version: 4.1.0
ids:
  pf_passive: # sequence of IDS paths
  - loop(i1)/name
  - loop(i1)/element(i2)/turns_with_sign
  - loop(i1)/element(i2)/geometry/geometry_type:
      allowed_values: [2,3,5,6] # rectangle, oblique, annulus and thick line are allowed
  - loop(i1)/current
  - ids_properties/homogeneous_time:
      allowed_values: [0,1]
```

## Including other definitions

The mapping with key `include` maps to a sequence of relative file paths, where
each path points to a YAML-file having the same structure as described in this
document.

Including YAML-files in this fashion is equivalent to concatenating the lists of
the mappings with keys `include` and `ids`. See the two examples below, where
the first example uses only this include statement and the second example lists the
IDS paths in each of the files under the include-key. These are
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
  magnetics:
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
  - ids_properties/homogeneous_time:
      allowed_values: [0,1]
  pf_active:
  - coil(i1)/name
  - coil(i1)/element/turns_with_sign
  - coil(i1)/element(i2)/geometry/geometry_type:
      allowed_values: [2,3,5,6]
  - circuit(i1)/connections
  - circuit(i1)/current/data
  - supply(i1)/name
  - ids_properties/homogeneous_time:
      allowed_values: [0,1]
  pf_passive:
  - loop(i1)/name
  - loop(i1)/element(i2)/turns_with_sign
  - loop(i1)/element(i2)/geometry/geometry_type:
      allowed_values: [2,3,5,6]
  - loop(i1)/current
  - ids_properties/homogeneous_time:
      allowed_values: [0,1]
  tf:
  - b_field_phi_vacuum_r/data
  - ids_properties/homogeneous_time:
      allowed_values: [0,1]
  wall:
  - description_2d(i1)/limiter/unit(i2)/outline/r
  - description_2d(i1)/limiter/unit(i2)/outline/z
```
