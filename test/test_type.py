# pylint: disable=no-self-use, duplicate-code
import pytest
from definitions import Parser
from definitions.error import DefinitionError


class BaseClass:
    pass


class SubClass(BaseClass):
    pass


class OtherClass:
    pass


class TestType:

    def test_inherited(self):
        parser = Parser('{type: BaseClass, module: test.test_type}')
        parser('type: BaseClass')
        parser('type: SubClass')

    def test_not_inherited(self):
        parser = Parser('{type: BaseClass, module: test.test_type}')
        with pytest.raises(DefinitionError):
            parser('type: OtherClass')

    def test_shorthand_inherited(self):
        parser = Parser('{type: BaseClass, module: test.test_type}')
        parser('BaseClass')
        parser('SubClass')

    def test_shorthand_not_inherited(self):
        parser = Parser('{type: BaseClass, module: test.test_type}')
        with pytest.raises(DefinitionError):
            parser('OtherClass')


class BaseClassArgs:

    def __init__(self, argument1):
        self.argument1 = argument1


class SubClassArgs(BaseClassArgs):

    def __init__(self, argument1, argument2):
        super().__init__(argument1)
        self.argument2 = argument2


class TestArguments:

    def test_provided(self):
        parser = Parser('{type: BaseClassArgs, module: test.test_type}')
        definition = parser('{argument1: 42}')
        assert isinstance(definition, BaseClassArgs)
        assert definition.argument1 == 42

    def test_missing(self):
        with pytest.raises(DefinitionError):
            Parser('{type: BaseClassArgs, module: test.test_type}')('{}')

    def test_additional(self):
        parser = Parser('{type: BaseClassArgs, module: test.test_type}')
        definition = '{type: SubClassArgs, argument1: 42, argument2: 13}'
        definition = parser(definition)
        assert isinstance(definition, SubClassArgs)
        assert definition.argument1 == 42
        assert definition.argument2 == 13
