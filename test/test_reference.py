# pylint: disable=no-self-use, wildcard-import, unused-wildcard-import
from datetime import date
import pytest
from definitions import Parser
from definitions.error import DefinitionError
from test.fixtures import *


class ClassNoArgument:

    def __init__(self):
        self.value = 42


class ClassNeedsArgument:

    def __init__(self, class_no_argument):
        self.value = class_no_argument.value


class TestReference:

    def test_dict(self):
        schema = filename('schema/reference_dict.yaml')
        definition = Parser(schema)('reference: 42')
        assert definition.foo == 42

    def test_dict_nested(self):
        schema = filename('schema/reference_nested.yaml')
        definition = Parser(schema)('reference: {nested: 42}')
        print(definition)
        assert definition.foo.nested == 42

    def test_elements(self):
        schema = filename('schema/reference_elements.yaml')
        definition = Parser(schema)('reference: 42')
        assert definition.foo == [42, 42]

    def test_index(self):
        schema = filename('schema/reference_index.yaml')
        definition = Parser(schema)('reference: [13, 42]')
        assert definition.first == 13
        assert definition.second == 42

    def test_index_out_of_bounds(self):
        schema = filename('schema/reference_index.yaml')
        with pytest.raises(DefinitionError):
            Parser(schema)('reference: [13]')

    def test_index_both(self):
        parser = Parser(filename('schema/two_lists.yaml'))
        definition = parser("{foo: [13, 42], bar: ['$foo[1]', '$foo[0]']}")
        assert definition.bar == [42, 13]

    def test_arguments(self):
        parser = Parser(filename('schema/reference_arguments.yaml'))
        assert parser('reference: {type: ClassNoArgument}').foo.value == 42

    def test_arguments_default(self):
        parser = Parser(filename('schema/reference_arguments_default.yaml'))
        assert parser('{}').foo.value == 42

    def test_cyclic_dict(self):
        pass

    def test_cyclic_index(self):
        # parser = Parser(filename('schema/two_lists.yaml'))
        # with pytest.raises(DefinitionError):
        #     parser("{foo: ['$bar[0]'], bar: ['$foo[0]']}")
        pass
