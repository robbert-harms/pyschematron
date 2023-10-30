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

from pyschematron.direct_mode.ast import Schema, ConcretePattern, ConcreteRule, Variable, XMLVariable, \
    QueryVariable, Check, Assert, Report
from pyschematron.direct_mode.ast import Query as ASTQuery
from pyschematron.direct_mode.lib.ast_visitors import GetNodesOfTypeVisitor
from pyschematron.direct_mode.utils import reduce_schema_to_phase
from pyschematron.direct_mode.validators.queries.base import EvaluationContext, Query, QueryProcessor, QueryParser, \
    CachingQueryParser
from pyschematron.direct_mode.validators.queries.factories import SimpleQueryProcessorFactory
from pyschematron.direct_mode.validators.reports import SchematronValidationReport
from pyschematron.direct_mode.validators.utils import evaluate_variables
from pyschematron.direct_mode.validators.validation_results import CheckResult, RuleResult, PatternResult, NodeResult, \
    XMLResult, ValidationResult, MultiCheckResult


class SchematronXMLValidator(metaclass=ABCMeta):
    """Base class for all Schematron XML validators.

    Schematron XML validators must be able to validate an XML and return a validation report.
    """

    @abstractmethod
    def validate_xml(self, xml_document: ElementTree) -> SchematronValidationReport:
        """Validate the provided XML using this Schematron XML validator.

        Args:
            xml_document: the XML document to validate

        Returns:
            A Schematron validation report.
        """


class SimpleSchematronXMLValidator(SchematronXMLValidator):

    def __init__(self,
                 schema: Schema,
                 phase: str | Literal['#ALL', '#DEFAULT'] | None = None,
                 schematron_base_path: Path | None = None):
        """XML validation using a Schematron Schema.

        Args:
            schema: the Schema AST node. We will make the AST concrete if not yet done so.
            phase: the phase we want to evaluate. If None, we evaluate the default phase.
            schematron_base_path: the base path from which we loaded the Schematron file, provided for context.
        """
        self._schema = reduce_schema_to_phase(schema, phase)
        self._phase = phase
        self._schematron_base_path = schematron_base_path
        self._query_processor = SimpleQueryProcessorFactory().get_schema_query_processor(schema)

    def validate_xml(self, xml_document: ElementTree) -> SchematronValidationReport:
        validator = _XMLValidator(xml_document, self._schema, self._query_processor)
        xml_results = validator.validate()
        return xml_results


class SchematronElementValidator(metaclass=ABCMeta):

    @abstractmethod
    def validate(self, xml_node: ItemArgType) -> ValidationResult:
        """Validate the provided XML node.

        Args:
            xml_node: the node we want to validate

        Returns:
            The validation result of applying this validator.
        """


class BaseSchematronElementValidator(SchematronElementValidator, metaclass=ABCMeta):

    def __init__(self, query_parser: QueryParser, context: EvaluationContext):
        """Base implementation of a Schematron validator.

        This stores the parser and the evaluation context for use by the validation method.

        Args:
            query_parser: the parser we can use to parse queries in this element.
            context: the evaluation context prepared with the context variables
        """
        self._query_parser = query_parser
        self._context = context

    @property
    def query_parser(self) -> QueryParser:
        """Get a reference to the query parser used by this base validator.

        Returns:
            A reference to the query parser used
        """
        return self._query_parser

    @property
    def evaluation_context(self) -> EvaluationContext:
        """Get a reference to the evaluation context used by this base validator.

        Returns:
            A reference to the evaluation context used
        """
        return self._context


class _XMLValidator:

    def __init__(self, xml_document: ElementTree, schema: Schema, query_processor: QueryProcessor):
        """Validate the xml document using the Schematron Schema.

        Having this in a separate class enables encapsulation of the actual validation algorithm.

        This assumes the Schema has no more abstract rules or patterns left.

        Args:
            xml_document: the document we want to validate
            schema: the schema to use for validation
        """
        self._xml_document = xml_document
        self._xml_tree = get_node_tree(root=xml_document)
        self._schema = schema

        self._query_parser = CachingQueryParser(query_processor.get_query_parser())
        self._evaluation_context = query_processor.get_evaluation_context().with_xml_root(self._xml_tree)
        self._evaluation_context = self._evaluation_context.with_variables(
            evaluate_variables(self._schema.variables, self._query_parser, self._evaluation_context))

    def validate(self):
        node_results = []
        for node in self._xml_tree.iter():
            if not isinstance(node, TextNode):
                if node_result := self._validate_node(node):
                    node_results.append(node_result)

            if node.attributes:
                for attribute in node.attributes:
                    if node_result := self._validate_node(attribute):
                        node_results.append(node_result)
        return XMLResult(self._xml_tree, self._evaluation_context, node_results)

    def _validate_node(self, node: ItemArgType) -> NodeResult | None:
        """Validate the indicated XML node.

        Args:
            node: the XML node to validate using all the patterns in the Schematron

        Returns:
            Either None if no applicable results, or else the result of visiting the node.
        """
        if not node.parent:
            return None

        pattern_results = []
        for pattern in self._schema.patterns:
            if not isinstance(pattern, ConcretePattern):
                raise ValueError(f'Schema not concrete, ConcretePattern expected, {type(pattern)} received.')

            pattern_validator = PatternValidator(pattern, self._query_parser, self._evaluation_context)
            pattern_result = pattern_validator.validate(node)

            if pattern_result.had_active_rule():
                pattern_results.append(pattern_result)

        return NodeResult(node, self._evaluation_context, pattern_results)


