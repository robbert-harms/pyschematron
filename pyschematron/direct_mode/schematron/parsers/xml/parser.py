__author__ = 'Robbert Harms'
__date__ = '2023-02-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

import os
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import override

import elementpath

from lxml import etree
from lxml.etree import Element

from pyschematron.direct_mode.schematron.ast import Schema, Check, Assert, SchematronASTNode, Pattern, Rule, Report, \
    Variable, \
    Paragraph, ExtendsById, Extends, ExtendsExternal, ExternalRule, Query, QueryVariable, XMLVariable, \
    Namespace, Title, PatternParameter, ValueOf, Name, Phase, ActivePhase, Diagnostic, Diagnostics, Properties, \
    Property, XPathExpression
from pyschematron.direct_mode.schematron.parsers.xml.builders import ConcreteRuleBuilder, ExternalRuleBuilder, \
    AbstractRuleBuilder, ConcretePatternBuilder, SchemaBuilder, AbstractPatternBuilder, \
    InstancePatternBuilder, PhaseBuilder
from pyschematron.direct_mode.schematron.parsers.xml.utils import node_to_str, resolve_href, parse_attributes
from pyschematron.utils import load_xml_document


class ParserFactory(metaclass=ABCMeta):
    """Create a parser for parsing a specific XML element into an AST node.

    By using a factory method we allow subclassing the :class:`SchematronASTNode` elements and have a
    dedicated parser for such new subclasses without having to subclass a deep class hierarchy.

    For example, suppose you subclass the element "Assert" as "MyAssert" with some additional attributes.
    When parsing, you could reuse most of the parsing code by providing the factory with::

        {'assert': MyAssertParser()}

    Where `MyAssertParser` is a parser returning your subclassed "MyAssert" instead of "Assert".
    """

    @abstractmethod
    def get_parser(self, xml_tag: str) -> "ElementParser":
        """Get the parser for a specific Schematron XML tag.

        Args:
            xml_tag: the xml tag for which we want to get the parser

        Returns:
            A parser for the specific XML tag
        """


class DefaultParserFactory(ParserFactory):
    """The default parser factory.

    For each Schematron element, this returns the standard parser from this library.
    """

    def __init__(self):
        self.parsers = {
            'schema': SchemaParser(),
            'ns': NamespaceParser(),
            'phase': PhaseParser(),
            'active': ActivePhaseParser(),
            'pattern': PatternParser(),
            'rule': RuleParser(),
            'assert': AssertParser(),
            'report': ReportParser(),
            'extends': ExtendsParser(),
            'param': PatternParameterParser(),
            'diagnostics': DiagnosticsParser(),
            'diagnostic': DiagnosticParser(),
            'properties': PropertiesParser(),
            'property': PropertyParser(),
            'name': NameParser(),
            'value-of': ValueOfParser(),
            'let': VariableParser(),
            'p': ParagraphParser(),
            'title': TitleParser(),
            'include': IncludeParser(),
        }

    def get_parser(self, xml_tag: str) -> "ElementParser":
        return self.parsers[xml_tag]


class ParsingContext:

    def __init__(self, parser_factory: ParserFactory = None, base_path: Path = None):
        """Create the parser context we use while parsing the Schematron XML into the AST.

        Args:
            parser_factory: the factory we use to create sub parsers, defaults to :class:`DefaultParserFactory`.
            base_path: the base path to use for file inclusions, if not provided it is set to the current working
                directory.
        """
        self.parser_factory = parser_factory or DefaultParserFactory()
        self.base_path = base_path or os.getcwd()


