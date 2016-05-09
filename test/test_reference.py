# pylint: disable=no-self-use, wildcard-import, unused-wildcard-import
from datetime import date
import pytest
from definitions import Parser
from definitions.error import DefinitionError
from test.fixtures import *


class TestReference:

    def test_reference(self):
        schema = filename('schema/reference.yaml')
        definition = Parser(schema)('reference: 42')
        assert definition.foo == 42
