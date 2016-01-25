import pytest
from argparse import ArgumentParser
from definitions import Parser
from definitions.error import ExpectedKey, UnknownKey


class TestAny:

    def __init__(self):
        self.SCHEMA_WITHOUT = ''
        self.SCHEMA_WITH = 'default: 42'

    def test_no_default_and_omitted(self):
        with pytest.raises(ExpectedKey):
            definition = Parser(self.SCHEMA_WITHOUT, '')

    def test_default_omitted(self):
        assert Parser(self.SCHEMA_WITH, '') == 42

    def test_override_default(self):
        assert Parser(self.SCHEMA_WITH, 'Foo') == 'Foo'


class TestArguments:

    def __init__(self):
        self.SCHEMA_WITHOUT = """
        type: ArgumentParser
        module: argparse
        default:
            prog:
            description:
        """
        self.SCHEMA_WITH = """
        type: ArgumentParser
        module: argparse
        default:
            prog: A default program.
            description: A default description.
        """
        self.DEFINITION = """
        prog: An overridden program.
        description: An overridden description.
        """

    def test_no_default_and_omitted(self):
        with pytest.raises(ExpectedKey):
            definition = Parser(self.SCHEMA_WITHOUT, '')

    def test_default_omitted(self):
        definition = Parser(self.SCHEMA_WITH, self.DEFINITION)
        assert isinstance(definition, ArgumentParser)
        assert definition.prog == 'A default program.'
        assert definition.description == 'A default description.'

    def test_override_default(self):
        definition = Parser(self.SCHEMA_WITH, self.DEFINITION)
        assert isinstance(definition, ArgumentParser)
        assert definition.prog == 'An overridden program.'
        assert definition.description == 'An overridden description.'
