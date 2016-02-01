# pylint: disable=no-self-use
import pytest
from definitions import Parser


class TestUseAttrdict:

    def test_dict_dict_access(self):
        parser = Parser('{type: dict, mapping: {foo: {}}}')
        definition = parser('{foo: bar}', attrdicts=False)
        assert definition['foo'] == 'bar'

    def test_dict_attr_access(self):
        parser = Parser('{type: dict, mapping: {foo: {}}}')
        definition = parser('{foo: bar}', attrdicts=False)
        with pytest.raises(AttributeError):
            # pylint: disable=pointless-statement
            definition.foo

    def test_attrdict_attr_access(self):
        parser = Parser('{type: dict, mapping: {foo: {}}}')
        definition = parser('{foo: bar}', attrdicts=True)
        assert definition.foo == 'bar'

    def test_attrdict_dict_access(self):
        parser = Parser('{type: dict, mapping: {foo: {}}}')
        definition = parser('{foo: bar}', attrdicts=True)
        assert definition['foo'] == 'bar'

    def test_nested(self):
        schema, definition = '{}', '{}'
        for _ in range(5):
            schema = schema.replace('{}', '{type: dict, mapping: {key: {}}}')
            definition = definition.replace('{}', '{key: {}}')
        definition = Parser(schema)(definition, attrdicts=True)
        assert definition.key.key.key.key.key == {}
