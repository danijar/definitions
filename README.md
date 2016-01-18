definitions
===========

Load and validate YAML definitions against a schema. Classes are
directly instantiated from names in your definition files.

Definition
----------

The only reserved key in definitions is `type` which can hold the name of a
subclass of the the type defined in the schema. Now, let's take a look at the
schema.

```yaml
key1: value
key2: ClassName
key3:
  argument1: foo
  argument2: 42
key4:
  type: SubClassName
  argument1: foo
  argument2: 42
```

Schema
------

Schemas are defined in a nested way. For example, you can specify the schemas
for required keys of a dict or for constructor arguments of a class. All top-level entries of the schema are held by a dict. The following keys have
a special meaning.

| Key | Description |
| --- | ----------- |
| `type` | Name of Python type Name of the Python type or base class. |
| `module` | Where to import non-primitive types from. |
| `default` | Parsed when the key is not specified. |
| `arguments` | Nested list of schemas describing how constructor arguments should be parsed. |
| `elements` | Nested schema or list of schemas. A collection of matching elements will be passed to the constructor. |

Example
-------

### Definition

```yaml
cost: SquaredError
constraints:
- angle: 70
- type: HINGE
  angle: 120
distribution:
  type: Gaussian
  variance: 2.5
```

### Schema

```yaml
cost:
  type: Cost
  module: mypackage.cost
constraints:
  type: list
  elements:
    type: Constraint
    module: mypackage.constraint
    parameters:
      constraint_type: ConstraintType
      module: mypackage.constraint
distribution:
  type: Distribution
  module: mypackage.distribution
  parameters:
    mean:
      type: float
    variance:
      type: float
backup:
  type: bool
  default: false
```

### Usage in Code

```python
from definitions import Parser
from mypackage.cost import SquaredError
from mypackage.contraint import Constraint, ConstraintType
from mypackage.distribution import Gaussian


definition = Parser('schema.yaml', 'definition.yaml', attribute_dicts=True)

assert isinstance(definition.cost, SquaredError)

first = definition.constraints[0]
assert isinstance(first, Constraint)
assert first.get_angle() == 70
assert first.get_type() == ConstraintType.ROTARY  # Constructor default

second = definition.constraints[1]
assert isinstance(second, Constraint)
assert second.get_angle() == 120
assert second.get_type() == ConstraintType.HINGE

assert isinstace(definition.distribution, Gaussian)
assert definition.distribution.get_mean() == 0
assert definition.distribution.get_variance() == 2.5

assert not definition.backup
```

Advanced Features
-----------------

### Access items in dict as properties

Passing `attribute_dicts=True` to the parser consturctor substitutes all `dict`
types with `AttributeDict`. This is just a Python dict except keys can be
accessed as attributes. You can also explicitly use this type in the schema to
allow attribute access only for some of the dicts.

```python
definition = Parser('schema.yaml', 'definition.yaml')
assert definition['key'] == value

definition = Parser('schema.yaml', 'definition.yaml', attribute_dicts=True)
assert definition.key == value
```

### Defaults for constructor arguments

It is possible to define defaults for arguments in the schema. However, it's
recommended to define default arguments in the constructor of the class
instead, so that there is no duplication.

### Unknown arguments

Keys without a special meaning will always be passed as keyword arguments to
the constructur of the type. This allows subclasses to accept additional
parameters that are not listed in the base constructor.

### Lists containing multiple types

Just list a collection of multiple elements after the `elements` key.

```yaml
people:
  type: set
  elements:
  - type: Worker
    module: mypackage.people
  - type: Visitor
    module: mypackage.people
```

This can parse definitions like this:

```yaml
people:
- Worker
- type: Worker
  name: John
- Visitor
```

### Enumerations

Usually, types get instantiated. However, for enumerations the corresponding
constant is stored. Just use a `type` that inherits from Python's `enum`.
