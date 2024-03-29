__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from abc import ABCMeta, abstractmethod

from pyschematron.direct_mode.ast import SchematronASTNode, Check, Variable, Paragraph, Extends, ConcreteRule, \
    ExternalRule, AbstractRule, Query, Rule, ConcretePattern, Pattern, Namespace, Schema, Title, AbstractPattern, \
    InstancePattern, PatternParameter, Phase, ActivePhase, Diagnostics, Properties
from pyschematron.direct_mode.parsers.xml.utils import parse_attributes


class SchematronASTNodeBuilder(metaclass=ABCMeta):
    """Builder pattern for delayed construction of Schematron nodes."""

    @abstractmethod
    def build(self) -> SchematronASTNode:
        """Build a Schematron node based on the information in this builder.

        Returns:
            The constructed schematron element.
        """


class RuleBuilder(SchematronASTNodeBuilder, metaclass=ABCMeta):

    def __init__(self):
        """Construct a Rule node out of the parts provided.

        Can not be used directly, one needs to use one of the specialized subclasses.
        """
        self.checks: list[Check] = []
        self.variables: list[Variable] = []
        self.paragraphs: list[Paragraph] = []
        self.extends: list[Extends] = []
        self.attributes = {}

    def add_checks(self, nodes: list[Check]):
        """Add a list of Check nodes (Report or Assert).

        Args:
            nodes: the nodes to add to the list of checks.
        """
        self.checks.extend(nodes)

    def add_variables(self, nodes: list[Variable]):
        """Add a list of Variable nodes.

        Args:
            nodes: the nodes to add to the list of variables.
        """
        self.variables.extend(nodes)

    def add_paragraphs(self, nodes: list[Paragraph]):
        """Add a list of Paragraph nodes.

        Args:
            nodes: the nodes to add to the list of paragraphs.
        """
        self.paragraphs.extend(nodes)

    def add_extends(self, nodes: Extends):
        """Add a list of extends nodes.

        Args:
            nodes: the nodes to add to the list of extends
        """
        self.extends.extend(nodes)

    def add_attributes(self, element_attributes: dict[str, str]):
        """Add all the attributes of the XML Rule element in one go.

        Args:
            element_attributes: dictionary of attributes taken from the XML node
        """
        allowed_attributes = ['context', 'subject', 'flag', 'fpi', 'icon', 'id', 'role', 'see',
                              '{http://www.w3.org/XML/1998/namespace}lang',
                              '{http://www.w3.org/XML/1998/namespace}space']

        attribute_handlers = {
            'context': lambda k, v: {k: Query(v)},
            'subject': lambda k, v: {k: Query(v)},
            '{http://www.w3.org/XML/1998/namespace}lang': lambda k, v: {'xml_lang': v},
            '{http://www.w3.org/XML/1998/namespace}space': lambda k, v: {'xml_space': v}
        }

        attributes = parse_attributes(element_attributes, allowed_attributes, attribute_handlers)
        self.attributes.update(attributes)


class ConcreteRuleBuilder(RuleBuilder):

    def build(self) -> ConcreteRule:
        if 'context' not in self.attributes:
            raise ValueError('A concrete rule must have a context.')

        return ConcreteRule(checks=self.checks, variables=self.variables,
                            paragraphs=self.paragraphs, extends=self.extends, **self.attributes)


class AbstractRuleBuilder(RuleBuilder):

    def build(self) -> AbstractRule:
        if 'context' in self.attributes:
            raise ValueError('An abstract rule can not have a context.')

        if 'id' not in self.attributes:
            raise ValueError('An abstract rule must have an id.')

        return AbstractRule(checks=self.checks, variables=self.variables,
                            paragraphs=self.paragraphs, extends=self.extends, **self.attributes)


class ExternalRuleBuilder(RuleBuilder):

    def build(self) -> ExternalRule:
        if 'context' in self.attributes:
            raise ValueError('An external rule can not have a context.')

        return ExternalRule(checks=self.checks, variables=self.variables,
                            paragraphs=self.paragraphs, extends=self.extends, **self.attributes)


