import os
import sys
import inspect
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
        definition = self._parse('root', self._schema, definition)
        if attrdicts:
            definition = self._use_attrdicts(definition)
        return definition

    def _validate_schema(self, schema):
        if schema is None:
            return
        if not isinstance(schema, dict):
            raise SchemaError('schema must be nested dicts')
        self._validate_type(schema)
        self._validate_exclusives(schema)
        self._validate_nested(schema)

    def _validate_type(self, schema):
        """
        Check if the type is available.
        """
        if 'type' not in schema:
            for key in ('arguments', 'elements', 'mapping'):
                if key in schema:
                    message = 'cannot parse {} without specified type'
                    message.format(key)
                    raise SchemaError(message)
        if 'type' in schema:
            if not self._find_type(schema.module, schema.type):
                message = 'type {} not found in module {}'
                message = message.format(schema.type, schema.module)
                raise SchemaError(message)

    @staticmethod
    def _validate_exclusives(schema):
        """
        Mutually exclusive keys.
        """
        exclusives = ('arguments', 'elements', 'mapping')
        if sum(x in schema for x in exclusives) > 1:
            message = '{} are mutually exclusive'.format(', '.join(exclusives))
            raise SchemaError(message)

    def _validate_nested(self, schema):
        """
        Recursively check nested schemas.
        """
        if schema.arguments:
            if not isinstance(schema.arguments, dict):
                raise SchemaError('arguments must be a dict')
            for argument in schema.arguments.values():
                self._validate_schema(argument)
        if schema.mapping:
            if not isinstance(schema.mapping, dict):
                raise SchemaError('mapping must be a dict')
            for value in schema.mapping.values():
                self._validate_schema(value)
        if schema.elements:
            self._validate_schema(schema.elements)

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
        has_type = schema and 'type' in schema
        if definition is not None and not has_type:
            return definition
        if definition is None:
            return self._parse_default(name, schema)
        if 'mapping' in schema:
            return self._parse_mapping(name, schema, definition)
        if 'elements' in schema:
            return self._parse_elements(name, schema, definition)
        if isinstance(definition, dict):
            return self._parse_arguments(name, schema, definition)
        else:
            return self._parse_single(name, schema, definition)

    def _parse_default(self, name, schema):
        """
        Parse default from schema or try to construct the type from the schema.
        Raise an error if no default is specified and the type requires
        arguments that have no defaults.
        """
        if schema and 'default' in schema:
            return self._parse(name, schema, schema.default)
        if schema and 'type' in schema:
            return self._parse_arguments(name, schema, {'type': schema.type})
        message = '{}: omitted value that has no default'.format(name)
        raise DefinitionError(message)

    def _parse_mapping(self, name, schema, definition):
        """
        Definition should contain a dict used as only argument.
        """
        if not isinstance(definition, dict):
            message = '{}: mapping must be a dict'.format(name)
            raise DefinitionError(message)
        mapping = {k: v.default for k, v in schema.mapping.items()}
        mapping.update(definition)
        for key, value in mapping.items():
            if key not in schema.mapping:
                message = '{}: unexpected mapping key {}'.format(name, key)
                raise DefinitionError(message)
            subname = '{}.{}'.format(name, key)
            subschema = schema.mapping[key]
            mapping[key] = self._parse(subname, subschema, value)
        base = self._find_type(schema.module, schema.type)
        return self._instantiate(name, base, mapping)

    def _parse_elements(self, name, schema, definition):
        """
        Definition chould contain a list used as only argument.
        """
        if not isinstance(definition, list):
            raise DefinitionError('elements must be a list')
        elements = [self._parse('{}[{}]'.format(name, i), schema.elements, x)
                    for i, x in enumerate(definition)]
        base = self._find_type(schema.module, schema.type)
        return self._instantiate(name, base, elements)

    def _parse_arguments(self, name, schema, definition):
        """
        Definition should be a mapping containing kwargs and possibly a type.
        """
        base = self._find_type(schema.module, schema.type)
        subtype = base
        if 'type' in definition:
            subtype = self._find_type(schema.module, definition.pop('type'))
            self._ensure_inherits(name, subtype, base)
        arguments = {}
        if 'arguments' in schema:
            arguments = {k: v.default for k, v in schema.arguments.items()}
        arguments.update(definition)
        for key, value in arguments.items():
            subschema = {}
            if 'arguments' in schema:
                subschema = schema.arguments.get(key, None)
            arguments[key] = self._parse(key, subschema, value)
        return self._instantiate(name, subtype, **arguments)

    def _parse_single(self, name, schema, definition):
        """
        Definition is a single typename or single constructor argument.
        """
        base = self._find_type(schema.module, schema.get('type', object))
        subtype = self._find_type(schema.module, definition)
        if inspect.isclass(subtype) and issubclass(subtype, base):
            return self._parse(name, schema, {'type': definition})
        else:
            return self._instantiate(name, base, definition)

    @staticmethod
    def _ensure_inherits(name, subtype, base):
        if inspect.isclass(subtype) and issubclass(subtype, base):
            return
        basename = base.__name__ if base else None
        subtypename = subtype.__name__ if subtype else None
        message = '{}: {} does not inherit from {}'
        message = message.format(name, subtypename, basename)
        raise DefinitionError(message)

    @staticmethod
    def _instantiate(name, type_, *args, **kwargs):
        try:
            return type_(*args, **kwargs)
        except (ValueError, TypeError) as error:
            message = '{}: cannot instantiate {} from args={} and kwargs={}'
            message = message.format(name, type_.__name__, args, kwargs)
            message += '. ' + str(error)
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
        if inspect.isclass(name):
            return name
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
