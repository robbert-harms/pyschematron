from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-05-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from lxml.etree import _ElementTree

from pyschematron.direct_mode.schematron.ast import ConcreteRule, Assert, Report, ConcretePattern, Schema
from pyschematron.direct_mode.xml_validation.queries.base import EvaluationContext
from pyschematron.direct_mode.xml_validation.results.xml_nodes import XMLNode


@dataclass(slots=True, frozen=True)
class ValidationResult:
    """Type class for the validation results. """


@dataclass(slots=True, frozen=True)
class XMLDocumentValidationResult(ValidationResult):
    """Result class for the full evaluation of the entire XML document.

    This encapsulates the processing of all patterns over all nodes.

    Args:
        xml_information: the knowledge of the XML
        schema_information: information about the applied Schema
        node_results: the results over all nodes
    """
    xml_information: XMLInformation
    schema_information: SchemaInformation
    node_results: tuple[FullNodeResult, ...]

    def is_valid(self) -> bool:
        """Return True if the XML document was considered valid, False otherwise.

        According to the specifications, a successful report is considered a failure. As such, this method considers
        an XML document to be valid if none of the assertions and none of the reports were raised.

        Returns:
            True if the document passed the Schematron validation, False otherwise.
        """
        for node_result in self.node_results:
            if not node_result.is_valid():
                return False
        return True


@dataclass(slots=True, frozen=True)
class XMLInformation(ValidationResult):
    """Container for the knowledge of the XML being validated.

    This encapsulates the processing of all patterns over all nodes.

    Args:
        xml_document: the XML document provided as input
    """
    xml_document: _ElementTree


@dataclass(slots=True, frozen=True)
class SchemaInformation(ValidationResult):
    """Container for the information of the Schematron used during validation.

    Args:
        schema: the Schema AST node used during evaluation
        phase: the phase used in evaluation
        schematron_base_path: the base path from which we loaded the Schematron file, provided for context.
    """
    schema: Schema
    phase: str | Literal['#ALL', '#DEFAULT'] | None = None,
    schematron_base_path: Path | None = None


@dataclass(slots=True, frozen=True)
class BaseXMLNodeResult(ValidationResult):
    """Base class for the result of processing a specific XML node.

    Args:
        xml_node: the node on which we are reporting the processing result.
        evaluation_context: the context in which the node was processed.
            This should not be specialized to the context in which the node was processed. For example, for a processed
            pattern, this should be the "outside" evaluation context without the parameters inside the pattern.
    """
    xml_node: XMLNode
    evaluation_context: EvaluationContext


@dataclass(slots=True, frozen=True)
class FullNodeResult(BaseXMLNodeResult):
    """Result class for the full evaluation of an XML node.

    This encapsulates the processing of all the patterns over the indicated XML node.

    Args:
        pattern_results: the results of all the patterns
    """
    pattern_results: tuple[PatternResult, ...]

    def is_valid(self) -> bool:
        """Return True if all patterns yielded a valid results, False otherwise.

        Returns:
            True if the document passed the Schematron validation, False otherwise.
        """
        for pattern_result in self.pattern_results:
            if not pattern_result.is_valid():
                return False
        return True


@dataclass(slots=True, frozen=True)
class PatternResult(BaseXMLNodeResult):
    """Result class for evaluating a pattern on a node.

    Args:
        pattern: a reference to the evaluated pattern
        rule_results: a list of the rule results for each rule in the pattern.
    """
    pattern: ConcretePattern
    rule_results: tuple[RuleResult, ...]

    def has_fired_rule(self) -> bool:
        """Check if this pattern result has a fired rule or not.

        Returns:
            True if there was an active rule in this pattern for the node, False otherwise
        """
        return any(result.is_fired() for result in self.rule_results)

    def is_valid(self) -> bool:
        """Return True if all rules yielded a valid results, False otherwise.

        Returns:
            True if the document passed the Schematron validation, False otherwise.
        """
        for rule_result in self.rule_results:
            if isinstance(rule_result, FiredRuleResult):
                if not rule_result.is_valid():
                    return False
        return True


@dataclass(slots=True, frozen=True)
class RuleResult(BaseXMLNodeResult, metaclass=ABCMeta):
    """Base class for skipped, fired, and suppressed rules.

    Since we process all rules we need a way to indicate if a rule was skipped, fired, or suppressed.
    This base class creates a base type for the different rule results.

    Args:
        rule: the rule which was processed
    """
    rule: ConcreteRule

    @abstractmethod
    def is_skipped(self) -> bool:
        """Check if this rule was skipped or not.

        Returns:
            True if the rule was skipped, False otherwise
        """

    @abstractmethod
    def is_fired(self) -> bool:
        """Check if this rule was fired or not.

        Returns:
            True if the rule was fired, False otherwise
        """

    @abstractmethod
    def is_suppressed(self) -> bool:
        """Check if this rule was suppressed or not.

        Returns:
            True if the rule was suppressed, False otherwise
        """


