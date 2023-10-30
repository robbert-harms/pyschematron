from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-05-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from dataclasses import dataclass

from elementpath.xpath_context import ItemArgType

from pyschematron.direct_mode.ast import Check, Rule, ConcreteRule, Assert, Report, ConcretePattern
from pyschematron.direct_mode.validators.queries.base import EvaluationContext


@dataclass(slots=True, frozen=True)
class ValidationResult:
    """Base class for the validation results. """


@dataclass(slots=True, frozen=True)
class BaseValidationResult(ValidationResult):
    xml_node: ItemArgType
    evaluation_context: EvaluationContext


@dataclass(slots=True, frozen=True)
class XMLResult(BaseValidationResult):
    node_results: list[NodeResult]


@dataclass(slots=True, frozen=True)
class NodeResult(BaseValidationResult):
    pattern_results: list[PatternResult]


@dataclass(slots=True, frozen=True)
class PatternResult(BaseValidationResult):
    pattern: ConcretePattern
    rule_result: RuleResult | None

    # todo add shadowed rules

    def had_active_rule(self) -> bool:
        """Check if this pattern result had an active rule or not.

        Returns:
            True if there was an active rule in this pattern for the node, False otherwise
        """
        return self.rule_result is not None


@dataclass(slots=True, frozen=True)
class RuleResult(BaseValidationResult):
    """The result of checking the asserts and reports of a Rule on an XML node.

    Since a rule may contain variables, we have both a parent context and a child context. The parent context is
    without the variables loaded in this rule, the child context contains the variables.

    Args:
        child_context: the context in which children of this rule may be evaluated
        rule: a reference to the rule being checked
        check_results: the results of the checks
    """
    child_context: EvaluationContext
    rule: ConcreteRule
    check_results: list[CheckResult]


@dataclass(slots=True, frozen=True)
class CheckResult(BaseValidationResult):
    """The result of checking a Schematron assert or report on an XML node.

    Args:
        check: the check which was run
        check_result: if the check passed or not
    """
    check: Assert | Report
    check_result: bool
