Definitions
===========

Load and validate YAML definitions against a schema. Classes are
directly instantiated from names in your definition files.

Definition
----------

Definitions can contain any valid YAML. The only reserved key in definitions is
`type` which can hold the name of a subclass of the the type defined in the
schema. If for a key just a single value is provided, it will be parsed as a
type name if possible, and otherwise as a value.

```yaml
key1: foo
key2: SubClassName
key3:
  argument1: foo
  argument2: 42
key4:
  type: SubClassName
  argument1: foo
  argument2: 42
key5:
- value1
- value2
- value3
```

Schema
------

Schemas are defined in a nested way. For example, you can specify the schemas
for required keys of a dict or for constructor arguments of a class. The
following keys have a special meaning.

| Key | Description |
| --- | ----------- |
| `type` | Name of Python type Name of the Python type or base class. |
| `module` | Where to import non-primitive types from. |
| `default` | Parsed when the key is not specified. |
| `arguments` | Mapping or single nested schema describing constructor arguments. |
| `elements` | Nested schema of elements that are passed as a list to the constructor. |
| `mapping` | Nested schema of values that are passed as a dict with string keys to the constructor. |

Only one of `arguments` and `elements` and `mapping` can be specified at the
same time. Also, those keys can only be parsed if a `type` is specified. Each
schema is validated to ensure these constraints.

Example
-------

### Definition

```yaml
cost: SquaredError
constraints:
- angle: 70
- angle: 120
distribution:
  type: Gaussian
  variance: 2.5
```

### Schema

```yaml
type: dict
mapping:
  cost:
    type: Cost
    module: mypackage.cost
  constraints:
    type: list
    elements:
      type: Constraint
      module: mypackage.constraint
      arguments:
        angle: {type: int}
  distribution:
    type: Distribution
    module: mypackage.distribution
    arguments:
      mean:
        type: float
        default: 0
  backup:
    type: bool
    default: false
```

### Usage in Code

```python
from definitions import Parser
from mypackage.cost import SquaredError
from mypackage.contraint import Constraint
from mypackage.distribution import Gaussian


parser = Parser('schema.yaml')
definition = parser('definition.yaml')

assert isinstance(definition.cost, SquaredError)

assert len(definition.constraints) == 2
assert all(isinstance(x, Constraint) for x in definition.constraints)
assert definition.constraints[0].angle == 70
assert definition.constraints[1].angle == 120

assert isinstance(definition.distribution, Gaussian)
assert definition.distribution.mean == 0
assert definition.distribution.variance == 2.5
```

Advanced Features
-----------------

### Access items in dict as properties

The `attrdicts` argument, which defaults to true, replaces all `dict` object in
the definition with `AttrDict`. This is just a Python dict except keys can be
accessed as attributes. You can also explicitly use this type in the schema to
allow attribute access only for some of the dicts.

```python
definition = Parser('schema.yaml', attrdicts=True)('definition.yaml')
assert definition.key == value

definition = Parser('schema.yaml', attrdicts=False)('definition.yaml')
assert definition['key'] == value
```

### Collection of arbitrary types

Don't specify the value for the `elements` or `mapping` key.

```yaml
type: list
elements:
```

### Defaults for constructor arguments

It is recommended to define arguments defaults in the constructor of the base
class. However, for standard types, it can make sense to define argument
defaults.

```yaml
type: date
module: datetime
arguments:
  year:
    type: int
    default: 2000
  month:
    type: int
    default: 1
  day:
    type: int
    default: 1
```

### Unknown arguments

Keys without a special meaning will always be passed as keyword arguments to
the constructur of the type. This allows subclasses to accept additional
parameters that are not listed in the base constructor.

### Shorter syntax

YAML provides a shorter syntax for mappings, that's similar to JSON. You can
even use real JSON for your schemas and definitions since YAML is a superset of
that.

```yaml
type: date
module datetime
arguments:
  year: {type: int, default: 2000}
  ...
```

### Enumerations

All types will get instantiated normally but this doesn't work for Python
`enum`. If you are interested in using enums, please [comment on the issue][1].

[1]: https://github.com/danijar/definitions/issues/6