@dataclass(slots=True, frozen=True)
class SkippedRuleResult(RuleResult):
    """Indicates the result of a rule which was skipped because the context did not match."""

    def is_skipped(self) -> bool:
        return True

    def is_fired(self) -> bool:
        return False

    def is_suppressed(self) -> bool:
        return False


@dataclass(slots=True, frozen=True)
class SuppressedRuleResult(RuleResult):
    """Indicates the result of a rule which was shadowed by a preceding rule."""

    @classmethod
    def from_fired_rule_result(cls, fired_rule_result: FiredRuleResult):
        """Generated a suppressed rule result from the result of a fired rule.

        This is a convenience method to turn a fired rule in a suppressed rule.

        Args:
            fired_rule_result: the fired result we would like to transform
        """
        return cls(fired_rule_result.xml_node, fired_rule_result.evaluation_context, fired_rule_result.rule)

    def is_skipped(self) -> bool:
        return False

    def is_fired(self) -> bool:
        return False

    def is_suppressed(self) -> bool:
        return True


@dataclass(slots=True, frozen=True)
class FiredRuleResult(RuleResult):
    """The result of checking the asserts and reports of a Rule on an XML node.

    Args:
        check_results: the results of the checks
        subject_node: the node referenced by the subject attribute of the Schematron rule.
    """
    check_results: list[CheckResult]
    subject_node: XMLNode | None

    def is_skipped(self) -> bool:
        return False

    def is_fired(self) -> bool:
        return True

    def is_suppressed(self) -> bool:
        return False

    def is_valid(self) -> bool:
        """Return True if all checks yielded a valid results, False otherwise.

        Returns:
            True if the document passed the Schematron validation, False otherwise.
        """
        for check_result in self.check_results:
            if check_result.check_result:
                return False
        return True


@dataclass(slots=True, frozen=True)
class CheckResult(BaseXMLNodeResult):
    """The result of checking a Schematron assert or report on an XML node.

    The test result stored in this class represents if the test in the check was true or false. As such,
    it is independent on the nature of the check. A false test result for an assertion means a failure, which will be
    reported, while only a true test result for a report is reported. If you want this derived message, use the
    dynamic check result property.

    Args:
        check: the check which was run
        test_result: the result of the test in the check.
        text: the text result from the rich text content.
        subject_node: the node referenced by the subject attribute of the Schematron check.
    """
    check: Assert | Report
    test_result: bool
    text: str
    subject_node: XMLNode | None
    property_results: tuple[PropertyResult, ...] | None = None
    diagnostic_results: tuple[DiagnosticResult, ...] | None = None

    @property
    def check_result(self) -> bool:
        """Get the result of the check.

        In Schematron, tests can be written in one of two ways:

            <sch:assert> outputs a message if an XPath test evaluates to false.
            <sch:report> outputs a message if an XPath test evaluates to true.

        The test result stored in this class represents the state of the test result, not the final outcome
        of the check. For that, there is this method.

        This checks if the result was a pass or not, it returns a value based on the following combinations:

        +--------+-------------+--------------+
        |  Check | Test result | Return value |
        +========+=============+==============+
        | Assert | true        | false        |
        | Assert | false       | true         |
        | Report | true        | true         |
        | Report | false       | false        |
        +--------+-------------+--------------+

        Returns:
            If the return value is true, we are either dealing with a failed assert, or a successful report.
            If the return value is false, we have a successful assert, or a failed report.
        """
        if isinstance(self.check, Assert):
            return not self.test_result
        else:
            return self.test_result


@dataclass(slots=True, frozen=True)
class PropertyResult(ValidationResult):
    """Result of evaluating a property indicated by a check.

    Args:
        text: resulting text
        property_id: identifier of this property
        role: the role attribute for this property, copied from the properties' role attribute
        scheme: the scheme attribute for this property, copied from the properties' scheme attribute
    """
    text: str
    property_id: str
    role: str | None = None
    scheme: str | None = None


@dataclass(slots=True, frozen=True)
class DiagnosticResult(ValidationResult):
    """Result of evaluating a diagnostic indicated by a check.

    Args:
        text: resulting text
        diagnostic_id: identifier of this diagnostic
        xml_lang: the xml language attribute for this diagnostic
        xml_space: the xml_space attribute from the diagnostic
    """
    text: str
    diagnostic_id: str
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None