class ElementParser(metaclass=ABCMeta):

    @abstractmethod
    def parse(self, element: Element, context: ParsingContext | None = None) -> SchematronASTNode:
        """Parse a piece of XML data into a SchematronASTNode.

        Args:
            element: the Schematron XML element we want to parse
            context: the context we use for parsing this Schematron XML element. If not set, we load a default parser.
        """

    @staticmethod
    def _parse_child_tags[T: Element](element: T, context: ParsingContext, xml_tag: str) -> list[T]:
        """Parse a sequence of XML elements with the same tag name.

        Args:
            element: the element which we search
            context: the parsing context
            xml_tag: the XML tag to search for
        """
        parser = context.parser_factory.get_parser(xml_tag)

        items = []
        for child in elementpath.select(element, xml_tag, namespaces={'': 'http://purl.oclc.org/dsdl/schematron'}):
            items.append(parser.parse(child, context))

        return items

    @staticmethod
    def get_rich_content(element: Element,
                         context: ParsingContext,
                         parse_special: bool = True,
                         remove_namespaces: bool = True) -> tuple[str | ValueOf | Name, ...]:
        """Get the rich content of the provided node.

        Args:
            element: the element for which to get the content.
            context: the parsing context
            parse_special: if set to True, we separate the strings and the special variables (ValueOf, Name).
                If set to false we return only string contents.
            remove_namespaces: if we want to remove the namespaces from the string rendered children

        Returns:
            A listing of text and special item nodes. All rich content like <emph> and <b> are rendered
            as string content. If parse special is True, Nodes of type <value-of> and <name> are parsed
            to ValueOf and Name.
        """
        content = [element.text]

        for child in element.getchildren():
            if parse_special and child.tag == '{http://purl.oclc.org/dsdl/schematron}value-of':
                parser = context.parser_factory.get_parser('value-of')
                content.append(parser.parse(child, context))
            elif parse_special and child.tag == '{http://purl.oclc.org/dsdl/schematron}name':
                parser = context.parser_factory.get_parser('name')
                content.append(parser.parse(child, context))
            else:
                content.append(node_to_str(child, remove_namespaces=remove_namespaces))
            content.append(child.tail)

        return tuple(el for el in content if el)


class SchemaParser(ElementParser):
    """Parse <schema> root tags"""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Schema:
        context = context or ParsingContext()

        builder = SchemaBuilder()
        builder.add_attributes(element.attrib)
        builder.add_patterns(self._parse_child_tags(element, context, 'pattern'))
        builder.add_namespaces(self._parse_child_tags(element, context, 'ns'))
        builder.add_phases(self._parse_child_tags(element, context, 'phase'))
        builder.add_diagnostics(self._parse_child_tags(element, context, 'diagnostics'))
        builder.add_properties(self._parse_child_tags(element, context, 'properties'))
        builder.add_paragraphs(self._parse_child_tags(element, context, 'p'))
        builder.add_variables(self._parse_child_tags(element, context, 'let'))

        if title_nodes := self._parse_child_tags(element, context, 'title'):
            builder.set_title(title_nodes[0])

        for include_node in self._parse_child_tags(element, context, 'include'):
            match include_node:
                case Pattern():
                    builder.add_patterns([include_node])
                case Namespace():
                    builder.add_namespaces([include_node])
                case Phase():
                    builder.add_namespaces([include_node])
                case Diagnostics():
                    builder.add_diagnostics([include_node])
                case Properties():
                    builder.add_properties([include_node])
                case Paragraph():
                    builder.add_paragraphs([include_node])
                case Variable():
                    builder.add_variables([include_node])
                case Title():
                    builder.set_title(include_node)

        return builder.build()


class NamespaceParser(ElementParser):
    """Parser for the `<ns>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Namespace:
        return Namespace(prefix=element.attrib['prefix'], uri=element.attrib['uri'])


class NameParser(ElementParser):
    """Parser for the `<name>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Name:
        if element.attrib.get('path'):
            return Name(Query(element.attrib['path']))
        return Name()


class ValueOfParser(ElementParser):
    """Parser for the `<value-of>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> ValueOf:
        return ValueOf(Query(element.attrib['select']))


class TitleParser(ElementParser):
    """Parser for the `<title>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Title:
        context = context or ParsingContext()
        return Title(content=''.join(self.get_rich_content(element, context)))


class PhaseParser(ElementParser):
    """Parser for the `<phase>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Phase:
        context = context or ParsingContext()
        builder = PhaseBuilder()

        builder.add_attributes(element.attrib)
        builder.add_active(self._parse_child_tags(element, context, 'active'))
        builder.add_variables(self._parse_child_tags(element, context, 'let'))
        builder.add_paragraphs(self._parse_child_tags(element, context, 'p'))

        for include_node in self._parse_child_tags(element, context, 'include'):
            match include_node:
                case ActivePhase():
                    builder.add_active([include_node])
                case Variable():
                    builder.add_variables([include_node])
                case Paragraph():
                    builder.add_paragraphs([include_node])

        return builder.build()


class ActivePhaseParser(ElementParser):
    """Parser for the `<active>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> ActivePhase:
        context = context or ParsingContext()
        content_parts = self.get_rich_content(element, context, parse_special=False)
        content = None
        if len(content_parts):
            content = ''.join(content_parts)

        return ActivePhase(pattern_id=element.attrib['pattern'], content=content)


