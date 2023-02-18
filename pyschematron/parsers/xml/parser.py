__author__ = 'Robbert Harms'
__date__ = '2023-02-16'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

import os
import re
import warnings
from abc import ABCMeta, abstractmethod
from io import BytesIO, IOBase
from itertools import chain
from pathlib import Path
from pprint import pprint
from typing import BinaryIO, Union, Type, Dict, Any
from xml.etree import ElementTree

import elementpath
from elementpath import XPathToken, XPath1Parser, XPath2Parser
from elementpath.tdop import Parser

import lxml
from elementpath.xpath3 import XPath3Parser
from elementpath.xpath31 import XPath31Parser
from lxml import etree, objectify
from lxml.etree import _ElementTree, _Element
from ruamel import yaml

from pyschematron.parsers.ast import Schema, Check, Assert, SchematronNode, Pattern, Rule, Report, Variable, Paragraph, \
    ConcreteRule, AbstractRule, ExtendsById, Extends, ExtendsExternal, ExternalRule
from pyschematron.parsers.xml.builders import ConcreteRuleBuilder, ExternalRuleBuilder, AbstractRuleBuilder
from pyschematron.parsers.xml.utils import node_to_str, resolve_href
from pyschematron.utils import load_xml


class ParserFactory(metaclass=ABCMeta):
    """Create Schematron node parsers for a specific Schematron element class.

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
            'include': IncludeParser()
        }

    def get_parser(self, xml_tag: str) -> "ElementParser":
        return self.parsers[xml_tag]


class ParsingContext:

    def __init__(self,
                 xpath_parser: Parser,
                 parser_factory: ParserFactory = None,
                 base_path: Path = None):
        """Create the parser context we use while parsing the Schematron XML.

        Args:
            xpath_parser: the xpath parser we can use during parsing of the Schematron XML
            parser_factory: the factory we use to create sub parsers, defaults to :class:`DefaultParserFactory`.
            base_path: the base path to use for file inclusions, if not provided it is set to the current working
                directory.
        """
        self.xpath_parser = xpath_parser
        self.parser_factory = parser_factory or DefaultParserFactory()
        self.base_path = base_path or os.getcwd()

    @classmethod
    def from_schematron_root(cls, xml: _Element, parser_factory: ParserFactory = None, base_path: Path = None):
        """Prepares the parsing context from the provided Schematron XML root.

        Args:
            xml: the Schematron root node, we use this to look up the namespaces and the query binding to
                create the right xpath parser
            parser_factory: the factory we can use to create sub parsers, if not provided we use the default parser
                factory.
            base_path: base path to use for file inclusions
        """
        xpath_parser = cls.get_xpath_parser(xml)
        return cls(xpath_parser, parser_factory, base_path)

    @staticmethod
    def get_xpath_parser(xml: _Element) -> Parser:
        """Determine the Xpath parser from the Schematron root.

        Args:
            xml: the Schematron XML root node

        Returns:
            A `elementpath` parser instance

        Raises:
            ValueError if the query binding is not supported by this library.
        """
        xpath_parsers = {
            'xslt': XPath1Parser,
            'xslt2': XPath2Parser,
            'xslt3': XPath31Parser,
            'xpath': XPath1Parser,
            'xpath2': XPath2Parser,
            'xpath3': XPath3Parser,
            'xpath31': XPath31Parser
        }
        query_binding = xml.attrib.get('queryBinding', 'xslt')

        if query_binding not in xpath_parsers:
            raise ValueError(f'The provided queryBinding {query_binding} is not available in this package.')

        if query_binding.startswith('xslt'):
            warnings.warn(f'XSLT queryBinding support is limited to xpath expressions only.')

        namespaces = {}
        for xpath_namespace in elementpath.select(xml, '/schema/ns'):
            namespaces[xpath_namespace.attrib['prefix']] = xpath_namespace.attrib['uri']

        return xpath_parsers[query_binding](namespaces=namespaces)


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
    def get_rich_content(element: _Element, context: ParsingContext) -> list[str | XPathToken]:
        """Get the rich content of the provided node.

        Args:
            element: the element for which to get the content.
            context: the parsing context, we use this to parse <value-of> nodes.

        Returns:
            A list of text and XPathToken nodes. All rich content like <emph> and <b> are rendered as string content.
                Nodes of type <value-of> are converted into XPathTokens.
        """
        content = [element.text]

        for child in element.getchildren():
            if child.tag == '{http://purl.oclc.org/dsdl/schematron}value-of':
                content.append(context.xpath_parser.parse(child.attrib['select']))
                content.append(child.tail)
            else:
                content.append(node_to_str(child))
                content.append(child.tail)

        return content


class RuleParser(ElementParser):
    """Parse <rule> tags."""

    def parse(self, element: _Element, context: ParsingContext) -> Rule:
        is_abstract = element.attrib.get('abstract', 'false') == 'true'
        loaded_external = element.attrib.get('context') is None

        if is_abstract:
            builder = AbstractRuleBuilder()
        elif loaded_external:
            builder = ExternalRuleBuilder()
        else:
            builder = ConcreteRuleBuilder()

        builder.add_attributes(element.attrib, context.xpath_parser)
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
        return Variable(name=element.attrib['name'],
                        value=context.xpath_parser.parse(element.attrib['value']))


class ParagraphParser(ElementParser):
    """Parse <p> tags."""

    def parse(self, element: _Element, context: ParsingContext) -> Paragraph:
        kwargs = {
            'content': self.get_rich_content(element, context)
        }

        for string_item in ['icon', 'id']:
            if string_item in element.attrib:
                kwargs[string_item] = element.attrib[string_item]

        if 'class' in element.attrib:
            kwargs['class_'] = element.attrib['class']

        return Paragraph(**kwargs)


class ExtendsParser(ElementParser):
    """Parse <extends> tags"""

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
        kwargs = {
            'test': context.xpath_parser.parse(element.attrib['test']),
            'content': self.get_rich_content(element, context)
        }

        if 'diagnostics' in element.attrib:
            kwargs['diagnostics'] = element.attrib['diagnostics'].split(' ')

        if 'properties' in element.attrib:
            kwargs['properties'] = element.attrib['properties'].split(' ')

        if 'subject' in element.attrib:
            kwargs['subject'] = context.xpath_parser.parse(element.attrib['subject'])

        for string_item in ['id', 'role', 'flag', 'see', 'fpi', 'icon']:
            if string_item in element.attrib:
                kwargs[string_item] = element.attrib[string_item]

        for xml_item in ['lang', 'space']:
            qname = '{http://www.w3.org/XML/1998/namespace}' + xml_item
            if qname in element.attrib:
                kwargs[f'xml_{xml_item}'] = element.attrib[qname]

        return self.type_instance(**kwargs)


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

    <pattern>
        <rule abstract="false" context="t:Document" flag="flagtest" fpi="fpitest" icon="icontest" id="idtest"
                        role="roletest" see="seetest" subject="t:Header" xml:lang="nl" xml:space="preserve">
            <let name="nametest" value="t:Footer" />
            <p class="classtest">some details</p>
            <assert id="TEST-R001" diagnostics="test1 test2" flag="flagtest" fpi="fpitest" icon="icontest"
                        properties="property1 property2" role="roletest" see="seetest"
                        subject="t:Header" xml:lang="nl" xml:space="preserve"
                    test="t:Header">Start <value-of select="note/to/text()"/>, and <b>something</b> <value-of select="note/to/text()"/> <emph>afterwards</emph>.</assert>
            <assert id="TEST-R002"
                    test="t:Author">Document MUST contain author.</assert>
            <assert id="TEST-R003"
                    test="t:Date">Document MUST contain date.</assert>
            <extends rule="idtest" />
            <extends href="../tests/fixtures/extends_example.xml" />
            <include href="../tests/fixtures/rule_include_example.xml" />
        </rule>
    </pattern>
</schema>
'''


schematron_xml = load_xml(test)
parsing_context = ParsingContext.from_schematron_root(schematron_xml)

# assert_parser = parsing_context.parser_factory.get_parser('assert')
assert_parser = RuleParser()
element = assert_parser.parse(elementpath.select(schematron_xml, '/schema/pattern/rule')[0], parsing_context)

pprint(element)

# from dataclasses import dataclass, asdict
# print(asdict(element))

print()


# builder = SchemaBuilder()
# schema = builder.build()
