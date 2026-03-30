# Structure of interface definitions

This document outlines the structure of interface definitions that describe
input and output datasets for simulation code using IMAS. These definitions are
written in YAML and validated against the Pydantic model `InterfaceDefinition`
in `schemas/pydantic_schema.py`. They use references to the IDS's in the IMAS
Data Dictionary.

## Top-level keys

Each YAML file may contain the following top-level keys:

- `dd_version` *(optional)*: A string specifying the version of the IMAS Data
  Dictionary to target (e.g. `"4.1.0"`).
- `include` *(optional)*: A list of relative file paths to other interface
  definitions to include. See [Including other definitions](#including-other-definitions).
- One or more **IDS names** (e.g. `magnetics`, `pf_active`, `wall`, etc.): Each
  maps to a nested structure of required IDS paths. See
  [Specifying IDS paths](#specifying-ids-paths).

At least one IDS name or `include` must be present for the definition to be
meaningful.

## Specifying IDS paths

Each IDS is specified as a top-level key whose name matches an IDS in the
[IMAS Data Dictionary](https://imas-data-dictionary.readthedocs.io/en/latest/reference_ids.html).
Its value is a nested mapping that mirrors the hierarchical structure of the IDS.

The nested mapping follows the recursive type `IDS_PATH`, defined as:

```python
IDS_PATH = Dict[str, None | IDS_PATH | list[int]]
```

Each key in the mapping is a node name from the IDS path. The value can be:

- **`null`/empty** — Indicates that this path is required and its data array
  must be non-empty. In YAML, this is written by leaving the value empty
  (e.g. `name:` or using flow style `{data:}`).
- **A nested mapping** (`IDS_PATH`) — Indicates further nesting into the IDS
  structure.
- **A list of integers** (e.g. `[0,1]` or `[1,2,5]`) — Constrains which values
  are allowed in the data array at this path.

### Example 1: Single IDS

```yaml
dd_version: 4.1.0

pf_passive:
  loop:
    name:
    element:
      turns_with_sign:
      geometry:
        geometry_type: [2,3,5,6]  # rectangle, oblique, annulus and thick line are allowed
    current:
  ids_proporties:
    homogeneous_time: [0,1]
```

In this example:

- `loop.name`, `loop.element.turns_with_sign`, and `loop.current` are required
  paths with no value constraints (empty/null values).
- `loop.element.geometry.geometry_type` is required and constrained to the
  values `2`, `3`, `5` or `6`.
- `ids_proporties.homogeneous_time` is required and constrained to the values
  `0` or `1`.

### Example 2: Flow style for simple sub-structures

When a node has only a few children, YAML flow style can be used for brevity:

```yaml
dd_version: 4.1.0

magnetics:
  b_field_pol_probe:
    name:
    position: {r:, phi:, z:}
    poloidal_angle:
    toroidal_angle:
    area:
    length:
    turns:
    field: {data:}
  flux_loop:
    name:
    position: {r:, phi:, z:}
    flux: {data:}
  ip: {data:}
  diamagnetic_flux: {data:}
  ids_proporties:
    homogeneous_time: [0,1]
```

## Including other definitions

The `include` key maps to a list of relative file paths, where each path points
to a YAML file having the same structure as described in this document.

Including files is equivalent to merging their contents: combining the IDS path
mappings from all included files into a single interface definition.

### Example 3

```yaml
include:  # list of relative paths to interface definitions
- magnetics.yaml
- pf_active.yaml
- pf_passive.yaml
- tf.yaml
- wall.yaml
```

The above include is equivalent to specifying all IDS paths directly in a single
file:

### Example 4: Equivalent expanded form

```yaml
dd_version: 4.1.0

magnetics:
  b_field_pol_probe:
    name:
    position: {r:, phi:, z:}
    poloidal_angle:
    toroidal_angle:
    area:
    length:
    turns:
    field: {data:}
  flux_loop:
    name:
    position: {r:, phi:, z:}
    flux: {data:}
  ip: {data:}
  diamagnetic_flux: {data:}
  ids_proporties:
    homogeneous_time: [0,1]

pf_active:
  coil:
    name:
    element:
      turns_with_sign:
      geometry:
        geometry_type: [2,3,5,6]
  circuit:
    connections:
    current: {data:}
  supply:
    name:
  ids_proporties:
    homogeneous_time: [0,1]

pf_passive:
  loop:
    name:
    element:
      turns_with_sign:
      geometry:
        geometry_type: [2,3,5,6]
    current:
  ids_proporties:
    homogeneous_time: [0,1]

tf:
  b_field_phi_vacuum_r: {data:}
  ids_proporties:
    homogeneous_time: [0,1]

wall:
  description_2d:
    limiter:
      unit:
        outline: {r:, z:}
```
