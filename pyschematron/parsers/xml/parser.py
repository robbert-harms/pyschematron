__author__ = 'Robbert Harms'
__date__ = '2023-02-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

import os
from abc import ABCMeta, abstractmethod
from pathlib import Path
from pprint import pprint
from typing import Type

import elementpath

from lxml import etree
from lxml.etree import _Element

from pyschematron.parsers.ast import Schema, Check, Assert, SchematronNode, Pattern, Rule, Report, Variable, Paragraph, \
    ConcreteRule, AbstractRule, ExtendsById, Extends, ExtendsExternal, ExternalRule, XPath, XPathVariable, XMLVariable, \
    Namespace, Title, PatternParameter, ValueOf, Name
from pyschematron.parsers.xml.builders import ConcreteRuleBuilder, ExternalRuleBuilder, AbstractRuleBuilder, \
    ConcretePatternBuilder, SchemaBuilder, AbstractPatternBuilder, InstancePatternBuilder
from pyschematron.parsers.xml.utils import node_to_str, resolve_href, parse_attributes
from pyschematron.utils import load_xml


class ParserFactory(metaclass=ABCMeta):
    """Create a parser for parsing a specific XML element into an AST node.

    By using a factory method we allow subclassing the :class:`SchematronNode` elements and have a
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
            'assert': AssertParser(),
            'report': ReportParser(),
            'rule': RuleParser(),
            'let': VariableParser(),
            'p': ParagraphParser(),
            'extends': ExtendsParser(),
            'include': IncludeParser(),
            'pattern': PatternParser(),
            'schema': SchemaParser(),
            'ns': NamespaceParser(),
            'title': TitleParser(),
            'param': PatternParameterParser()
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
    def parse(self, element: _Element, context: ParsingContext) -> SchematronNode:
        """Parse a piece of XML data into a SchematronNode.

        Args:
            element: the Schematron XML element we want to parse
            context: the context we use for parsing this Schematron XML element
        """

    @staticmethod
    def _parse_child_tags(element: _Element, context: ParsingContext, xml_tag: str) -> list[SchematronNode]:
        """Parse a sequence of XML elements with the same tag name.

        Args:
            element: the element which we search
            context: the parsing context
            xml_tag: the XML tag to search for
        """
        parser = context.parser_factory.get_parser(xml_tag)

        items = []
        for child in elementpath.select(element, xml_tag):
            items.append(parser.parse(child, context))

        return items

    @staticmethod
    def get_rich_content(element: _Element, parse_special: bool = True) -> list[str | ValueOf | Name]:
        """Get the rich content of the provided node.

        Args:
            element: the element for which to get the content.
            parse_special: if set to True, we separate the strings and the special variables (ValueOf, Name).
                If set to false we return only string contents.

        Returns:
            A list of text and special item nodes. All rich content like <emph> and <b> are rendered as string content.
                If parse special is True, Nodes of type <value-of> and <name> are parsed to ValueOf and Name.
        """
        content = [element.text]

        for child in element.getchildren():
            if parse_special and child.tag == '{http://purl.oclc.org/dsdl/schematron}value-of':
                content.append(ValueOf(XPath(child.attrib['select'])))
            elif parse_special and child.tag == '{http://purl.oclc.org/dsdl/schematron}name':
                if child.attrib.get('path'):
                    content.append(Name(XPath(child.attrib['path'])))
                else:
                    content.append(Name())
            else:
                content.append(node_to_str(child))
            content.append(child.tail)

        return [el for el in content if el]


class SchemaParser(ElementParser):
    """Parse <schema> root tags"""

    def parse(self, element: _Element, context: ParsingContext) -> SchematronNode:
        builder = SchemaBuilder()
        builder.add_attributes(element.attrib)
        builder.add_patterns(self._parse_child_tags(element, context, 'pattern'))
        builder.add_namespaces(self._parse_child_tags(element, context, 'ns'))

        if title_nodes := self._parse_child_tags(element, context, 'title'):
            builder.set_title(title_nodes[0])

        return builder.build()


class NamespaceParser(ElementParser):

    def parse(self, element: _Element, context: ParsingContext) -> Namespace:
        return Namespace(prefix=element.attrib['prefix'], uri=element.attrib['uri'])


class TitleParser(ElementParser):

    def parse(self, element: _Element, context: ParsingContext) -> Title:
        return Title(content=''.join(self.get_rich_content(element)))


class PatternParser(ElementParser):
    """Parse <pattern> tags.

    If the pattern contains the abstract attribute set to True (`abstract="true"`), we load the
    pattern as an `AbstractPattern`. If the `is-a` attribute is present, we load the pattern as an `InstancePattern`.
    In other cases, we load the pattern as a `ConcretePattern`.
    """

    def parse(self, element: _Element, context: ParsingContext) -> Pattern:
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

    def parse(self, element: _Element, context: ParsingContext) -> PatternParameter:
        return PatternParameter(name=element.attrib['name'], value=element.attrib['value'])


class RuleParser(ElementParser):
    """Parse `<rule>` tags.

    Tags like `<rule abstract="true">` are parsed as `AbstractRule`.
    Tags like `<rule context="...">` are parsed as `ConcreteRule`.
    Tags missing both an abstract and context attribute are parsed as `ExternalRule`.
    """

    def parse(self, element: _Element, context: ParsingContext) -> Rule:
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

    This parses the XML in the referenced file into a SchematronNode. Due to the generic nature of the include node
    this can be a node of any type.
    """

    def parse(self, element: _Element, context: ParsingContext) -> SchematronNode:
        file_path = resolve_href(element.attrib['href'], context.base_path)
        xml = load_xml(file_path)
        parser = context.parser_factory.get_parser(etree.QName(xml).localname)
        return parser.parse(xml, context)


