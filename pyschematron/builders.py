from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-09'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta, abstractmethod
from copy import copy
from lxml import etree
from pyschematron.elements import Variable, Phase, Pattern, Namespace, Schema, RuleMessage, Assert, Test, Report, \
    Rule, SchematronElement


class SchematronElementBuilder(metaclass=ABCMeta):
    """Builder pattern for constructing Schematron element classes."""

    @abstractmethod
    def build(self) -> SchematronElement:
        """Build a Schematron element based on the information in this builder.

        Returns:
            The constructed schematron element.
        """

    @abstractmethod
    def clear(self):
        """Clear the content of this builder."""


class SchemaBuilder(SchematronElementBuilder):

    def __init__(self):
        """Builder pattern for the Schema element."""
        self.variables: list[Variable] = []
        self.phases: list[Phase] = []
        self.patterns: list[Pattern] = []
        self.namespaces: list[Namespace] = []
        self.title: str | None = None
        self.default_phase: str | None = None

    def build(self) -> Schema:
        """Build the Schema from all the information we have."""
        return Schema(self.variables, self.phases, self.patterns,
                      self.namespaces, self.title, self.default_phase)

    def clear(self):
        """Clear the content of this builder."""
        self.variables = []
        self.phases = []
        self.patterns = []
        self.namespaces = []
        self.title = None
        self.default_phase = None

    def add_variable(self, variable: Variable):
        """Add a variable to this builder.

        Args:
            variable: the variable to add
        """
        self.variables.append(variable)

    def add_phase(self, phase: Phase):
        """Add a phase to this builder.

        Args:
            phase: the phase to add
        """
        self.phases.append(phase)

    def add_pattern(self, pattern: Pattern):
        """Add a pattern to this builder.

        Args:
            pattern: the pattern to add
        """
        self.patterns.append(pattern)

    def add_namespace(self, namespace: Namespace):
        """Add a namespace to this builder.

        Args:
            namespace: the namespace to add
        """
        self.namespaces.append(namespace)

    def set_title(self, title: str | None):
        """Set the title to the provided value.

        Args:
            title: the new title for the Schema element
        """
        self.title = title

    def set_default_phase(self, default_phase: str | None):
        """Set the default phase to the provided value.

        Args:
            default_phase: the new default phase for the Schema element
        """
        self.default_phase = default_phase


class RuleBuilder(SchematronElementBuilder):

    def __init__(self):
        """Builder class for building Rule tags."""
        self.context: str = ''
        self.rule_elements: list[Test] = []
        self.variables: list[Variable] = []

    def build(self) -> Rule:
        """Build the Rule with all the information we have.

        Returns:
            The build Rule
        """
        return Rule(self.context, self.rule_elements, self.variables)

    def clear(self):
        self.context = ''
        self.rule_elements = []
        self.variables = []

    def set_context(self, context: str):
        """Set the context attribute.

        Args:
            context: the context string
        """
        self.context = context

    def add_rule_element(self, rule_element: Test):
        """Add a rule element (assert or report).

        Args:
            rule_element: the rule element to add
        """
        self.rule_elements.append(rule_element)


class TestBuilder(SchematronElementBuilder, metaclass=ABCMeta):

    def __init__(self):
        """Base class for building test elements (assert and report)."""
        self.test: str = ''
        self.message_parts = []
        self.id: str | None = None

    @abstractmethod
    def build(self) -> Test:
        """Build the rule element with all the information we have.

        Returns:
            The specific rule element as dictated by the subclass.
        """

    def clear(self):
        """Clear the content of this builder."""
        self.test = None
        self.message_parts = []
        self.id = None

    def set_test(self, test: str):
        """Set the test condition.

        Args:
            test: the test condition
        """
        self.test = test

    def add_message_part(self, message_part: str | etree.Element):
        """Add a part of the message.

        This allows constructing the message from one or more string and XML elements

        Args:
             message_part: the message part to append
        """
        self.message_parts.append(message_part)

    def prepend_message_part(self, message_part: str | etree.Element):
        """Insert a message part at the beginning of the parts.

        Args:
            message_part: the message part to put in front of all the others
        """
        self.message_parts.insert(0, message_part)

    def set_message_parts(self, message_parts: list[str | etree.Element]):
        """Set the entire message parts to this data.

        This overwrites the current list.

        Args:
            message_parts: the message parts which form this rule element.
        """
        self.message_parts = copy(message_parts)

    def set_id(self, id: str):
        """Set the id of this assertion.

        Args:
            id: the ID of this assertion
        """
        self.id = id


class AssertBuilder(TestBuilder):

    def build(self) -> Assert:
        return Assert(self.test, RuleMessage(self.message_parts), self.id)


class ReportBuilder(TestBuilder):

    def build(self) -> Report:
        return Report(self.test, RuleMessage(self.message_parts), self.id)
