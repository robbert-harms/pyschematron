from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from pprint import pprint
from typing import BinaryIO, Any

from lxml import etree

from elements import Assert, SchematronElement


class SchematronParser:

    def __init__(self, semantics: SchematronParserSemantics):
        """Create a Schematron parser using the provided semantics.

        The job of this class is to parse the Schematron XML and call the semantics for each node.

        Args:
             semantics: the semantics we want to use for this Schematron parser.
        """
        self._semantics = semantics

    def parse_from_bytes(self, xml_data: bytes) -> SchematronElement:
        """Parse a Schematron XML from a byte string.

        Args:
            xml_data: the XML data we want to parse

        Returns:
            A Python representation of the Schematron

        Raises:
            ValueError if no Schematron element could be parsed.
        """
        return self._parse(BytesIO(xml_data))

    def parse_from_string(self, xml_data: str) -> SchematronElement:
        """Parse a Schematron XML from a string.

        Args:
            xml_data: the XML data we want to parse

        Returns:
            A Python representation of the Schematron

        Raises:
            ValueError if no Schematron element could be parsed.
        """
        return self.parse_from_bytes(xml_data.encode('utf-8'))

    def parse_from_file(self, xml_file: Path | BinaryIO) -> SchematronElement:
        """Parse a Schematron XML from a path.

        Args:
            xml_file: either a Path or an open file handle

        Returns:
            A Python representation of the Schematron

        Raises:
            ValueError if no Schematron element could be parsed.
        """
        if isinstance(xml_file, Path):
            with open(xml_file, 'rb') as f:
                return self._parse(f)
        return self._parse(xml_file)

    def _parse(self, xml_data: BinaryIO) -> SchematronElement:
        """Parse the provided XML data.

        Args:
            xml_data: the XML data to parse

        Returns:
            The parsed schematron element, or None if None found.

        Raises:
            ValueError if no Schematron element could be parsed.
        """
        ast = []
        current_tag = None
        for action, element in etree.iterparse(xml_data, events=['start', 'end']):
            if action == 'start':
                current_tag = element.tag


            name = etree.QName(element.tag).localname

            if hasattr(self._semantics, f'handle_{name}'):
                action = getattr(self._semantics, f'handle_{name}')
                ast = action(SchematronAST(element, ast))
                children.append(ast)

            element.clear()

        if not ast:
            raise ValueError('Could not find any schematron element in the provided data.')
        return ast


@dataclass
class SchematronAST:
    node: Any
    children: list[Any]
    #
    # def __init__(self, node: Any, children: list[Any]):
    #     """The constructed AST"""
    #     self.node = node
    #     self.children = children


class SchematronParserSemantics(metaclass=ABCMeta):
    """Semantics for a Schematron parser.
    """

    def handle_pattern(self, ast):
        return ast

    def handle_rule(self, ast):
        return ast

    def handle_assert(self, ast):

        # Assert.from_xml(ast)
        return ast



parser = SchematronParser(SchematronParserSemantics())

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

v = parser.parse_from_string(test)
pprint(v)




