__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

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
from pyschematron.parsers.xml_to_ast.builders import ConcreteRuleBuilder, ExternalRuleBuilder, AbstractRuleBuilder
from pyschematron.parsers.xml_to_ast.utils import node_to_str, resolve_href
from pyschematron.utils import load_xml



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
