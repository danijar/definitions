# pylint: disable=no-self-use
import os
from datetime import date
import pytest
from definitions import Parser
from definitions.error import DefinitionError


def filename(relative):
    return os.path.join(os.path.dirname(__file__), relative)


class TestAny:

    def test_no_default_no_value(self):
        with pytest.raises(DefinitionError):
            Parser('')('')

    def test_no_default_has_value(self):
        assert Parser('')('13') == 13

    def test_has_default_no_value(self):
        assert Parser('default: 42')('') == 42

    def test_has_default_has_value(self):
        assert Parser('default: 42')('13') == 13


class TestArguments:

    def test_no_default_no_value(self):
        schema = filename('schema/default/without_arguments.yaml')
        with pytest.raises(DefinitionError):
            Parser(schema)('')

    def test_no_default_has_value(self):
        definition = filename('definition/default/arguments.yaml')
        definition = Parser('')(definition)
        assert isinstance(definition, dict)
        assert definition.year == 13

    def test_has_default_no_value(self):
        schema = filename('schema/default/with_arguments.yaml')
        definition = Parser(schema)('')
        assert isinstance(definition, date)
        assert definition.year == 42

    def test_has_default_has_value(self):
        schema = filename('schema/default/with_arguments.yaml')
        parser = Parser(schema)
        definition = filename('definition/default/arguments.yaml')
        definition = parser(definition)
        assert isinstance(definition, date)
        assert definition.year == 13