class DiagnosticsParser(ElementParser):
    """Parser for the `<diagnostics>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Diagnostics:
        context = context or ParsingContext()
        diagnostics = []
        diagnostics.extend(self._parse_child_tags(element, context, 'diagnostic'))

        for include_node in self._parse_child_tags(element, context, 'include'):
            diagnostics.append(include_node)

        return Diagnostics(tuple(diagnostics))


class DiagnosticParser(ElementParser):
    """Parser for the `<diagnostic>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Diagnostic:
        context = context or ParsingContext()
        allowed_attributes = ['fpi', 'icon', 'id', 'role', 'see',
                              '{http://www.w3.org/XML/1998/namespace}lang',
                              '{http://www.w3.org/XML/1998/namespace}space']

        attribute_handlers = {
            '{http://www.w3.org/XML/1998/namespace}lang': lambda k, v: {'xml_lang': v},
            '{http://www.w3.org/XML/1998/namespace}space': lambda k, v: {'xml_space': v}
        }

        attributes = parse_attributes(element.attrib, allowed_attributes, attribute_handlers)
        return Diagnostic(content=self.get_rich_content(element, context), **attributes)


class PropertiesParser(ElementParser):
    """Parser for the `<properties>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Properties:
        context = context or ParsingContext()
        properties = []
        properties.extend(self._parse_child_tags(element, context, 'property'))

        for include_node in self._parse_child_tags(element, context, 'include'):
            properties.append(include_node)

        return Properties(tuple(properties))


class PropertyParser(ElementParser):
    """Parser for the `<property>` tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Property:
        context = context or ParsingContext()
        attributes = parse_attributes(element.attrib, ['id', 'role', 'scheme'])
        return Property(content=self.get_rich_content(element, context), **attributes)


class PatternParser(ElementParser):
    """Parse <pattern> tags.

    If the pattern contains the abstract attribute set to True (`abstract="true"`), we load the
    pattern as an `AbstractPattern`. If the `is-a` attribute is present, we load the pattern as an `InstancePattern`.
    In other cases, we load the pattern as a `ConcretePattern`.
    """

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Pattern:
        context = context or ParsingContext()

        is_abstract = element.attrib.get('abstract', 'false') == 'true'
        is_instance = element.attrib.get('is-a')

        if is_abstract:
            builder = AbstractPatternBuilder()
        elif is_instance:
            builder = InstancePatternBuilder()
        else:
            builder = ConcretePatternBuilder()

        builder.add_attributes(element.attrib)
        builder.add_rules(self._parse_child_tags(element, context, 'rule'))
        builder.add_variables(self._parse_child_tags(element, context, 'let'))
        builder.add_paragraphs(self._parse_child_tags(element, context, 'p'))
        builder.add_parameters(self._parse_child_tags(element, context, 'param'))

        if title_nodes := self._parse_child_tags(element, context, 'title'):
            builder.set_title(title_nodes[0])

        for include_node in self._parse_child_tags(element, context, 'include'):
            match include_node:
                case Rule():
                    builder.add_rules([include_node])
                case Variable():
                    builder.add_variables([include_node])
                case Paragraph():
                    builder.add_paragraphs([include_node])
                case Title():
                    builder.set_title(include_node)

        return builder.build()


class PatternParameterParser(ElementParser):
    """Parse <param> tags used in instance patterns."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> PatternParameter:
        return PatternParameter(name=element.attrib['name'], value=element.attrib['value'])


class RuleParser(ElementParser):
    """Parse `<rule>` tags.

    Tags like `<rule abstract="true">` are parsed as `AbstractRule`.
    Tags like `<rule context="...">` are parsed as `ConcreteRule`.
    Tags missing both an abstract and context attribute are parsed as `ExternalRule`.
    """

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Rule:
        context = context or ParsingContext()

        is_abstract = element.attrib.get('abstract', 'false') == 'true'
        loaded_external = element.attrib.get('context') is None

        if is_abstract:
            builder = AbstractRuleBuilder()
        elif loaded_external:
            builder = ExternalRuleBuilder()
        else:
            builder = ConcreteRuleBuilder()

        builder.add_attributes(element.attrib)
        builder.add_checks(self._parse_child_tags(element, context, 'assert'))
        builder.add_checks(self._parse_child_tags(element, context, 'report'))
        builder.add_variables(self._parse_child_tags(element, context, 'let'))
        builder.add_paragraphs(self._parse_child_tags(element, context, 'p'))
        builder.add_extends(self._parse_child_tags(element, context, 'extends'))

        for include_node in self._parse_child_tags(element, context, 'include'):
            match include_node:
                case Check():
                    builder.add_checks([include_node])
                case Variable():
                    builder.add_variables([include_node])
                case Paragraph():
                    builder.add_paragraphs([include_node])
                case Extends():
                    builder.add_extends([include_node])

        return builder.build()