class VariableParser(ElementParser):
    """Parse <let> tags."""

    def parse(self, element: _Element, context: ParsingContext) -> Variable:
        if 'value' in element.attrib:
            return XPathVariable(name=element.attrib['name'], value=XPath(element.attrib['value']))
        else:
            content = ''.join(self.get_rich_content(element, parse_special=False))
            return XMLVariable(name=element.attrib['name'], value=content)


class ParagraphParser(ElementParser):
    """Parse <p> tags."""

    def parse(self, element: _Element, context: ParsingContext) -> Paragraph:
        attributes = parse_attributes(element.attrib, ['icon', 'id', 'class'], {'class': lambda k, v: {'class_': v}})
        content = ''.join(self.get_rich_content(element, parse_special=False))
        return Paragraph(content=content, **attributes)


class ExtendsParser(ElementParser):
    """Parse <extends> tags.

    If the extends tag points to another file, we will load the rule from that file and return
    wrapped in an `ExtendsExternal`. If the extends points to a rule by ID, we return an `ExtendsById`.
    """

    def parse(self, element: _Element, context: ParsingContext) -> Extends:
        if 'rule' in element.attrib:
            return ExtendsById(element.attrib['rule'])

        file_path = resolve_href(element.attrib['href'], context.base_path)
        xml = load_xml(file_path)
        parser = context.parser_factory.get_parser('rule')

        return ExtendsExternal(parser.parse(xml, context), file_path)


class CheckParser(ElementParser):

    def __init__(self, type_instance: Type[Check]):
        """Base parser for the <assert> and <report> checks.

        Args:
            type_instance: the type we are initializing, Assert or Report.
        """
        self.type_instance = type_instance

    def parse(self, element: _Element, context: ParsingContext) -> Check:
        allowed_attributes = ['test', 'diagnostics', 'properties', 'subject',
                              'id', 'role', 'flag', 'see', 'fpi', 'icon',
                              '{http://www.w3.org/XML/1998/namespace}lang',
                              '{http://www.w3.org/XML/1998/namespace}space']

        attribute_handlers = {
            'test': lambda k, v: {k: XPath(v)},
            'diagnostics': lambda k, v: {k: v.split(' ')},
            'properties': lambda k, v: {k: v.split(' ')},
            'subject': lambda k, v: {k: XPath(v)},
            '{http://www.w3.org/XML/1998/namespace}lang': lambda k, v: {'xml_lang': v},
            '{http://www.w3.org/XML/1998/namespace}space': lambda k, v: {'xml_space': v}
        }

        attributes = parse_attributes(element.attrib, allowed_attributes, attribute_handlers)
        return self.type_instance(content=self.get_rich_content(element), **attributes)


class AssertParser(CheckParser):

    def __init__(self):
        super().__init__(Assert)


class ReportParser(CheckParser):

    def __init__(self):
        super().__init__(Report)



test = '''
<schema xmlns="http://purl.oclc.org/dsdl/schematron" schemaVersion="iso" queryBinding="xpath2">
    <title>SCH-001</title>
    <ns prefix="t" uri="test"/>

    <pattern documents="current-date()">
        <title>SCH-003</title>
        <p>some paragraph</p>
        <rule abstract="false" context="t:Document" flag="flagtest" fpi="fpitest" icon="icontest" id="idtest"
                        role="roletest" see="seetest" subject="t:Header" xml:lang="nl" xml:space="preserve">
            <let name="nametest" value="t:Footer" />
            <let name="open_item"><data xmlns="http://test.nl">test</data></let>
            <p/>
            <p class="classtest">some details</p>
            <assert id="TEST-R001" diagnostics="test1 test2" flag="flagtest" fpi="fpitest" icon="icontest"
                        properties="property1 property2" role="roletest" see="seetest"
                        subject="t:Header" xml:lang="nl" xml:space="preserve"
                    test="t:Header">Start <value-of select="note/to/text()"/>, and <b>something</b> <value-of select="note/to/text()"/> <emph>afterwards</emph>.</assert>
            <assert id="TEST-R002"
                    test="t:Author">Document <name /> MUST <name path="/" /> contain author.</assert>
            <assert id="TEST-R003"
                    test="t:Date">Document MUST contain date.</assert>
            <extends rule="idtest" />
            <extends href="../tests/fixtures/extends_example.xml" />
            <include href="../tests/fixtures/rule_include_example.xml" />
        </rule>
        <rule context="lions">
            <report id="some_report" test="@alpha">Some alpha test</report>
        </rule>
        <include href="../tests/fixtures/pattern_include_example.xml" />
    </pattern>

  <pattern abstract="true" id="table-pattern">
    <rule context="$table">
      <assert test="$row">
        The element <value-of select="local-name()"/> is a table structure.
        Tables must contain the correct row elements.
      </assert>
    </rule>
    <rule context="$table/$row">
      <assert test="$entry">
        The element <value-of select="local-name()"/> is a table row.
        Rows must contain the correct cell elements.
      </assert>
    </rule>
  </pattern>

    <pattern is-a="table-pattern" >
    <param name="table" value="table"/>
    <param name="row" value="tr"/>
    <param name="entry" value="td"/>
  </pattern>

</schema>
'''


schematron_xml = load_xml(test)
parsing_context = ParsingContext()

# assert_parser = parsing_context.parser_factory.get_parser('assert')
assert_parser = SchemaParser()
element = assert_parser.parse(schematron_xml, parsing_context)

pprint(element)
# pprint(element.patterns[0].rules[0].checks[0])
# from dataclasses import dataclass, asdict
# print(asdict(element))

print()


# builder = SchemaBuilder()
# schema = builder.build()
