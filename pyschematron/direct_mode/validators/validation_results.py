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

from lxml.etree import ElementTree

from elementpath.xpath_context import ItemArgType, DocumentNode

from pyschematron.direct_mode.ast import ConcreteRule, Assert, Report, ConcretePattern, Schema
from pyschematron.direct_mode.validators.queries.base import EvaluationContext


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


@dataclass(slots=True, frozen=True)
class XMLInformation(ValidationResult):
    """Container for the knowledge of the XML being validated.

    This encapsulates the processing of all patterns over all nodes.

    Args:
        xml_document: the XML document provided as input
        xml_tree: xpath node wrapping the XML, this is the tree used during validation
    """
    xml_document: ElementTree
    xml_tree: DocumentNode


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
        xml_node: the node on which we are reporting the processing result
        evaluation_context: the context in which the node was processed.
            This should not be specialized to the context in which the node was processed. For example, for a processed
            pattern, this should be the "outside" evaluation context without the parameters inside the pattern.
    """
    xml_node: ItemArgType
    evaluation_context: EvaluationContext


@dataclass(slots=True, frozen=True)
class FullNodeResult(BaseXMLNodeResult):
    """Result class for the full evaluation of an XML node.

    This encapsulates the processing of all the patterns over the indicated XML node.

    Args:
        pattern_results: the results of all the patterns
    """
    pattern_results: tuple[PatternResult, ...]


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
    """
    check_results: list[CheckResult]

    def is_skipped(self) -> bool:
        return False

    def is_fired(self) -> bool:
        return True

    def is_suppressed(self) -> bool:
        return False


@dataclass(slots=True, frozen=True)
class CheckResult(BaseXMLNodeResult):
    """The result of checking a Schematron assert or report on an XML node.

    Args:
        check: the check which was run
        check_result: if the check passed or not
    """
    check: Assert | Report
    check_result: bool
