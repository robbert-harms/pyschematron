__author__ = 'Robbert Harms'
__date__ = '2022-10-09'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pyschematron.elements import Variable, Phase, Pattern, Namespace, Schema, RuleMessage, Assert


class SchemaBuilder:

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


class AssertBuilder:

    def __init__(self):
        self.test: str = None
        self.message: RuleMessage = None
        self.is_report: bool = None
        self.id: str | None = None

    def build(self) -> Assert:
        """Build the Schema from all the information we have."""
        return Assert(self.test, self.message, self.is_report, self.id)

    def clear(self):
        """Clear the content of this builder."""
        self.test = None
        self.message = None
        self.is_report = None
        self.id = None

    def set_test(self, test: str):
        """Set the test condition.

        Args:
            test: the test condition
        """
        self.test = test

    def set_message(self, message: RuleMessage):
        """Set the assertion message.

        Args:
            message: the assertion message
        """
        self.message = message

    def set_report_switch(self, is_report: bool):
        """Set the report switch.

        Args:
            is_report: if this assertion is part of a report
        """
        self.is_report = is_report

    def set_id(self, id: str):
        """Set the id of this assertion.

        Args:
            id: the ID of this assertion
        """
        self.id = id
