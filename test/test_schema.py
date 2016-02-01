# pylint: disable=no-self-use
import pytest
from definitions import Parser
from definitions.error import SchemaError


class TestSchema:

    def test_empty(self):
        Parser('')

    def test_nested_non_dicts(self):
        with pytest.raises(SchemaError):
            Parser('None')

    def test_arguments_non_dict(self):
        with pytest.raises(SchemaError):
            Parser('{arguments: None}')
        with pytest.raises(SchemaError):
            Parser('{arguments: [13]}')

    def test_elements_non_dict(self):
        with pytest.raises(SchemaError):
            Parser('{elements: None}')
        with pytest.raises(SchemaError):
            Parser('{elements: [13]}')

    def test_mapping_non_dict(self):
        with pytest.raises(SchemaError):
            Parser('{mapping: None}')
        with pytest.raises(SchemaError):
            Parser('{mapping: [13]}')

    def test_arguments_and_elements(self):
        with pytest.raises(SchemaError):
            Parser('{arguments: {}, elements: {}}')

    def test_arguments_and_mapping(self):
        with pytest.raises(SchemaError):
            Parser('{arguments: {}, mapping: {}}')

    def test_elements_and_mapping(self):
        with pytest.raises(SchemaError):
            Parser('{elements: {}, mapping: {}}')

    def test_type_found(self):
        Parser('{type: str}')

    def test_type_not_found(self):
        Parser('{type: str}')
        with pytest.raises(SchemaError):
            Parser('{type: Foo}')
