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
from typing import BinaryIO, Any, Union, Type, Dict

import lxml
from elementpath import Selector
from lxml import etree

from elements import Assert, SchematronElement, Namespace, Variable, Phase, Pattern, Schema
from pyschematron.builders import AssertBuilder

from elementpath.xpath31 import XPath31Parser


class ParserFactory(metaclass=ABCMeta):
    """Create Schematron element parsers for the different Schematron elements.

    This allows subclassing the :class:`SchematronElement` elements and have a dedicated parser for the
    new subclass without having to go through a deep class hierarchy.

    For example, suppose you subclass the element "Assert" as "MyAssert" with some additional metadata.
    When parsing, you could reuse most of the parsing code and have the factory::

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

    def get_parser(self, schematron_element: Type[SchematronElement]) -> SchematronElementParser:
        parser_mapping: Dict[Type[SchematronElement], SchematronElementParser] = {
            # Schema: SchemaParser(),
            Assert: AssertParser()
        }

        return parser_mapping[schematron_element]

# #
# # class SchematronParser(metaclass=ABCMeta):
# #
# #     @abstractmethod
# #     def parse(self, xml_data: Union[bytes, str, Path, BytesIO, lxml.etree.iterparse]) -> SchematronElement:
# #         """Parse a piece of XML data into a SchematronElement.
# #
# #         Args:
# #             xml_data: the XML data we want to parse. Can be in different formats and this class
# #                 will switch behaviour based on the input
# #         """
# #
# #
# # class BaseSchematronParser(SchematronParser):
# #
# #     def __init__(self, parser_mapping: ParserMapping = DefaultParserMapping()):
# #         """Standard base class for a schematron parser.
# #
# #         This base class allows specifying a :class:`ParserMapping` which allows specifying which
# #         exact :class:`SchematronElement` gets created (for instance, when subclassing some parts).
# #
# #         Args:
# #             parser_mapping: the parser mapping to use for sub-elements.
# #         """
# #         self.parser_mapping = parser_mapping or DefaultParserMapping()
# #
# #     def parse(self, xml_data: Union[bytes, str, Path, BytesIO, lxml.etree.iterparse]) -> SchematronElement:
# #         match xml_data:
# #             case BytesIO():
# #                 return self.parse(etree.iterparse(xml_data, events=['start', 'end']))
# #             case lxml.etree.iterparse():
# #                 return self.iterparse(xml_data)
# #             case bytes():
# #                 return self.parse(BytesIO(xml_data))
# #             case str():
# #                 return self.parse(BytesIO(xml_data.encode('utf-8')))
# #             case Path():
# #                 with open(xml_data, 'rb') as f:
# #                     return self.parse(f)
#

class SchematronElementParser(metaclass=ABCMeta):
    """Abstract base class for a schematron element parser.

    These parsers take in a part of a Schematron XML file and parse it into a :class:`SchematronElement`.
    """

    @abstractmethod
    def parse(self, xml_data: Union[bytes, str, Path, BytesIO, lxml.etree.iterparse]) -> SchematronElement:
        """Parse a piece of XML data into a SchematronElement.

        Args:
            xml_data: the XML data we want to parse. Can be in different formats and this class
                will switch behaviour based on the input
        """


