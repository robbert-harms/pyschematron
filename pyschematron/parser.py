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

from elements import Assert, SchematronElement, Variable, Report, Rule, Pattern
from pyschematron.builders import AssertBuilder, TestBuilder, ReportBuilder, RuleBuilder, PatternBuilder, \
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
            Variable: VariableParser(self)
        }
        return parser_mapping[schematron_element]

    def get_schematron_element(self, xml_tag: str) -> Type[SchematronElement]:
        mapping: Dict[str, Type[SchematronElement]] = {
            'pattern': Pattern,
            'rule': Rule,
            'assert': Assert,
            'report': Report,
            'let': Variable
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


class BaseElementParser(ElementParser, metaclass=ABCMeta):

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


class SimpleElementParser(BaseElementParser):

    def __init__(self, builder: SchematronElementBuilder, xml_tag: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._element_name = xml_tag
        self._builder = builder

    def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
        self._builder.clear()

        for action, element in iterparser:
            local_name = etree.QName(element.tag).localname

            if action == ITERPARSE_START_TAG:
                if local_name != self._element_name:
                    self._parse_child_start_tag(element, iterparser)
            elif action == ITERPARSE_END_TAG:
                self._parse_end_tag(element)
                self._iterparser_clear_memory(element)
                break

        return self._builder.build()

    def _parse_child_start_tag(self, element, iterparser):
        local_name = etree.QName(element.tag).localname
        element_type = self._parser_factory.get_schematron_element(local_name)
        sub_parser = self._parser_factory.get_parser(element_type)
        self._builder.add_child(sub_parser.parse(iterparser))

    def _parse_end_tag(self, element):
        for name, value in element.attrib.items():
            self._builder.set_attribute(name, value)


class PatternParser(SimpleElementParser):

    def __init__(self, *args, **kwargs):
        super().__init__(PatternBuilder(), 'pattern',  *args, **kwargs)

#
# class PatternParser(BaseElementParser):
#
#     def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
#         builder = PatternBuilder()
#
#         for action, element in iterparser:
#             local_name = etree.QName(element.tag).localname
#
#             if action == ITERPARSE_START_TAG:
#                 if local_name in ['rule', 'let']:
#                     element_type = self._parser_factory.get_schematron_element(local_name)
#                     sub_parser = self._parser_factory.get_parser(element_type)
#                     builder.add_child(sub_parser.parse(iterparser))
#
#             elif action == ITERPARSE_END_TAG:
#                 builder.set_id(element.attrib.get('id'))
#                 self._iterparser_clear_memory(element)
#                 break
#
#         return builder.build()


class RuleParser(BaseElementParser):

    def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
        builder = RuleBuilder()

        for action, element in iterparser:
            local_name = etree.QName(element.tag).localname

            if action == ITERPARSE_START_TAG:
                if local_name in ['assert', 'report']:
                    element_type = self._parser_factory.get_schematron_element(local_name)
                    sub_parser = self._parser_factory.get_parser(element_type)
                    builder.add_test(sub_parser.parse(iterparser))
                elif local_name == 'let':
                    element_type = self._parser_factory.get_schematron_element(local_name)
                    sub_parser = self._parser_factory.get_parser(element_type)
                    builder.add_variable(sub_parser.parse(iterparser))

            elif action == ITERPARSE_END_TAG:
                builder.set_context(element.attrib.get('context'))
                self._iterparser_clear_memory(element)
                break

        return builder.build()


class TestParser(BaseElementParser):
    """Base parser for the Schematron rules Assert and Report.

    To implement, the tag name must be defined and the :meth:`get_builder` method implemented.
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
    def get_builder(self) -> TestBuilder:
        """Get the builder we will use for this parser.

        Returns:
            The builder we will use for building this element.
        """


class AssertParser(TestParser):
    tag_name: str = 'assert'

    def get_builder(self) -> TestBuilder:
        return AssertBuilder()


class ReportParser(TestParser):
    tag_name: str = 'report'

    def get_builder(self) -> TestBuilder:
        return ReportBuilder()


class VariableParser(BaseElementParser):

    def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
        builder = VariableBuilder()

        for action, element in iterparser:
            local_name = etree.QName(element.tag).localname

            if local_name != 'let':
                raise ValueError(f'Unknown element {local_name} in parsing.')

            if action == ITERPARSE_END_TAG:
                builder.set_name(element.attrib.get('name'))
                builder.set_value(element.attrib.get('value'))
                self._iterparser_clear_memory(element)
                break

        return builder.build()



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

# print(PatternParser().parse(Path('/tmp/example.xml')))
# exit()
print(PatternParser().parse('''
<pattern id="test">
    <let name="animalSpecies" value="ark:species"/>
    <rule context="//ad:altoida_data/ad:metadata/ad:session/ad:datetime">
        <let name="roat" value="'roat'"/>
        <assert test="xs:dateTime(@local) = xs:dateTime(@utc)">
            Start <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards.
        </assert>
        <report
            test="//notes"
            id="unique-id">
            String with a value: <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards Report.
        </report>
    </rule>
</pattern>
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
    String with a value: <value-of select="note/to/text()"/>, <p>and</p> something <value-of select="note/to/text()"/> afterwards Report.
</report>'''
report = ReportParser().parse(report_str)
print(report)

xml_writer = JinjaXMLWriter()
print(xml_writer.to_string(report))




# import elementpath
# import lxml.etree as etree
#
# xml = etree.fromstring('''
# <html>
#     <body>
#         <p>Test</p>
#     </body>
# </html>
# ''')
#
# variables = {'node': 'html'}
#
# p_node = elementpath.select(xml, '//html/body/p')[0]
# parent_selector = elementpath.select(xml, '//*[name()=$node]', item=p_node, variables=variables)
# print(parent_selector)
