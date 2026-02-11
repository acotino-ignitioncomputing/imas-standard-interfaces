# Structure of interface definitions

This document outlines the structure of the interface definitions that describe
input datasets for equilibrium reconstruction code, like EFIT++. These
definitions are written in YAML and use references to the IDS's in the IMAS Data
Dictionary.

In each file at least one of the following two top level mapping keys must be
present:

- ids
- include

## Specifying IDS paths

The mapping with key `ids` maps to a squence of nested mappings, where the key
of each of these mappings is the name of an IDS in the IMAS Data Dictionary and
the value is a mapping with key `required`.

Each mapping with key `required` maps to a sequence of IDS paths that must be present in the dataset and whose data array must be
non-empty.

If there are no further constraints on the data array of an IDS path then it is
encoded as a `string`. In case there are extra constrains imposed on the data
array, then the IDS path is encoded as a mapping whose values are these
constraints.

Currently, the only constraint implemented is `allowed_values`, indicating which
values are allowed to be present in the data array.

**Example 1**

```
ids:
- pf_passive:
    required: # sequence of IDS paths
    - loop.name
    - loop.element.turns_with_sign
    - loop.element.geometry.geometry_type:
       allowed_values: [1,2,5] # Only outline, rectangle and annulus are allowed
    - loop.current
```

## Including other definitions

The mapping with key `include` maps to a sequence of relative file paths, where
each path points to a YAML-file having the same structure as described in this
document.

Including YAML-files in this fashion is equivalent to concatenating the lists of
the mappings with keys `include` and `ids`. See the two examples below, showing
 the content of `efit++_iter_structured_v1.0.yaml` and
`efit++_iter_unstructured_v1.0.yaml` respectively (relative file paths are
adjusted). These are equivalent interface definitions according to this
document.

**Example 2**

```
include: # sequence of relative paths to interface definitions
- ids_specific_definitions/efit++_magnetics_v1.0.yaml
- ids_specific_definitions/efit++_pf_active_v1.0.yaml
- ids_specific_definitions/efit++_pf_passive_v1.0.yaml
- ids_specific_definitions/efit++_tf_v1.0.yaml
- ids_specific_definitions/efit++_wall_v1.0.yaml
```

**Example 3**

```
ids:
- magnetics:
    required:
    - b_field_pol_probe.name
    - b_field_pol_probe.position.r
    - b_field_pol_probe.position.phi
    - b_field_pol_probe.position.z
    - b_field_pol_probe.poloidal_angle
    - b_field_pol_probe.toroidal_angle
    - b_field_pol_probe.area
    - b_field_pol_probe.length
    - b_field_pol_probe.turns
    - b_field_pol_probe.field.data
    - flux_loop.name
    - flux_loop.position.r
    - flux_loop.position.phi
    - flux_loop.position.z
    - flux_loop.flux.data
    - ip.data
    - diamagnetic_flux.data
    - ids_proporties.homogeneous_time:
      allowed_values: [0,1]
- pf_active:
    required:
    - coil.name
    - coil.element.turns_with_sign
    - coil.element.geometry.geometry_type:
        allowed_values: [1,2,5]
    - circuit.connections
    - circuit.current.data
    - supply.name
- pf_passive:
    required:
    - loop.name
    - loop.element.turns_with_sign
    - loop.element.geometry.geometry_type:
        allowed_values: [1,2,5]
    - loop.current
- tf:
    required:
    - b_field_phi_vacuum_r.data
- wall:
    required:
    - description_2d.limiter.unit.outline.r
    - description_2d.limiter.unit.outline.z
```