class PatternBuilder(SchematronASTNodeBuilder, metaclass=ABCMeta):

    def __init__(self):
        """Construct a Pattern node out of the parts provided.

        Can not be used directly, one needs to use one of the specialized subclasses.
        """
        self.rules: list[Rule] = []
        self.variables: list[Variable] = []
        self.title: Title | None = None
        self.paragraphs: list[Paragraph] = []
        self.pattern_parameters: list[PatternParameter] = []
        self.attributes = {}

    def add_rules(self, nodes: list[Rule]):
        """Add a list of Rule nodes

        Args:
            nodes: the nodes to add to the list of checks.
        """
        self.rules.extend(nodes)

    def add_variables(self, nodes: list[Variable]):
        """Add a list of Variable nodes.

        Args:
            nodes: the nodes to add to the list of variables.
        """
        self.variables.extend(nodes)

    def set_title(self, node: Title | None):
        """Set the title node.

        Args:
            node: the title node
        """
        self.title = node

    def add_paragraphs(self, nodes: list[Paragraph]):
        """Add a list of Paragraph nodes.

        Args:
            nodes: the nodes to add to the list of paragraphs.
        """
        self.paragraphs.extend(nodes)

    def add_parameters(self, nodes: list[PatternParameter]):
        """Add a list of PatternParameter nodes.

        Args:
            nodes: the nodes to add to the list of parameters.
        """
        self.pattern_parameters.extend(nodes)

    def add_attributes(self, element_attributes: dict[str, str]):
        """Add all the attributes of the XML Pattern element in one go.

        Args:
            element_attributes: dictionary of attributes taken from the XML node
        """
        allowed_attributes = ['documents', 'fpi', 'icon', 'id', 'see', 'is-a',
                              '{http://www.w3.org/XML/1998/namespace}lang',
                              '{http://www.w3.org/XML/1998/namespace}space']

        attribute_handlers = {
            'documents': lambda k, v: {k: Query(v)},
            'is-a': lambda k, v: {'abstract_id_ref': v},
            '{http://www.w3.org/XML/1998/namespace}lang': lambda k, v: {'xml_lang': v},
            '{http://www.w3.org/XML/1998/namespace}space': lambda k, v: {'xml_space': v}
        }

        attributes = parse_attributes(element_attributes, allowed_attributes, attribute_handlers)
        self.attributes.update(attributes)


class ConcretePatternBuilder(PatternBuilder):

    def build(self) -> ConcretePattern:
        return ConcretePattern(rules=self.rules, variables=self.variables, paragraphs=self.paragraphs,
                               title=self.title, **self.attributes)


class AbstractPatternBuilder(PatternBuilder):

    def build(self) -> AbstractPattern:
        return AbstractPattern(rules=self.rules, variables=self.variables, paragraphs=self.paragraphs,
                               title=self.title, **self.attributes)


class InstancePatternBuilder(PatternBuilder):

    def build(self) -> InstancePattern:
        return InstancePattern(params=self.pattern_parameters, **self.attributes)


class PhaseBuilder(SchematronASTNodeBuilder):

    def __init__(self):
        """Construct a Phase node out of the parts provided."""
        self.active: list[ActivePhase] = []
        self.variables: list[Variable] = []
        self.paragraphs: list[Paragraph] = []
        self.attributes = {}

    def build(self) -> Phase:
        return Phase(active=self.active, variables=self.variables, paragraphs=self.paragraphs, **self.attributes)

    def add_active(self, nodes: list[ActivePhase]):
        """Add a list of ActivePhase nodes

        Args:
            nodes: the nodes to add to the list of active phases.
        """
        self.active.extend(nodes)

    def add_variables(self, nodes: list[Variable]):
        """Add a list of Variable nodes.

        Args:
            nodes: the nodes to add to the list of variables.
        """
        self.variables.extend(nodes)

    def add_paragraphs(self, nodes: list[Paragraph]):
        """Add a list of Paragraph nodes.

        Args:
            nodes: the nodes to add to the list of paragraphs.
        """
        self.paragraphs.extend(nodes)

    def add_attributes(self, element_attributes: dict[str, str]):
        """Add all the attributes of the XML Pattern element in one go.

        Args:
            element_attributes: dictionary of attributes taken from the XML node
        """
        allowed_attributes = ['fpi', 'icon', 'id', 'see',
                              '{http://www.w3.org/XML/1998/namespace}lang',
                              '{http://www.w3.org/XML/1998/namespace}space']

        attribute_handlers = {
            '{http://www.w3.org/XML/1998/namespace}lang': lambda k, v: {'xml_lang': v},
            '{http://www.w3.org/XML/1998/namespace}space': lambda k, v: {'xml_space': v}
        }

        attributes = parse_attributes(element_attributes, allowed_attributes, attribute_handlers)
        self.attributes.update(attributes)


