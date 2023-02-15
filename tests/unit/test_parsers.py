__author__ = 'Robbert Harms'
__date__ = '2023-01-25'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from abc import ABCMeta, abstractmethod
from typing import Union

from pytest_check import check

from pyschematron.elements import Report, Assert, Variable, Rule, SchematronElement, Pattern
from pyschematron.parser import ReportParser, AssertParser, VariableParser, RuleParser, PatternParser


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


class ParserTester(metaclass=ABCMeta):

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


class PatternTester(ParserTester):

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


class RuleTester(ParserTester):

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


class TestTester(ParserTester, metaclass=ABCMeta):

    def __init__(self, attributes: dict[str, str], content: str):
        self._attributes = attributes
        self._content = content

        self._attributes_to_kwargs = {
            'id': 'id',
            'diagnostics': 'diagnostics',
            'subject': 'subject',
            'role': 'role',
            'flag': 'flag',
            'see': 'see',
            'fpi': 'fpi',
            'icon': 'icon'
        }

    @classmethod
    def get_default(cls):
        """Get a default test case"""
        attributes = {
            'test': '//root',
            'id': 'some-id',
            'diagnostics': 'some-diagnostics',
            'subject': 'some-subject',
            'role': 'some-role',
            'flag': 'some-flag',
            'see': 'some-see',
            'fpi': 'some-fpi',
            'icon': 'some-icon'
        }
        return cls(attributes, '''
            String with <emph>bold text</emph>, a value: <value-of select="note/to/text()" />,
            <dir> reversed stuff</dir> and text at the end.
        ''')

    def test_correctness(self, parsed_element: Report):
        _check_parsed_attributes(parsed_element, self._attributes, self._attributes_to_kwargs)
        check.equal(parsed_element.content, self._content, "Check node content.")


class ReportTester(TestTester):

    def get_xml_string(self) -> str:
        attributes = ' '.join([f'{key}="{val}"' for key, val in self._attributes.items()])
        return f'<report {attributes}>{self._content}</report>'

    def get_parsed_element(self):
        return ReportParser().parse(self.get_xml_string())


class AssertTester(TestTester):

    def get_xml_string(self) -> str:
        attributes = ' '.join([f'{key}="{val}"' for key, val in self._attributes.items()])
        return f'<assert {attributes}>{self._content}</assert>'

    def get_parsed_element(self):
        return AssertParser().parse(self.get_xml_string())


class VariableTester(ParserTester):

    def __init__(self, attributes: dict[str, str]):
        self._attributes = attributes
        self._attributes_to_kwargs = {
            'name': 'name',
            'value': 'value'
        }

    @classmethod
    def get_default(cls):
        """Get a default test case"""
        return cls({'name': 'documents', 'value': '//root/documents'})

    def get_xml_string(self) -> str:
        attributes = ' '.join([f'{key}="{val}"' for key, val in self._attributes.items()])
        return f'<let {attributes} />'

    def get_parsed_element(self):
        return VariableParser().parse(self.get_xml_string())

    def test_correctness(self, parsed_element: Variable):
        _check_parsed_attributes(parsed_element, self._attributes, self._attributes_to_kwargs)


def _check_parsed_attributes(parsed_element: SchematronElement,
                             attributes: dict[str, str],
                             attributes_to_class: dict[str, str]) -> None:
    """Check if all attributes were successfully parsed.

    Args:
        parsed_element: the parsed and constructed element
        attributes: the XML attributes we used in the parsed XML string
        attributes_to_class: a mapping of XML attribute names to class attributes of the parsed Schematron element

    Returns:
        None, all checking is done in this function
    """
    for attr_name, class_val_name in attributes_to_class.items():
        attr_val = attributes.get(attr_name)
        class_val = getattr(parsed_element, class_val_name)
        check.equal(attr_val, class_val, f'Check parsing of XML attribute "{attr_name}" '
                                         f'to class variable {class_val_name}.')
