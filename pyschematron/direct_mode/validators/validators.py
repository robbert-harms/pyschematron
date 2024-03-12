from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Literal, Any

from elementpath import TextNode
from elementpath.tree_builders import get_node_tree
from elementpath.xpath_context import ItemArgType
from lxml.etree import ElementTree

from pyschematron.direct_mode.ast import (Schema, ConcretePattern, ConcreteRule, Variable,
                                          XMLVariable, QueryVariable, Assert, Report)
from pyschematron.direct_mode.lib.ast_visitors import (ResolveExtendsVisitor, ResolveAbstractPatternsVisitor,
                                                       PhaseSelectionVisitor)
from pyschematron.direct_mode.validators.queries.base import EvaluationContext, Query, QueryParser, CachingQueryParser
from pyschematron.direct_mode.validators.queries.factories import SimpleQueryProcessorFactory
from pyschematron.direct_mode.validators.validation_results import (CheckResult, RuleResult, PatternResult,
                                                                    FullNodeResult, XMLDocumentValidationResult,
                                                                    SuppressedRuleResult, FiredRuleResult,
                                                                    SkippedRuleResult)


class SchematronXMLValidator(metaclass=ABCMeta):
    """Base class for Schematron XML validators.

    Schematron XML validators are used to validate an XML and return a validation report.
    """

    @abstractmethod
    def validate_xml(self, xml_document: ElementTree) -> XMLDocumentValidationResult:
        """Validate the provided XML using this Schematron XML validator.

        Args:
            xml_document: the XML document to validate in an lxml `elementtree` object

        Returns:
            An XML document result containing the result of processing all patterns over all nodes.
        """


class SimpleSchematronXMLValidator(SchematronXMLValidator):

    def __init__(self,
                 schema: Schema,
                 phase: str | Literal['#ALL', '#DEFAULT'] | None = None,
                 schematron_base_path: Path | None = None):
        """XML validation using a Schematron Schema.

        Parsing is done into two phases. In the first phase we create a hierarchy of validator objects. These
        validator objects are not context aware until evaluation, they are prepared with a query parser for
        parsing the queries and are aware of the Schematron schema. During evaluation (e.g. after calling the method
        `validate_xml`), the entire hierarchy is called with the XML node under investigation, and an evaluation context
        object.

        Args:
            schema: the Schema AST node. We will make the AST concrete if not yet done so.
            phase: the phase we want to evaluate. If None, we evaluate the default phase.
            schematron_base_path: the base path from which we loaded the Schematron file, provided for context.
        """
        self._phase = phase
        self._schema = self._reduce_schema_to_phase(schema, self._phase)
        self._schematron_base_path = schematron_base_path
        self._query_processor = SimpleQueryProcessorFactory().get_schema_query_processor(schema)
        self._query_parser = CachingQueryParser(self._query_processor.get_query_parser())
        self._variable_evaluators = _get_variable_evaluators(self._schema.variables, self._query_parser)
        self._pattern_validators = self._get_pattern_validators()

    def validate_xml(self, xml_document: ElementTree) -> XMLDocumentValidationResult:
        xml_tree = get_node_tree(root=xml_document)

        root_context = self._query_processor.get_evaluation_context().with_xml_root(xml_tree)
        context = _get_context_with_variables(self._variable_evaluators, root_context)

        node_results = []
        for node in xml_tree.iter():
            if not node.parent:
                continue

            if not isinstance(node, TextNode):
                if node_result := self._validate_node(node, context):
                    node_results.append(node_result)

            if node.attributes:
                for attribute in node.attributes:
                    if node_result := self._validate_node(attribute, context):
                        node_results.append(node_result)

        return XMLDocumentValidationResult(xml_document, xml_tree, node_results)

    def _validate_node(self, node: ItemArgType, evaluation_context: EvaluationContext) -> FullNodeResult:
        """Validate the indicated XML node.

        Args:
            node: the XML node to validate using all the patterns in the Schematron
            evaluation_context: the context we use to parse the queries.

        Returns:
            Either None if no applicable results, or else the result of visiting the node.
        """
        pattern_results = []
        for pattern_validator in self._pattern_validators:
            pattern_results.append(pattern_validator.validate(node, evaluation_context))

        return FullNodeResult(node, evaluation_context, pattern_results)

    def _reduce_schema_to_phase(self, schema: Schema, phase: str | Literal['#ALL', '#DEFAULT'] | None = None) -> Schema:
        """Reduce an AST to only those patterns and phases referenced by a specific phase.

        This will first resolve all AST abstractions and afterward reduce the Schema to the phase selected.

        Reducing a Schema means selecting only those patterns and phases which fall within the selected phase.

        Args:
            schema: the Schema to resolve and reduce
            phase: the selected phase

        Returns:
            The resolved and reduced Schema
        """
        schema = self._resolve_ast_abstractions(schema)
        return PhaseSelectionVisitor(schema, phase=phase).apply(schema)

    @staticmethod
    def _resolve_ast_abstractions(schema: Schema) -> Schema:
        """Resolve all abstractions in a provided AST Schema node and return a Schema node without abstractions.

        This resolves the `extends` in the Rules, and resolves the abstract patterns.

        Args:
             schema: the Schema to resolve all abstractions in

        Returns:
            The Schema with the abstractions resolved.
        """
        schema = ResolveExtendsVisitor(schema).apply(schema)
        schema = ResolveAbstractPatternsVisitor(schema).apply(schema)
        return schema

    def _get_pattern_validators(self) -> list[_PatternValidator]:
        """Parse the patterns in the AST Schema and return a list of validators.

        Returns:
            A list of pattern validators.
        """
        pattern_validators = []
        for pattern in self._schema.patterns:
            if not isinstance(pattern, ConcretePattern):
                raise ValueError(f'Schema not concrete, ConcretePattern expected, {type(pattern)} received.')
            pattern_validators.append(_PatternValidator(self._query_parser, pattern))

        return pattern_validators