class SchemaBuilder(SchematronASTNodeBuilder):

    def __init__(self):
        """Construct a Schema node out of the parts provided."""
        self.patterns: list[Pattern] = []
        self.namespaces: list[Namespace] = []
        self.diagnostics: list[Diagnostics] = []
        self.properties: list[Properties] = []
        self.title: Title | None = None
        self.variables: list[Variable] = []
        self.paragraphs: list[Paragraph] = []
        self.phases: list[Phase] = []
        self.attributes = {}

    def build(self) -> Schema:
        return Schema(patterns=self.patterns, namespaces=self.namespaces, phases=self.phases,
                      paragraphs=self.paragraphs, variables=self.variables,
                      diagnostics=self.diagnostics, properties=self.properties, title=self.title,
                      **self.attributes)

    def add_patterns(self, nodes: list[Pattern]):
        """Add a list of Pattern nodes

        Args:
            nodes: the nodes to add to the list of patterns.
        """
        self.patterns.extend(nodes)

    def add_namespaces(self, nodes: list[Namespace]):
        """Add a list of Namespace nodes

        Args:
            nodes: the nodes to add to the list of namespaces.
        """
        self.namespaces.extend(nodes)

    def add_phases(self, nodes: list[Phase]):
        """Add a list of Phase nodes

        Args:
            nodes: the nodes to add to the list of phases.
        """
        self.phases.extend(nodes)

    def add_diagnostics(self, nodes: list[Diagnostics]):
        """Add a list of Diagnostics nodes

        Args:
            nodes: the nodes to add to the list of diagnostics.
        """
        self.diagnostics.extend(nodes)

    def add_properties(self, nodes: list[Properties]):
        """Add a list of Properties nodes

        Args:
            nodes: the nodes to add to the list of properties.
        """
        self.properties.extend(nodes)

    def add_variables(self, nodes: list[Variable]):
        """Add a list of Variable nodes.

        Args:
            nodes: the nodes to add to the list of variables.
        """
        self.variables.extend(nodes)

    def add_paragraphs(self, nodes: list[Paragraph]):
        """Add a list of Paragraph nodes.

        Args:
            nodes: the nodes to add to the list of paragraphs.
        """
        self.paragraphs.extend(nodes)

    def set_title(self, node: Title | None):
        """Set the title node.

        Args:
            node: the title node
        """
        self.title = node

    def add_attributes(self, element_attributes: dict[str, str]):
        """Add all the attributes of the XML Schema element in one go.

        Args:
            element_attributes: dictionary of attributes taken from the XML node
        """
        allowed_attributes = ['defaultPhase', 'fpi', 'icon', 'id',
                              'queryBinding', 'schemaVersion', 'see',
                              '{http://www.w3.org/XML/1998/namespace}lang',
                              '{http://www.w3.org/XML/1998/namespace}space']

        attribute_handlers = {
            'defaultPhase': lambda k, v: {'default_phase': v},
            'queryBinding': lambda k, v: {'query_binding': v},
            'schemaVersion': lambda k, v: {'schema_version': v},
            '{http://www.w3.org/XML/1998/namespace}lang': lambda k, v: {'xml_lang': v},
            '{http://www.w3.org/XML/1998/namespace}space': lambda k, v: {'xml_space': v}
        }

        attributes = parse_attributes(element_attributes, allowed_attributes, attribute_handlers)
        self.attributes.update(attributes)
