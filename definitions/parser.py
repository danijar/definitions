import os
import sys
import yaml
from definitions.error import DefinitionError, SchemaError
from definitions.attrdict import AttrDict, DefaultAttrDict


class Parser:

    def __init__(self, schema):
        schema = self._load(schema)
        schema = self._use_attrdicts(schema, fallbacks=True)
        self._validate_schema(schema)
        self._schema = schema

    def __call__(self, definition, attrdicts=True):
        definition = self._load(definition)
        definition = self._parse('schema root', self._schema, definition)
        if attrdicts:
            definition = self._use_attrdicts(definition)
        return definition

    def _validate_schema(self, schema):
        if schema is None:
            return
        if not isinstance(schema, dict):
            raise SchemaError('schema must be nested dicts')
        # Mutually exclusive keys
        exclusives = ('arguments', 'elements', 'mapping')
        if sum(x in schema for x in exclusives) > 1:
            message = '{} are mutually exclusive'.format(', '.join(exclusives))
            raise SchemaError(message)
        # Recursively check nested schemas
        if schema.arguments:
            self._validate_schema(schema.arguments)
        if schema.elements:
            self._validate_schema(schema.elements)
        if schema.mapping:
            self._validate_schema(schema.mapping)

    def _use_attrdicts(self, structure, fallbacks=False):
        """
        Recursively replace nested dicts with attribute default dicts.
        Optionally let them return None for non existing keys instead of
        raisinig an error.
        """
        if not isinstance(structure, dict):
            return structure
        mapping = {}
        for key, value in structure.items():
            value = self._use_attrdicts(value, fallbacks)
            mapping[key] = value
        if fallbacks:
            return DefaultAttrDict(mapping)
        else:
            return AttrDict(mapping)

    def _parse(self, name, schema, definition):
        if not schema:
            if definition is None:
                message = '{}: no value for required argument'.format(name)
                raise DefinitionError(message)
            return definition
        if not definition:
            return self._parse_default(name, schema)
        if 'arguments' in schema:
            return self._parse_arguments(name, schema, definition)
        if 'elements' in schema:
            return self._parse_elements(name, schema, definition)
        if 'mapping' in schema:
            return self._parse_mapping(name, schema, definition)
        else:
            return self._parse_single(name, schema, definition)

    def _parse_arguments(self, name, schema, definition):
        """
        Definition should contain kwargs and possibly a type.
        """
        base = self._find_type(schema.module, schema.get('type', object))
        subtype = self._find_type(schema.module, definition.pop('type', None))
        subtype = subtype or base
        # Validate subtype from definition.
        if not issubclass(subtype, base):
            message = ('{}: {} does not inherit from {}'
                       .format(name, subtype.__name__, base.__name__))
            raise DefinitionError(message)
        # Collect and recursively parse arguments.
        if not isinstance(definition, dict):
            raise DefinitionError('arguments must be a dict')
        arguments = {k: v.default for k, v in schema.arguments.items()}
        if isinstance(definition, dict):
            arguments.update(definition)
        for key, value in arguments.items():
            subschema = schema.arguments.get(key, None)
            arguments[key] = self._parse(key, subschema, value)
        return self._instantiate(name, subtype, **arguments)

    def _parse_elements(self, name, schema, definition):
        """
        Definition chould contain a list used as only argument.
        """
        base = self._find_type(schema.module, schema.type) or object
        if not isinstance(definition, list):
            raise DefinitionError('elements must be a list')
        elements = [self._parse(name + ' elements', schema.elements, x)
                    for x in definition]
        return self._instantiate(name, base, elements)

    def _parse_mapping(self, name, schema, definition):
        """
        Definition should contain a dict used as only argument.
        """
        base = self._find_type(schema.module, schema.type) or object
        if not isinstance(definition, dict):
            raise DefinitionError('mapping must be a dict')
        mapping = {k: self._parse(name + ' mapping', schema.mapping, v)
                   for k, v in definition.items()}
        return self._instantiate(name, base, mapping)

    def _parse_single(self, name, schema, definition):
        """
        Definition could be a subtype, only argument or single value.
        """
        base = self._find_type(schema.module, schema.type)
        subtype = self._find_type(schema.module, definition)
        if subtype and isinstance(subtype, base):
            arguments = self._parse(name + ' argument', schema.arguments, None)
            return self._instantiate(subtype, **arguments)
        elif base:
            argument = self._parse(name, schema.arguments, definition)
            return self._instantiate(name, base, argument)
        else:
            return definition

    def _parse_default(self, name, schema):
        """
        Use default from schema or raise error.
        """
        if schema.default:
            return self._parse(name, schema, schema.default)
        # See if all arguments have defaults.
        if schema.arguments:
            if all('default' in x for x in schema.arguments.values()):
                return self._parse_arguments(name, schema, {})
        message = '{}: omitted value that has no default'.format(name)
        raise DefinitionError(message)

    @staticmethod
    def _instantiate(name, type_, *args, **kwargs):
        try:
            return type_(*args, **kwargs)
        except ValueError:
            message = ('{}: cannot instantiate {} from args={} and kwargs={}'
                       .format(name, type_.__name__, args, kwargs))
            raise DefinitionError(message)

    @staticmethod
    def _load(source):
        """Load a YAML file or string."""
        if source and os.path.isfile(source):
            with open(source) as file_:
                return yaml.load(file_)
        return yaml.load(source)

    @staticmethod
    def _find_type(module, name):
        if not isinstance(name, str):
            return None
        scopes = [__builtins__]
        if module:
            __import__(module)
            scopes.insert(0, sys.modules[module])
        for scope in scopes:
            if isinstance(scope, dict) and name in scope:
                return scope[name]
            if hasattr(scope, name):
                return getattr(scope, name)
        return None