class IncludeParser(ElementParser):
    """Parse <include> tags.

    This parses the XML in the referenced file into a SchematronASTNode. Due to the generic nature of the include node
    this can be a node of any type. Note that Schematron includes do not support a multi-root XML document.
    """

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> SchematronASTNode:
        context = context or ParsingContext()
        file_path = resolve_href(element.attrib['href'], context.base_path)
        xml = load_xml_document(file_path).getroot()
        parser = context.parser_factory.get_parser(etree.QName(xml).localname)
        return parser.parse(xml, context)


class VariableParser(ElementParser):
    """Parse <let> tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Variable:
        context = context or ParsingContext()

        if 'value' in element.attrib:
            return QueryVariable(name=element.attrib['name'], value=Query(element.attrib['value']))
        else:
            content = ''.join(self.get_rich_content(element, context, parse_special=False, remove_namespaces=False))
            return XMLVariable(name=element.attrib['name'], value=content)


class ParagraphParser(ElementParser):
    """Parse <p> tags."""

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Paragraph:
        context = context or ParsingContext()

        allowed_attributes = ['icon', 'id', 'class',
                              '{http://www.w3.org/XML/1998/namespace}lang',
                              '{http://www.w3.org/XML/1998/namespace}space']

        attribute_handlers = {
            'class': lambda k, v: {'class_': v},
            '{http://www.w3.org/XML/1998/namespace}lang': lambda k, v: {'xml_lang': v},
            '{http://www.w3.org/XML/1998/namespace}space': lambda k, v: {'xml_space': v}
        }

        attributes = parse_attributes(element.attrib, allowed_attributes, attribute_handlers)
        content = ''.join(self.get_rich_content(element, context, parse_special=False))
        return Paragraph(content=content, **attributes)


class ExtendsParser(ElementParser):
    """Parse <extends> tags.

    If the extends tag points to another file, we will load the rule from that file and return it
    wrapped in an `ExtendsExternal`. If the `<extends>` points to a rule by ID, we return an `ExtendsById`.
    """

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Extends:
        context = context or ParsingContext()

        if 'rule' in element.attrib:
            return ExtendsById(element.attrib['rule'])

        file_path = resolve_href(element.attrib['href'], context.base_path)
        xml = load_xml_document(file_path).getroot()
        parser = context.parser_factory.get_parser('rule')
        rule = parser.parse(xml, context)

        if not isinstance(rule, ExternalRule):
            raise ValueError('The rule defined in the <extends> tag is invalid (contains context or is abstract).')

        return ExtendsExternal(rule, file_path)


class CheckParser(ElementParser):

    def __init__(self, type_instance: type[Check]):
        """Base parser for the <assert> and <report> checks.

        Args:
            type_instance: the type we are initializing, Assert or Report.
        """
        self.type_instance = type_instance

    @override
    def parse(self, element: Element, context: ParsingContext | None = None) -> Check:
        context = context or ParsingContext()

        allowed_attributes = ['test', 'diagnostics', 'properties', 'subject',
                              'id', 'role', 'flag', 'see', 'fpi', 'icon',
                              '{http://www.w3.org/XML/1998/namespace}lang',
                              '{http://www.w3.org/XML/1998/namespace}space']

        attribute_handlers = {
            'test': lambda k, v: {k: Query(v)},
            'diagnostics': lambda k, v: {k: tuple(v.split(' '))},
            'properties': lambda k, v: {k: tuple(v.split(' '))},
            'subject': lambda k, v: {k: XPathExpression(v)},
            '{http://www.w3.org/XML/1998/namespace}lang': lambda k, v: {'xml_lang': v},
            '{http://www.w3.org/XML/1998/namespace}space': lambda k, v: {'xml_space': v}
        }

        attributes = parse_attributes(element.attrib, allowed_attributes, attribute_handlers)
        return self.type_instance(content=self.get_rich_content(element, context), **attributes)


class AssertParser(CheckParser):

    def __init__(self):
        super().__init__(Assert)


class ReportParser(CheckParser):

    def __init__(self):
        super().__init__(Report)
