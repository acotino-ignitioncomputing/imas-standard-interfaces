# Structure of interface definitions

This document outlines the structure of interface definitions that describe
input and output datasets for simulation code using IMAS. These definitions are
written in YAML following the [LinkML](https://linkml.io/) schema language and
use references to the IDS's in the IMAS Data Dictionary.

## LinkML schema structure

Each definition file is a LinkML schema with the following top-level keys:

| Key           | Description                                                  |
|---------------|--------------------------------------------------------------|
| `id`          | A unique URI identifying the schema                          |
| `name`        | A short name for the schema                                  |
| `description` | A human-readable description of the schema                   |
| `version`     | The IMAS Data Dictionary version the definition targets      |
| `prefixes`    | Namespace prefix declarations used in the schema             |
| `imports`     | A list of other schemas or LinkML built-ins to import        |
| `classes`     | Definitions of IDS classes with their required attributes    |
| `enums`       | Definitions of enumerated value sets used by attributes      |

## Specifying IDS paths as classes and attributes

Each IDS is represented as a **class** under the `classes` key. The class name
corresponds to the name of an IDS in the [IMAS Data
Dictionary](https://imas-data-dictionary.readthedocs.io/en/latest/reference_ids.html).

The required IDS paths are specified as **attributes** of the class. Each
attribute name follows the [IMAS netCDF naming
convention](https://imas-python.readthedocs.io/en/stable/netcdf/conventions.html)
where the forward slashes (`/`) in the corresponding Data Dictionary path are
replaced by periods (`.`).

Each attribute has the following properties:

| Property      | Description                                                  |
|---------------|--------------------------------------------------------------|
| `description` | A human-readable description of the attribute                |
| `required`    | Set to `true` to indicate the path must be present and non-empty |
| `range`       | (Optional) References an enum to constrain allowed values    |

**Example 1**

```yaml
id: https://imas.iter.org/schemas/pf_passive
name: pf_passive
description: Interface definition for the pf_passive IDS
version: "4.1.0"

prefixes:
  linkml: https://w3id.org/linkml/
  imas: https://imas.iter.org/schemas/

imports:
  - linkml:types

classes:
  pf_passive:
    description: PF passive structures IDS interface definition
    attributes:
      loop.name:
        description: Name of the passive loop
        required: true
      loop.element.turns_with_sign:
        description: Turns with sign of the loop element
        required: true
      loop.element.geometry.geometry_type:
        description: Geometry type of the loop element
        required: true
        range: GeometryTypeEnum
      loop.current:
        description: Current in the passive loop
        required: true

enums:
  GeometryTypeEnum:
    description: Allowed geometry types (outline, rectangle, annulus)
    permissible_values:
      1:
        description: Outline
      2:
        description: Rectangle
      5:
        description: Annulus
```

## Constraining allowed values with enums

When an IDS path has a restricted set of allowed values, these are expressed
using the LinkML `enums` construct. An enum is defined under the top-level
`enums` key and referenced from an attribute via the `range` property.

Each enum contains a `permissible_values` mapping where the keys are the
allowed values and each value can have a `description`.

## Importing other definitions

The LinkML `imports` key replaces the previous `include` mechanism. It maps to
a list of schema references to import. Importing a schema is equivalent to
merging its classes, enums, and other definitions into the current schema.

The special import `linkml:types` brings in the LinkML built-in type
definitions and should be included in every schema.

To import other definition files, list them by name (without the `.yaml`
extension) in the `imports` list.

### Example 2

```yaml
id: https://imas.iter.org/schemas/input_efit_structured
name: input_efit_structured
description: Structured input interface definition for EFIT++
version: "4.1.0"

prefixes:
  linkml: https://w3id.org/linkml/
  imas: https://imas.iter.org/schemas/

imports:
  - linkml:types
  - magnetics
  - pf_active
  - pf_passive
  - tf
  - wall
```