class _PatternValidator:

    def __init__(self, query_parser: QueryParser, pattern: ConcretePattern):
        """The Pattern validator validates an XML node against a pattern.

        Args:
            pattern: the Schematron pattern we would like to apply in the validation step.
            query_parser: the parser we can use to parse queries in the pattern.
        """
        self._query_parser = query_parser
        self._pattern = pattern
        self._variable_evaluators = _get_variable_evaluators(self._pattern.variables, self._query_parser)
        self._rule_validators: list[_RuleValidator] = self._get_rule_validators()

    def validate(self, xml_node: ItemArgType, evaluation_context: EvaluationContext) -> PatternResult:
        """Validate the XML node using the encapsulated pattern.

        For building the report, this will apply all the rules in the pattern against the provided XML node.
        According to Schematron, the first rule whose context matches the XML node will be used as the rule for that
        node within this pattern. Nevertheless, we apply all rules in order to build a comprehensive report.

        Args:
            xml_node: the node we are validating
            evaluation_context: the context to use for validation

        Returns:
            A report with the results of validating this pattern.
        """
        context = _get_context_with_variables(self._variable_evaluators, evaluation_context)

        nmr_fired_rules = 0
        rule_results = []
        for rule_validator in self._rule_validators:
            rule_result = rule_validator.validate(xml_node, context)

            if rule_result.is_fired():
                if nmr_fired_rules == 0:
                    rule_results.append(rule_result)
                else:
                    rule_results.append(SuppressedRuleResult.from_fired_rule_result(rule_result))
                nmr_fired_rules += 1
            else:
                rule_results.append(rule_result)

        return PatternResult(xml_node, evaluation_context, self._pattern, rule_results)

    def _get_rule_validators(self) -> list[_RuleValidator]:
        """Initialize the rule validators.

        Returns:
            The list of rule validators obtained from the pattern
        """
        rule_validators = []
        for rule in self._pattern.rules:
            if not isinstance(rule, ConcreteRule):
                raise ValueError(f'Schema not concrete, ConcreteRule expected, {type(rule)} received.')
            rule_validators.append(_RuleValidator(self._query_parser, rule))

        return rule_validators


