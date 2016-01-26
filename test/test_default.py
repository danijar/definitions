import pytest
from argparse import ArgumentParser
from definitions import Parser
from definitions.error import ExpectedKey, UnknownKey


class TestAny:

    def test_no_default_no_value(self):
        with pytest.raises(ExpectedKey):
            definition = Parser('', '')

    def test_no_default_has_value(self):
        assert Parser('', '13') == 13

    def test_has_default_no_value(self):
        assert Parser('default: 42', '') == 42

    def test_has_default_has_value(self):
        assert Parser('default: 42', '13') == 13


class TestArguments:

    def test_no_default_no_value(self):
        with pytest.raises(ExpectedKey):
            Parser('schema/default/without_arguments.yaml')('')

    def test_no_default_has_value(self):
        definition = Parser('')('definition/default/arguments.yaml')
        assert definition.prog == 'A specified program.'
        assert definition.description == 'A specified description.'

    def test_has_default_no_value(self):
        definition = Parser('schema/default/with_arguments.yaml')('')
        assert isinstance(definition, ArgumentParser)
        assert definition.prog == 'A default program.'
        assert definition.description == 'A default description.'

    def test_has_default_has_value(self):
        parser = Parser('schema/default/with_arguments.yaml')
        definition = parser('definition/default/arguments.yaml')
        definition = Parser(self.schema_with, self.definition)
        assert isinstance(definition, ArgumentParser)
        assert definition.prog == 'A specified program.'
        assert definition.description == 'A specified description.'
