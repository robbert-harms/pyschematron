from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from io import BytesIO, IOBase
from pathlib import Path
from typing import BinaryIO, Union, Type, Dict

import lxml
from lxml import etree
from xml.etree import ElementTree

from elements import Assert, SchematronElement, Variable, Report, Rule, Pattern
from pyschematron.builders import AssertBuilder, ReportBuilder, RuleBuilder, PatternBuilder, \
    VariableBuilder, SchematronElementBuilder
from pyschematron.xml_writer import JinjaXMLWriter

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
    def get_parser(self, schematron_element: Type[SchematronElement]) -> ElementParser:
        """Get the parser for a specific schematron element.

        Args:
            schematron_element: the element for which we want to get the parser

        Returns:
            A parser for the schematron element we want to construct
        """

    @abstractmethod
    def get_schematron_element(self, xml_tag: str) -> Type[SchematronElement]:
        """Get a schematron element type for the indicated tag.

        This should be a mapping of xml tags to Schematron element types, such that the resulting schematron element
        type can be used in the :meth:`get_parser`.

        Args:
            xml_tag: the XML tag for which we want the schematron element.

        Returns:
            The schematron element type we associate with the indicated tag.
        """


class DefaultParserFactory(ParserFactory):
    """The default parser factory.

    For each Schematron element, this returns the standard parser from this library.
    """

    def get_parser(self, schematron_element: Type[SchematronElement]) -> ElementParser:
        parser_mapping: Dict[Type[SchematronElement], ElementParser] = {
            Pattern: PatternParser(self),
            Rule: RuleParser(self),
            Assert: AssertParser(self),
            Report: ReportParser(self),
            Variable: VariableParser(self),
        }
        return parser_mapping[schematron_element]

    def get_schematron_element(self, xml_tag: str) -> Type[SchematronElement]:
        mapping: Dict[str, Type[SchematronElement]] = {
            'pattern': Pattern,
            'rule': Rule,
            'assert': Assert,
            'report': Report,
            'let': Variable,
        }
        return mapping[xml_tag]


class ElementParser(metaclass=ABCMeta):

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


class IterparseElementParser(ElementParser, metaclass=ABCMeta):

    def parse(self, xml_data: Union[bytes, str, Path, IOBase, BinaryIO, lxml.etree.iterparse]) -> SchematronElement:
        match xml_data:
            case IOBase():
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

    @staticmethod
    def _iterparser_clear_memory(element):
        """Helper routine to clear memory of an element used in an iterparser.

        This also eliminate now-empty references from the root node to elem.

        Args:
            element: the element we can clear
        """
        def clear_references():
            for ancestor in element.xpath('ancestor-or-self::*'):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]

        element.clear()
        clear_references()


class BasicIterparseElementParser(IterparseElementParser):

    def __init__(self,
                 builder: SchematronElementBuilder,
                 xml_tag: str,
                 *args,
                 complex_text_node: bool = False,
                 **kwargs):
        """Basic interpretation of an iterparse element parser.

        This contains the basic logic for traversing and parsing the Schematron file using the iterparser.
        Building logic is determined by the instance variables provided in the initialization,
        and by (optionally) overwriting the private helper methods.

        Args:
             builder: the element builder we use to construct the elements
             xml_tag: the specific element tag this builder is meant for
             complex_text_node: if the content of the parsed XML tag should be interpreted as a
                text node with (possibly) complex content (set to True), or as a tag with regular children tags which
                need another parser for processing (set to False).
        """
        super().__init__(*args, **kwargs)
        self._element_name = xml_tag
        self._builder = builder
        self._complex_text_node = complex_text_node

    def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
        self._builder.clear()

        for action, element in iterparser:
            local_name = etree.QName(element.tag).localname

            if action == ITERPARSE_START_TAG:
                if local_name != self._element_name:
                    self._parse_child_start_tag(element, iterparser)
            elif action == ITERPARSE_END_TAG:
                if local_name == self._element_name:
                    self._parse_end_tag(element)
                    self._iterparser_clear_memory(element)
                    break

        return self._builder.build()

    def _parse_child_start_tag(self, element: etree.Element, iterparser):
        """Parse the start tag of a child element.

        Args:
            element: the starting part of the child element
            iterparser: the parser we can forward to next parsers.
        """
        if self._complex_text_node:
            self._builder.add_mixed_content(ElementTree.tostring(element, encoding='unicode'))
        else:
            local_name = etree.QName(element.tag).localname
            element_type = self._parser_factory.get_schematron_element(local_name)
            sub_parser = self._parser_factory.get_parser(element_type)
            self._builder.add_child(sub_parser.parse(iterparser))

    def _parse_end_tag(self, element: etree.Element):
        """Parse the end tag of the element we are meant to parse.

        Args:
            element: the end tag of the element
        """
        if self._complex_text_node:
            self._builder.set_text(element.text)

        for name, value in element.attrib.items():
            self._builder.set_attribute(name, value)