# todo, also report rules that were shadowed by an earlier rule in a pattern


class PatternValidator(BaseSchematronElementValidator):

    def __init__(self, pattern: ConcretePattern, query_parser: QueryParser, context: EvaluationContext):
        """Apply a Schematron pattern to an XML node.

        This performs a context check against all the rule's contexts in this pattern. The first rule matching the
        xml node will be processed by the rule validator.

        Args:
            pattern: the Schematron pattern we would like to apply
            query_parser: the parser we can use to parse queries in the check.
            context: the evaluation context prepared with the context variables
        """
        context = context.with_variables(evaluate_variables(pattern.variables, query_parser, context))
        super().__init__(query_parser, context)
        self._pattern = pattern
        self._rule_validators = self._init_rule_validators()
        self._rule_context_queries = [self._query_parser.parse(rule.context.query) for rule in self._pattern.rules]

    def validate(self, xml_node: ItemArgType) -> PatternResult:
        rule_result = self._get_rule_result(xml_node)
        return PatternResult(xml_node, self._context, self._pattern, rule_result)

    def _get_rule_result(self, xml_node: ItemArgType) -> RuleResult | None:
        parent_context = self._context.with_context_item(xml_node.parent)

        for context_query, rule_validator in zip(self._rule_context_queries, self._rule_validators):
            if self._node_matches_context(xml_node, context_query, parent_context):
                return rule_validator.validate(xml_node)

    def _node_matches_context(self, node: ItemArgType, context_query: Query, parent_context: EvaluationContext) -> bool:
        """Check if the node we are investigating matches the context of a rule.

        We perform the check by querying the parent of the node for a match on the context of the rule.
        There may be multiple matches, as such we check if the node is within the matches. If so, the node
        must match the context query of the Schematron rule.

        Args:
            node: the node we are investigating
            context_query: the context query of a rule
            parent_context: an evaluation context specific to the parent of this node

        Returns:
            True if the node matches the rule, false otherwise.
        """
        if matches := context_query.evaluate(parent_context):
            if node in matches:
                return True
        return False

    def _init_rule_validators(self) -> list[RuleValidator]:
        """Initialize the rule validators.

        Returns:
            The list of rule validators obtained from the pattern
        """
        rule_validators = []
        for rule in self._pattern.rules:
            if not isinstance(rule, ConcreteRule):
                raise ValueError(f'Schema not concrete, ConcreteRule expected, {type(rule)} received.')

            rule_validators.append(RuleValidator(rule, self._query_parser, self._context))

        return rule_validators


class RuleValidator(BaseSchematronElementValidator):

    def __init__(self, rule: ConcreteRule, query_parser: QueryParser, context: EvaluationContext):
        """Apply a Schematron rule to an XML node.

        This will not perform a context check against the provided XML node. Rather, it always applies all the
        Schematron checks (assert and report) in this rule against the provided XML node. Any context evaluations
        must be done by the caller.

        Args:
            rule: the Schematron rule we would like to apply
            query_parser: the parser we can use to parse queries in the check.
            context: the evaluation context prepared with the context variables
        """
        super().__init__(query_parser, context)

        self._rule = rule

        rule_variables = evaluate_variables(self._rule.variables, self._query_parser, self._context)
        self._child_context = self._context.with_variables(rule_variables)

        self._check_validators = self._init_check_validators()

    def validate(self, xml_node: ItemArgType) -> RuleResult:
        check_results = []
        for check_validator in self._check_validators:
            check_results.append(check_validator.validate(xml_node))

        return RuleResult(xml_node, self._context, self._child_context, self._rule, check_results)

    def _init_check_validators(self) -> list[CheckValidator]:
        """Initialize the check validators.

        Returns:
            The list of check validators obtained from the rule
        """
        check_validators = []
        for check in self._rule.checks:
            if not isinstance(check, (Assert, Report)):
                raise ValueError(f'Each check should either be an Assert or Report node, {type(check)} received.')

            check_validators.append(CheckValidator(check, self._query_parser, self._child_context))

        return check_validators


class CheckValidator(BaseSchematronElementValidator):

    def __init__(self, check: Assert | Report, query_parser: QueryParser, context: EvaluationContext):
        """Validate an XML node using the indicated Schematron assert or report.

        Args:
            check: the check node to apply to the XML node
            query_parser: the parser we can use to parse queries in the check.
            context: the queries evaluation context, prepared with the context variables for this check
        """
        super().__init__(query_parser, context)
        self._check = check
        self._check_query = self._query_parser.parse(check.test.query)

    def validate(self, xml_node: ItemArgType) -> CheckResult:
        context = self._context.with_context_item(xml_node)

        check_result = self._check_query.evaluate(context)
        return CheckResult(xml_node, self._context, self._check, check_result)
