__author__ = 'Robbert Harms'
__date__ = '2023-01-25'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from abc import ABCMeta, abstractmethod
from typing import Union

from elements import Report, Assert, Variable, Rule, SchematronElement, Pattern
from parser import ReportParser, AssertParser, VariableParser, RuleParser, PatternParser


def test_pattern_parser():
    tester = PatternTester.get_default()
    tester.test_correctness(tester.get_parsed_element())


def test_rule_parser():
    tester = RuleTester.get_default()
    tester.test_correctness(tester.get_parsed_element())


def test_report_parser():
    tester = ReportTester.get_default()
    tester.test_correctness(tester.get_parsed_element())


def test_assert_parser():
    tester = AssertTester.get_default()
    tester.test_correctness(tester.get_parsed_element())


def test_let_parser():
    tester = VariableTester.get_default()
    tester.test_correctness(tester.get_parsed_element())


class SchematronElementTester(metaclass=ABCMeta):

    @classmethod
    @abstractmethod
    def get_default(cls):
        """Get a default test case

        Returns:
            Complete instance of this implemented class with a default test case loaded.
        """

    @abstractmethod
    def get_xml_string(self) -> str:
        """Get a complete XML string with the content of this test case.

        Returns:
            An XML formatted string which we can parse as part of the test case.
        """

    @abstractmethod
    def get_parsed_element(self) -> SchematronElement:
        """Get the element we parsed from this test case.

        This parses the result of the method `meth`:get_xml_string`.

        Returns:
            The parsed XML string.
        """

    @abstractmethod
    def test_correctness(self, parsed_element: SchematronElement) -> None:
        """Test the correctness of the parsed element.

        This is typically provided with the result of :meth:`get_parsed_element`, but can also be provided
        with another element. We made this field compulsory to ensure we do not forget to provide this test case
        with the actual parsed content.

        This should not return anything, it should merely assert if everything is correct.

        Args:
            parsed_element: the parsed element
        """


class PatternTester(SchematronElementTester):

    def __init__(self,
                 rules: list["RuleTester"],
                 variables: list["VariableTester"],
                 id: str):
        self._rules = rules
        self._variables = variables
        self._id = id

    @classmethod
    def get_default(cls):
        """Get a default test case"""
        variables = [
            VariableTester({'name': 'pattern_var', 'value': '//*/test'}),
            VariableTester({'name': 'second', 'value': '//root/*'})
        ]
        rules = [RuleTester.get_default()]
        return cls(rules, variables, 'pattern_id')

    def get_xml_string(self) -> str:
        xml_str = f'<pattern id="{self._id}">'
        for variable in self._variables:
            xml_str += variable.get_xml_string()
        for rule in self._rules:
            xml_str += rule.get_xml_string()
        xml_str += '</pattern>'
        return xml_str

    def get_parsed_element(self):
        return PatternParser().parse(self.get_xml_string())

    def test_correctness(self, parsed_element: Pattern):
        assert parsed_element.id == self._id
        for ind, variable in enumerate(self._variables):
            variable.test_correctness(parsed_element.variables[ind])
        for ind, rule in enumerate(self._rules):
            rule.test_correctness(parsed_element.rules[ind])


class RuleTester(SchematronElementTester):

    def __init__(self,
                 context: str,
                 variables: list["VariableTester"],
                 tests: list[Union["AssertTester", "ReportTester"]]):
        self._context = context
        self._variables = variables
        self._tests = tests

    @classmethod
    def get_default(cls):
        """Get a default test case"""
        variables = [
            VariableTester({'name': 'documents', 'value': '//root/documents'}),
            VariableTester({'name': 'test', 'value': '//root/tests'})
        ]
        tests = [AssertTester.get_default(), ReportTester.get_default()]
        return cls('//test/data', variables, tests)

    def get_xml_string(self) -> str:
        xml_str = f'<rule context="{self._context}">'
        for variable in self._variables:
            xml_str += variable.get_xml_string()
        for test in self._tests:
            xml_str += test.get_xml_string()
        xml_str += '</rule>'
        return xml_str

    def get_parsed_element(self):
        return RuleParser().parse(self.get_xml_string())

    def test_correctness(self, parsed_element: Rule):
        assert parsed_element.context == self._context
        for ind, variable in enumerate(self._variables):
            variable.test_correctness(parsed_element.variables[ind])
        for ind, test in enumerate(self._tests):
            test.test_correctness(parsed_element.tests[ind])


class AssertTester(SchematronElementTester):

    def __init__(self, attributes: dict[str, str], content: str):
        self._attributes = attributes
        self._content = content

    @classmethod
    def get_default(cls):
        """Get a default test case"""
        return cls({'test': '//notes', 'id': 'unique-id'}, '''
            String with <emph>bold text</emph>, a value: <value-of select="note/to/text()" />,
            <dir> reversed stuff</dir> and text at the end.
        ''')

    def get_xml_string(self) -> str:
        return f'<assert test="{self._attributes["test"]}" id="{self._attributes["id"]}">{self._content}</assert>'

    def get_parsed_element(self):
        return AssertParser().parse(self.get_xml_string())

    def test_correctness(self, parsed_element: Assert):
        assert parsed_element.id == self._attributes['id']
        assert parsed_element.test == self._attributes['test']
        assert parsed_element.content == self._content


class ReportTester(SchematronElementTester):

    def __init__(self, attributes: dict[str, str], content: str):
        self._attributes = attributes
        self._content = content

    @classmethod
    def get_default(cls):
        """Get a default test case"""
        return cls({'test': '//notes', 'id': 'unique-id'}, '''
            String with <emph>bold text</emph>, a value: <value-of select="note/to/text()" />,
            <dir> reversed stuff</dir> and text at the end.
        ''')

    def get_xml_string(self) -> str:
        return f'<report test="{self._attributes["test"]}" id="{self._attributes["id"]}">{self._content}</report>'

    def get_parsed_element(self):
        return ReportParser().parse(self.get_xml_string())

    def test_correctness(self, parsed_element: Report):
        assert parsed_element.id == self._attributes['id']
        assert parsed_element.test == self._attributes['test']
        assert parsed_element.content == self._content


class VariableTester(SchematronElementTester):

    def __init__(self, attributes: dict[str, str]):
        self._attributes = attributes

    @classmethod
    def get_default(cls):
        """Get a default test case"""
        return cls({'name': 'documents', 'value': '//root/documents'})

    def get_xml_string(self) -> str:
        return f'<let name="{self._attributes["name"]}" value="{self._attributes["value"]}" />'

    def get_parsed_element(self):
        return VariableParser().parse(self.get_xml_string())

    def test_correctness(self, parsed_element: Variable):
        assert parsed_element.name == self._attributes['name']
        assert parsed_element.value == self._attributes['value']