class PatternParser(BasicIterparseElementParser):

    def __init__(self, *args, **kwargs):
        super().__init__(PatternBuilder(), 'pattern',  *args, **kwargs)


class RuleParser(BasicIterparseElementParser):

    def __init__(self, *args, **kwargs):
        super().__init__(RuleBuilder(), 'rule',  *args, **kwargs)


class AssertParser(BasicIterparseElementParser):

    def __init__(self, *args, **kwargs):
        super().__init__(AssertBuilder(), 'assert', *args, complex_text_node=True, **kwargs)


class ReportParser(BasicIterparseElementParser):

    def __init__(self, *args, **kwargs):
        super().__init__(ReportBuilder(), 'report', *args, complex_text_node=True, **kwargs)


class VariableParser(BasicIterparseElementParser):

    def __init__(self, *args, **kwargs):
        super().__init__(VariableBuilder(), 'let', *args, **kwargs)


xml_writer = JinjaXMLWriter()

# test = '''<?xml version="1.0" encoding="UTF-8"?>
# <schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
#     <ns uri="http://www.altoida.com/XMLSchema/data/2021" prefix="ad"/>
#     <ns uri="http://www.w3.org/2001/XMLSchema-instance" prefix="xsi"/>
#     <pattern>
#         <rule context="//ad:altoida_data/ad:assessment//*[@start_ts and @end_ts]">
#             <assert test="number(@end_ts) >= number(@start_ts)">
#                 Test if the end ts is larger than the start ts.
#             </assert>
#             <assert test="number(@end_ts) >= number(@start_ts)">
#                 Test if the end ts is larger than the start ts.
#             </assert>
#         </rule>
#     </pattern>
#     <pattern>
#         <rule context="//ad:altoida_data/ad:metadata/ad:session/ad:datetime">
#             <assert test="xs:dateTime(@local) = xs:dateTime(@utc)">
#                 The local and UTC datetime's do not agree.
#             </assert>
#         </rule>
#     </pattern>
# </schema>
# '''

pattern_str = '''
<pattern id="test">
    <let name="animalSpecies" value="ark:species"/>
    <rule context="//ad:altoida_data/ad:metadata/ad:session/ad:datetime">
        <let name="roat" value="'roat'"/>
        <assert test="xs:dateTime(@local) = xs:dateTime(@utc)" see="google.com">
            Start <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards.
        </assert>
        <report test="//notes" id="unique-id">
            String with a value: <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards Report.
        </report>
    </rule>
</pattern>
'''
pattern_item = PatternParser().parse(pattern_str)
# print(pattern_item)
print(xml_writer.to_string(pattern_item))

# rule_str = '''
# <rule context="//ad:altoida_data/ad:metadata/ad:session/ad:datetime">
#     <let name="roat" value="'roat'"/>
#     <let name="test" value="//test"/>
#     <assert test="xs:dateTime(@local) = xs:dateTime(@utc)" id="test">
#         Start <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards.
#     </assert>
#     <report test="//notes">
#         String with a value: <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards Report.
#     </report>
# </rule>
# '''
# # str = '''
# # <rule id="inline" abstract="yes">
# #   <report test="*">Error! Element inside inline.</report>
# #   <assert test="text">Strange, there's no text inside this inline.</assert>
# # </rule>
# # '''
#
# rule_item = RuleParser().parse(rule_str)
# # # print(rule_item)
# print(xml_writer.to_string(rule_item))
#
#
# #
# # let_str = '''
# # <let name="roat" value="'roat'"/>
# # '''
# # let_item = VariableParser().parse(let_str)
# # print(let_item)
# # print(xml_writer.to_string(let_item))
#
# assert_str = '''
# <assert
#     test="//notes/test"
#     id="unique-id2">
#     String with a value: <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards.
# </assert>'''
# assert_item = AssertParser().parse(assert_str)
# # print(assert_item)
# print(xml_writer.to_string(assert_item))
#
# report_str = '''
# <report
#     test="//notes"
#     id="unique-id">
#     String with <emph>bold text</emph>, a value: <value-of select="note/to/text()"/>,
#     <dir> reversed stuff</dir> and text at the end.
# </report>'''
# report = ReportParser().parse(report_str)
# # print(report)
# print(xml_writer.to_string(report))
