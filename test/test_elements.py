# pylint: disable=no-self-use
from datetime import date
import pytest
from definitions import Parser
from definitions.error import DefinitionError


class TestElements:

    def test_parse_elements(self):
        assert Parser('')('[1, 2, Foo]') == [1, 2, 'Foo']

    def test_arbitrary_elements(self):
        parser = Parser('{type: list, elements:}')
        assert parser('[1, 2, Foo]') == [1, 2, 'Foo']

    def test_reject_non_list(self):
        parser = Parser('{type: list, elements: {}}')
        with pytest.raises(DefinitionError):
            print(parser('None'))
        with pytest.raises(DefinitionError):
            print(parser('42'))
        with pytest.raises(DefinitionError):
            print(parser('{foo: bar}'))

    def test_type(self):
        parser = Parser('{type: list, elements: {type: int}}')
        assert parser('[1, 2, 3]') == [1, 2, 3]
        assert parser('- 1\n- 2\n- 3') == [1, 2, 3]
        with pytest.raises(DefinitionError):
            parser('Foo')
        with pytest.raises(DefinitionError):
            parser('[Foo, Bar]')

    def test_arguments(self):
        parser = Parser(
            '{type: list, elements: {type: date, module: datetime, arguments: '
            '{year: {type: int}, month: {type: int}, day: {type: int}}}}')
        assert parser('[{year: 42, month: 3, day: 8}]') == [date(42, 3, 8)]