# class BaseSchematronElementParser(SchematronElementParser, metaclass=ABCMeta):
#
#     def __init__(self, parser_mapping: ParserMapping = None):
#         """Standard base class for schematron element parsers.
#
#         This base class allows specifying a :class:`ParserMapping` which allows specifying which
#         exact :class:`SchematronElement` gets created (for instance, when subclassing some parts).
#
#         Args:
#             parser_mapping: the parser mapping to use for sub-elements.
#         """
#         self.parser_mapping = parser_mapping or DefaultParserMapping()
#
#     def parse(self, xml_data: Union[bytes, str, Path, BytesIO, lxml.etree.iterparse]) -> SchematronElement:
#         match xml_data:
#             case BytesIO():
#                 return self.parse(etree.iterparse(xml_data, events=['start', 'end']))
#             case lxml.etree.iterparse():
#                 return self.iterparse(xml_data)
#             case bytes():
#                 return self.parse(BytesIO(xml_data))
#             case str():
#                 return self.parse(BytesIO(xml_data.encode('utf-8')))
#             case Path():
#                 with open(xml_data, 'rb') as f:
#                     return self.parse(f)
#
#     @abstractmethod
#     def iterparse(self, iterparser: lxml.etree.iterparse) -> SchematronElement:
#         """Parse a piece of XML using the iterparser from the lxml etree library.
#
#         The iterparser will provide start and end tags of any element. Note that the implementing class
#         is responsible for clearing the memory after having parsed the elements.
#
#         Args:
#              iterparser: the iterative parser we can use to load the XML
#         """
#
#     def _iterparser_clear_memory(self, element):
#         """Helper routine to clear memory of an element used in an iterparser.
#         """
#         element.clear()
#         # Also eliminate now-empty references from the root node to elem
#         for ancestor in element.xpath('ancestor-or-self::*'):
#             while ancestor.getprevious() is not None:
#                 del ancestor.getparent()[0]
# #
# #
# # class SchemaParser(SchematronElementParser):
# #
# #     def __init__(self, subparsers: dict[str, SchematronElementParser]):
# #         self.subparsers = {'ns': NamespaceParser(),
# #                            'pattern': PatternParser()}
# #
# #     def iterparse(self, iterparser):
# #         builder = SchemaBuilder()
# #         for action, element in iterparser:
# #             print('schemaparser', action, element)
# #
# #             local_name = etree.QName(element.tag).localname
# #
# #             match local_name:
# #                 case 'ns':
# #                     namespaces.append(self.subparsers['ns'].parse(iterparser))
# #                 case 'pattern':
# #                     patterns.append(self.subparsers['pattern'].parse(iterparser))
# #             self._iterparser_clear_memory()
# #         builder.build()
# #
# #
# #
# # class NamespaceParser(SchematronElementParser):
# #
# #     def __init__(self):
# #         super().__init__({})
# #
# #     # def construct(self, element):
# #     #     print(self.__class__.__name__, element)
# #
# #     def iterparse(self, iterparser):
# #         for action, element in iterparser:
# #             print('namespaceparser', action, element)
# #             if action == 'end':
# #                 return Namespace('test', 'test')
#
# #
# # class PatternParser(SchematronElementParser):
# #
# #     def __init__(self):
# #         super().__init__({})
# #
# #     # def construct(self, element):
# #     #     print(self.__class__.__name__, element)
# #
# #     def iterparse(self, iterparser):
# #         for action, element in iterparser:
# #
# #
# #
# #             print('patternparser', action, element)
# #             if action == 'end':
# #                 return Namespace('test', 'test')
#
#

class AssertParser(BaseSchematronElementParser):

    def __init__(self, parser_mapping: ParserMapping = None):
        super().__init__(parser_mapping)
        self.selectors = {
            'test': Selector('@test'),
            'id': Selector('@id'),
            'message': Selector('./text()|./element()')
        }

    def iterparse(self, iterparser):
        builder = AssertBuilder()

        message_selector = Selector('./text()|./element()')

        for action, element in iterparser:
            local_name = etree.QName(element.tag).localname

            if action == 'end':
                if local_name == 'assert':
                    print(message_selector.select(element))
                    builder.add_message_part(element.text)
                else:
                    builder.add_message_part(element)
                    builder.add_message_part(element.tail)

            # self._iterparser_clear_memory(element)
        print(message)