class _RuleValidator:

    def __init__(self, query_parser: QueryParser, rule: ConcreteRule):
        """The Rule validator validates an XML node against a single rule.

        Args:
            rule: the Schematron rule we would like to apply in the validation step.
            query_parser: the parser we can use to parse queries in the pattern.
        """
        self._query_parser = query_parser
        self._rule = rule
        self._variable_evaluators = _get_variable_evaluators(self._rule.variables, self._query_parser)
        self._check_validators = self._get_check_validators()
        self._context_query = self._query_parser.parse(self._rule.context.query)

    def validate(self,
                 xml_node: ItemArgType,
                 evaluation_context: EvaluationContext) -> SkippedRuleResult | FiredRuleResult:
        """Validate the XML node using the encapsulated rule.

        This first checks if the context of the rule matches the XML node. If it matches we apply all the assertions
        and report checks in the rule. If it does not match we return the negative match as a result.

        Args:
            xml_node: the node we are validating
            evaluation_context: the context to use for validation

        Returns:
            A report with the results of validating this rule.
        """
        if not self._node_matches_context(xml_node, evaluation_context):
            return SkippedRuleResult(xml_node, evaluation_context, self._rule)

        context = _get_context_with_variables(self._variable_evaluators, evaluation_context)
        check_results = []
        for check_validator in self._check_validators:
            check_results.append(check_validator.validate(xml_node, context))

        return FiredRuleResult(xml_node, evaluation_context, self._rule, check_results)

    def _node_matches_context(self, xml_node: ItemArgType, evaluation_context: EvaluationContext) -> bool:
        """Check if the node we are investigating matches the context of a rule.

        We perform the check by querying the parent of the node for a match on the context of the rule.
        There may be multiple matches, as such we check if the node is within the matches. If so, the node
        must match the context query of the Schematron rule.

        Args:
            xml_node: the node we are investigating
            evaluation_context: the evaluation context. We will relativize this to the parent of the XML node.

        Returns:
            True if the node matches the rule, false otherwise.
        """
        parent_context = evaluation_context.with_context_item(xml_node.parent)

        if matches := self._context_query.evaluate(parent_context):
            if xml_node in matches:
                return True
        return False

    def _get_check_validators(self) -> list[_CheckValidator]:
        """Initialize the assert and report validators.

        Returns:
            The list of check validators obtained from the rule.
        """
        check_validators = []
        for check in self._rule.checks:
            if not isinstance(check, (Assert, Report)):
                raise ValueError(f'Each check should either be an Assert or Report node, {type(check)} received.')
            check_validators.append(_CheckValidator(self._query_parser, check))

        return check_validators


class _CheckValidator:

    def __init__(self, query_parser: QueryParser, check: Assert | Report):
        """Validate an XML node using the indicated Schematron assert or report.

        Args:
            query_parser: the parser we can use to parse queries in the check.
            check: the check node to apply to the XML node
        """
        self._query_parser = query_parser
        self._check = check
        self._check_query = self._query_parser.parse(check.test.query)

    def validate(self, xml_node: ItemArgType, evaluation_context: EvaluationContext) -> CheckResult:
        """Validate the XML node using the encapsulated check (report or assert).

        Args:
            xml_node: the node we are validating
            evaluation_context: the context to use for validation

        Returns:
            A report with the results of validating this check.
        """
        context = evaluation_context.with_context_item(xml_node)
        check_result = bool(self._check_query.evaluate(context))
        return CheckResult(xml_node, evaluation_context, self._check, check_result)


class _VariableEvaluator(metaclass=ABCMeta):
    """Representation of variables from the Schematron Schema with the ability to evaluate the query."""

    @abstractmethod
    def evaluate(self, context: EvaluationContext) -> Any:
        """Evaluate the parsed variable using the provided context.

        Args:
            context: the context we need to evaluate a query.
        """


class _StringVariableEvaluator(_VariableEvaluator):

    def __init__(self, value: str):
        """Representation of a string variable.

        Args:
            value: the string value
        """
        self._value = value

    def evaluate(self, context: EvaluationContext) -> str:
        return self._value


class _QueryVariableEvaluator(_VariableEvaluator):

    def __init__(self, value: Query):
        """Representation of a Query variable.

        Args:
            value: the query ready to be evaluated.
        """
        self._value = value

    def evaluate(self, context: EvaluationContext) -> Any:
        return self._value.evaluate(context)


def _get_variable_evaluators(variables: list[Variable], parser: QueryParser) -> dict[str, _VariableEvaluator]:
    """Parse a list of Schematron variables into evaluator objects.

    Args:
        variables: the AST variables we would like to parse.
        parser: the parser to use for parsing the queries.

    Returns:
        The parsed variables ready for evaluation.
    """
    results = {}
    for variable in variables:
        if isinstance(variable, QueryVariable):
            results[variable.name] = _QueryVariableEvaluator(parser.parse(variable.value.query))
        elif isinstance(variable, XMLVariable):
            results[variable.name] = _StringVariableEvaluator(variable.value)
    return results


def _get_context_with_variables(variable_evaluators: dict[str, _VariableEvaluator], context: EvaluationContext):
    """Update the provided context with the evaluated variables.

    This will evaluate the provided variable evaluators with the provided context and add the result of the
    variable evaluators to an updated context. Updating happens recursively since variables may refer to each other.
    It returns the updated context.

    Args:
        variable_evaluators: the evaluators for the various variables, indexed by name
        context: the context used to evaluate the variables. Will be updated with said variables and returned.

    Returns:
        The context updated with the variables.
    """
    updated_context = context
    for name, variable_evaluator in variable_evaluators.items():
        variable_value = variable_evaluator.evaluate(updated_context)
        updated_context = updated_context.with_variables({name: variable_value})

    return updated_context
