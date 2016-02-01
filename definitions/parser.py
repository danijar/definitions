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
        if schema.type and not self._find_type(schema.module, schema.type):
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
        if schema is None:
            if definition is None:
                message = '{}: no value for required argument'.format(name)
                raise DefinitionError(message)
            return definition
        if definition is None:
            return self._parse_default(name, schema)
        if 'arguments' in schema:
            return self._parse_arguments(name, schema, definition)
        if 'mapping' in schema:
            return self._parse_mapping(name, schema, definition)
        if 'elements' in schema:
            return self._parse_elements(name, schema, definition)
        else:
            return self._parse_single(name, schema, definition)

    def _parse_arguments(self, name, schema, definition):
        """
        Definition should be a mapping containing kwargs and possibly a type.
        Alternatively, definition is just a typename.
        """
        base = self._find_type(schema.module, schema.get('type', object))
        if isinstance(definition, dict):
            subtype = definition.pop('type', None)
        elif isinstance(definition, str):
            subtype = definition
        else:
            message = '{}: dict or type name expected'.format(name)
            raise DefinitionError(message)
        subtype = self._find_type(schema.module, subtype)
        subtype = subtype or base
        # Validate subtype from definition.
        if not inspect.isclass(subtype) or not issubclass(subtype, base):
            basename = base.__name__ if base else None
            subtypename = subtype.__name__ if subtype else None
            message = '{}: {} does not inherit from {}'
            message = message.format(name, subtypename, basename)
            raise DefinitionError(message)
        # Collect and recursively parse arguments.
        arguments = {}
        if schema.arguments:
            arguments = {k: v.default for k, v in schema.arguments.items()}
        if isinstance(definition, dict):
            arguments.update(definition)
        for key, value in arguments.items():
            subschema = schema.arguments.get(key, None)
            arguments[key] = self._parse(key, subschema, value)
        return self._instantiate(name, subtype, **arguments)

    def _parse_single(self, name, schema, definition):
        """
        Definition could be the only argument or an unspecified single value.
        """
        base = self._find_type(schema.module, schema.type)
        subtype = self._find_type(schema.module, definition)
        if subtype and issubclass(subtype, base):
            return self._parse_arguments(name, schema, definition)
        elif base:
            argument = self._parse(name, schema.arguments, definition)
            return self._instantiate(name, base, argument)
        else:
            return definition

    def _parse_mapping(self, name, schema, definition):
        """
        Definition should contain a dict used as only argument.
        """
        base = self._find_type(schema.module, schema.type) or object
        mapping = {}
        if not isinstance(definition, dict):
            message = '{}: mapping must be a dict'.format(name)
            raise DefinitionError(message)
        for key, value in definition.items():
            if key not in schema.mapping:
                message = '{}: unexpected mapping key {}'.format(name, key)
                raise DefinitionError(message)
            subname = '{}.{}'.format(name, key)
            subschema = schema.mapping[key]
            mapping[key] = self._parse(subname, subschema, value)
        return self._instantiate(name, base, mapping)

    def _parse_elements(self, name, schema, definition):
        """
        Definition chould contain a list used as only argument.
        """
        base = self._find_type(schema.module, schema.type) or object
        if not isinstance(definition, list):
            raise DefinitionError('elements must be a list')
        elements = [self._parse('{}[{}]'.format(name, i), schema.elements, x)
                    for i, x in enumerate(definition)]
        return self._instantiate(name, base, elements)

    def _parse_default(self, name, schema):
        """
        Use default from schema or raise error.
        """
        if schema.default is not None:
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
