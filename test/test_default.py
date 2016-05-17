# pylint: disable=no-self-use, wildcard-import, unused-wildcard-import
from datetime import date
import pytest
from definitions import Parser
from definitions.error import DefinitionError
from test.fixtures import *


class TestAny:

    def test_no_default_no_value(self):
        with pytest.raises(DefinitionError):
            Parser('')('')

    def test_has_default_no_value(self):
        assert Parser('default: 42')('') == 42

    def test_no_default_has_value(self):
        assert Parser('')('13') == 13

    def test_has_default_has_value(self):
        assert Parser('default: 42')('13') == 13


class ClassNoArgument:

    def __init__(self):
        self.value = 42


class ClassArgument:

    def __init__(self, value):
        pass


class TestType:

    def test_no_default_no_value(self):
        with pytest.raises(DefinitionError):
            Parser('{type: ClassArgument, module: test.test_default}')('')

    def test_has_default_no_value(self):
        assert Parser('type: int')('') == 0
        assert Parser('{type: int, default: 42}')('') == 42
        parser = Parser('{type: ClassNoArgument, module: test.test_default}')
        assert parser('').value == 42

    def test_no_default_has_value(self):
        assert Parser('type: int')('13') == 13

    def test_has_default_has_value(self):
        assert Parser('{type: int, default: 42}')('13') == 13


class TestArguments:

    def test_no_default_no_value(self):
        schema = filename('schema/date.yaml')
        with pytest.raises(DefinitionError):
            Parser(schema)('')

    def test_has_default_no_value(self):
        schema = filename('schema/date_default.yaml')
        definition = Parser(schema)('')
        assert isinstance(definition, date)
        assert definition.year == 42

    def test_no_default_has_value(self):
        definition = filename('definition/date.yaml')
        definition = Parser('')(definition)
        assert isinstance(definition, dict)
        assert definition.year == 13

    def test_has_default_has_value(self):
        schema = filename('schema/date_default.yaml')
        parser = Parser(schema)
        definition = filename('definition/date.yaml')
        definition = parser(definition)
        assert isinstance(definition, date)
        assert definition.year == 13


class TestCollection:

    def test_no_default_no_value(self):
        schema = filename('schema/date.yaml')
        with pytest.raises(DefinitionError):
            Parser(schema)('')

    def test_has_default_no_value(self):
        schema = filename('schema/list_default.yaml')
        definition = Parser(schema)('')
        assert isinstance(definition, list)
        assert definition == [13, 42]

    def test_no_default_has_value(self):
        definition = filename('definition/list.yaml')
        definition = Parser('')(definition)
        assert isinstance(definition, list)
        assert definition == ['Foo']

    def test_has_default_has_value(self):
        schema = filename('schema/list_default.yaml')
        parser = Parser(schema)
        definition = filename('definition/list.yaml')
        definition = parser(definition)
        assert isinstance(definition, list)
        assert definition == ['Foo']


class TestMapping:

    def test_nested_has_default(self):
        pass
