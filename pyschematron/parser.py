from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from pprint import pprint
from typing import BinaryIO, Any, Union, Type, Dict, TypeVar

import lxml
from elementpath import Selector
from lxml import etree

from elements import Assert, SchematronElement, Namespace, Variable, Phase, Pattern, Schema, Report, Rule
from pyschematron.builders import AssertBuilder, RuleElementBuilder, ReportBuilder, RuleBuilder

from elementpath.xpath31 import XPath31Parser


ITERPARSE_START_TAG = 'start'
ITERPARSE_END_TAG = 'end'


class ParserFactory(metaclass=ABCMeta):
    """Create Schematron element parsers for the different Schematron elements.

    By using a factory method we allow subclassing the :class:`SchematronElement` elements and have a
    dedicated parser for such new subclasses without having to subclass a deep class hierarchy.

    For example, suppose you subclass the element "Assert" as "MyAssert" with some additional metadata.
    When parsing, you could reuse most of the parsing code by providing the factory with::

        {Assert: MyAssertParser()}

    Where `MyAssertParser` is a parser returning your subclassed "MyAssert" instead of "Assert".
    """

    @abstractmethod
    def get_parser(self, schematron_element: Type[SchematronElement]) -> SchematronElementParser:
        """Get the parser for a specific schematron element.

        Args:
            schematron_element: the element for which we want to get the parser

        Returns:
            A parser for the schematron element we want to construct
        """


class DefaultParserFactory(ParserFactory):
    """The default parser factory.

    For each Schematron element, this returns the standard parser from this library.
    """

    def get_parser(self, schematron_element: Type[SchematronElement]) -> SchematronElementParser:
        parser_mapping: Dict[Type[SchematronElement], SchematronElementParser] = {
            Rule: RuleParser(self),
            Assert: AssertParser(self),
            Report: ReportParser(self),
        }
        return parser_mapping[schematron_element]


class SchematronElementParser(metaclass=ABCMeta):

    def __init__(self, parser_factory: ParserFactory = DefaultParserFactory()):
        """Abstract base class for a Schematron element parser.

        These parsers take in a part of a Schematron XML file and parse it into a :class:`SchematronElement`.

        The element parsers are initialized with the factory we can use for creating sub element parsers.
        """
        self._parser_factory = parser_factory

    @abstractmethod
    def parse(self, xml_data: Union[bytes, str, Path, BytesIO, lxml.etree.iterparse]) -> SchematronElement:
        """Parse a piece of XML data into a SchematronElement.

        Args:
            xml_data: the XML data we want to parse. Can be in different formats, but the result should all be the same.
        """


class BaseSchematronElementParser(SchematronElementParser, metaclass=ABCMeta):

    # todo BinaryIO?
    def parse(self, xml_data: Union[bytes, str, Path, BytesIO, lxml.etree.iterparse]) -> SchematronElement:
        match xml_data:
            case BytesIO():
                return self.parse(etree.iterparse(xml_data, events=['start', 'end']))
            case lxml.etree.iterparse():
                return self.iterparse(xml_data)
            case bytes():
                return self.parse(BytesIO(xml_data))
            case str():
                return self.parse(BytesIO(xml_data.encode('utf-8')))
            case Path():
                with open(xml_data, 'rb') as f:
                    return self.parse(f)

    @abstractmethod
    def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
        """Parse a piece of XML using the iterparser from the lxml etree library.

        The iterparser will provide start and end tags of any element, the implementing class is free to use
        this to parse the element. Note that the implementing class is responsible for clearing the memory
        after having parsed the elements.

        Args:
             iterparser: the iterative parser we can use to load the XML
        """

    def _iterparser_clear_memory(self, element):
        """Helper routine to clear memory of an element used in an iterparser.

        This also eliminate now-empty references from the root node to elem.

        Args:
            element: the element we can clear
        """
        def clean_references():
            for ancestor in element.xpath('ancestor-or-self::*'):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]

        element.clear()
        clean_references()


class RuleParser(BaseSchematronElementParser):

    def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
        builder = RuleBuilder()

        for action, element in iterparser:
            local_name = etree.QName(element.tag).localname

            if action == ITERPARSE_START_TAG:
                if local_name == 'assert':
                    sub_parser = self._parser_factory.get_parser(Assert)
                    builder.add_rule_element(sub_parser.parse(iterparser))
                elif local_name == 'report':
                    sub_parser = self._parser_factory.get_parser(Report)
                    builder.add_rule_element(sub_parser.parse(iterparser))

            elif action == ITERPARSE_END_TAG:
                builder.set_context(element.attrib.get('context'))
                self._iterparser_clear_memory(element)
                break

        return builder.build()


class RuleElementParser(BaseSchematronElementParser):
    """Base parser for the Schematron rules Assert and Report.

    To implement, the tag name must be defined and the get_builder method implemented.
    """
    tag_name: str = None

    def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
        builder = self.get_builder()

        for action, element in iterparser:
            local_name = etree.QName(element.tag).localname

            if action == ITERPARSE_END_TAG:
                if local_name == self.tag_name:
                    builder.prepend_message_part(element.text)
                    builder.set_id(element.attrib.get('id'))
                    builder.set_test(element.attrib.get('test', ''))
                    self._iterparser_clear_memory(element)
                    break
                else:
                    builder.add_message_part(element)
                    builder.add_message_part(element.tail)

        return builder.build()

    @abstractmethod
    def get_builder(self) -> RuleElementBuilder:
        """Get the builder we will use for this parser.

        Returns:
            The builder we will use for building this element.
        """


class AssertParser(RuleElementParser):
    tag_name: str = 'assert'

    def get_builder(self) -> RuleElementBuilder:
        return AssertBuilder()


class ReportParser(RuleElementParser):
    tag_name: str = 'report'

    def get_builder(self) -> RuleElementBuilder:
        return ReportBuilder()


test = '''<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
    <ns uri="http://www.altoida.com/XMLSchema/data/2021" prefix="ad"/>
    <ns uri="http://www.w3.org/2001/XMLSchema-instance" prefix="xsi"/>
    <pattern>
        <rule context="//ad:altoida_data/ad:assessment//*[@start_ts and @end_ts]">
            <assert test="number(@end_ts) >= number(@start_ts)">
                Test if the end ts is larger than the start ts.
            </assert>
            <assert test="number(@end_ts) >= number(@start_ts)">
                Test if the end ts is larger than the start ts.
            </assert>
        </rule>
    </pattern>
    <pattern>
        <rule context="//ad:altoida_data/ad:metadata/ad:session/ad:datetime">
            <assert test="xs:dateTime(@local) = xs:dateTime(@utc)">
                The local and UTC datetime's do not agree.
            </assert>
        </rule>
    </pattern>
</schema>
'''

# SchemaParser().parse(test)

print(RuleParser().parse('''
    <rule context="//ad:altoida_data/ad:metadata/ad:session/ad:datetime">
        <assert test="xs:dateTime(@local) = xs:dateTime(@utc)">
            Start <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards.
        </assert>
        <report
            test="//notes"
            id="unique-id">
            String with a value: <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards Report.
        </report>
    </rule>
'''))


assert_str = '''
<assert
    test="//notes"
    id="unique-id">
    String with a value: <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards.
</assert>'''
print(AssertParser().parse(assert_str))

report_str = '''
<report
    test="//notes"
    id="unique-id">
    String with a value: <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards Report.
</report>'''
print(ReportParser().parse(report_str))

# v = parser.parse_from_string(test)
# pprint(v)



# query = XPath31Parser().parse('array { (./text()|./element()) }')