#
# class SchematronParser:
#
#     def __init__(self, semantics: SchematronParserSemantics):
#         """Create a Schematron parser using the provided semantics.
#
#         The job of this class is to parse the Schematron XML and call the semantics for each node.
#
#         Args:
#              semantics: the semantics we want to use for this Schematron parser.
#         """
#         self._semantics = semantics
#
#     def parse_from_bytes(self, xml_data: bytes) -> SchematronElement:
#         """Parse a Schematron XML from a byte string.
#
#         Args:
#             xml_data: the XML data we want to parse
#
#         Returns:
#             A Python representation of the Schematron
#
#         Raises:
#             ValueError if no Schematron element could be parsed.
#         """
#         return self._parse(BytesIO(xml_data))
#
#     def parse_from_string(self, xml_data: str) -> SchematronElement:
#         """Parse a Schematron XML from a string.
#
#         Args:
#             xml_data: the XML data we want to parse
#
#         Returns:
#             A Python representation of the Schematron
#
#         Raises:
#             ValueError if no Schematron element could be parsed.
#         """
#         return self.parse_from_bytes(xml_data.encode('utf-8'))
#
#     def parse_from_file(self, xml_file: Path | BinaryIO) -> SchematronElement:
#         """Parse a Schematron XML from a path.
#
#         Args:
#             xml_file: either a Path or an open file handle
#
#         Returns:
#             A Python representation of the Schematron
#
#         Raises:
#             ValueError if no Schematron element could be parsed.
#         """
#         if isinstance(xml_file, Path):
#             with open(xml_file, 'rb') as f:
#                 return self._parse(f)
#         return self._parse(xml_file)
#
#     def _parse(self, xml_data: BinaryIO) -> SchematronElement:
#         """Parse the provided XML data.
#
#         Args:
#             xml_data: the XML data to parse
#
#         Returns:
#             The parsed schematron element, or None if None found.
#
#         Raises:
#             ValueError if no Schematron element could be parsed.
#         """
#         ast = []
#         current_tag = None
#         for action, element in etree.iterparse(xml_data, events=['start', 'end']):
#             if action == 'start':
#                 current_tag = element.tag
#
#
#             name = etree.QName(element.tag).localname
#
#             if hasattr(self._semantics, f'handle_{name}'):
#                 action = getattr(self._semantics, f'handle_{name}')
#                 ast = action(SchematronAST(element, ast))
#                 children.append(ast)
#
#             element.clear()
#
#         if not ast:
#             raise ValueError('Could not find any schematron element in the provided data.')
#         return ast
#
#
# @dataclass
# class SchematronAST:
#     node: Any
#     children: list[Any]
#     #
#     # def __init__(self, node: Any, children: list[Any]):
#     #     """The constructed AST"""
#     #     self.node = node
#     #     self.children = children
#
#
# class SchematronParserSemantics(metaclass=ABCMeta):
#     """Semantics for a Schematron parser.
#     """
#
#     def handle_pattern(self, ast):
#         return ast
#
#     def handle_rule(self, ast):
#         return ast
#
#     def handle_assert(self, ast):
#
#         # Assert.from_xml(ast)
#         return ast
#
#
# parser = SchematronParser(SchematronParserSemantics())
#


# with open(Path('/home/robbert/programming/python/altoida/altoida_data_file/'
#                             'altoida_data_file/data/xml_schemas/v0.5.1/altoida_data.sch'), 'rb') as f:
#     parser.parse_from_file(f)



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

# PatternParser().parse('''
# <pattern>
#     <rule context="//ad:altoida_data/ad:metadata/ad:session/ad:datetime">
#         <assert test="xs:dateTime(@local) = xs:dateTime(@utc)">
#             The local and UTC datetime's do not agree.
#         </assert>
#     </rule>
# </pattern>
# ''')

xml_test = '''<?xml version="1.0" encoding="UTF-8"?>
<notes>
    <note>
      <to>Jane</to>
      <from>John</from>
      <heading>Test</heading>
      <body>This is a test</body>
    </note>
    <note>
        <to>John></to>
        <from>Jane</from>
        <heading>Test back</heading>
        <body>This is a test back</body>
    </note>
</notes>
'''

assert_str = '''
<assert
    test="//notes"
    id="unique-id">
    String with a value: <value-of select="note/to/text()"/>, and something <value-of select="note/to/text()"/> afterwards.
</assert>'''
AssertParser().parse(assert_str)

# v = parser.parse_from_string(test)
# pprint(v)



# query = XPath31Parser().parse('array { (./text()|./element()) }')


