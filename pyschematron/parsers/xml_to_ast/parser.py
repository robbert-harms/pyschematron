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
    ConcreteRule, AbstractRule, ExtendsById, Extends, ExtendsExternal, ExternalRule, XPath, XPathVariable, XMLVariable
from pyschematron.parsers.xml_to_ast.builders import ConcreteRuleBuilder, ExternalRuleBuilder, AbstractRuleBuilder, \
    ConcretePatternBuilder
from pyschematron.parsers.xml_to_ast.utils import node_to_str, resolve_href
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
            'pattern': PatternParser()
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
    def get_rich_content(element: _Element) -> list[str | XPath]:
        """Get the rich content of the provided node.

        Args:
            element: the element for which to get the content.
            context: the parsing context, we use this to parse <value-of> nodes.

        Returns:
            A list of text and XPath nodes. All rich content like <emph> and <b> are rendered as string content.
                Nodes of type <value-of> are converted into XPath nodes.
        """
        content = [element.text]

        for child in element.getchildren():
            if child.tag == '{http://purl.oclc.org/dsdl/schematron}value-of':
                content.append(XPath(child.attrib['select']))
                content.append(child.tail)
            else:
                content.append(node_to_str(child))
                content.append(child.tail)

        return content


class PatternParser(ElementParser):
    """Parse <pattern> tags."""

    def parse(self, element: _Element, context: ParsingContext) -> Pattern:
        # is_abstract = element.attrib.get('abstract', 'false') == 'true'
        # loaded_external = element.attrib.get('context') is None
        #
        # if is_abstract:
        #     builder = AbstractRuleBuilder()
        # elif loaded_external:
        #     builder = ExternalRuleBuilder()
        # else:
        builder = ConcretePatternBuilder()

        builder.add_attributes(element.attrib)
        builder.add_rules(self._parse_child_tags(element, context, 'rule'))
        builder.add_variables(self._parse_child_tags(element, context, 'let'))
        # builder.add_paragraphs(self._parse_child_tags(element, context, 'p'))
        # builder.add_extends(self._parse_child_tags(element, context, 'extends'))

        # for include_node in self._parse_child_tags(element, context, 'include'):
        #     match include_node:
        #         case Check():
        #             builder.add_checks([include_node])
        #         case Variable():
        #             builder.add_variables([include_node])
        #         case Paragraph():
        #             builder.add_paragraphs([include_node])
        #         case Extends():
        #             builder.add_extends([include_node])

        return builder.build()




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

        content = []
        if element.text:
            content.append(element.text)

        for child in element.getchildren():
            content.append(node_to_str(child, remove_namespaces=False))

            if child.tail:
                content.append(child.tail)

        return XMLVariable(name=element.attrib['name'], value=''.join(content))


class ParagraphParser(ElementParser):
    """Parse <p> tags."""

    def parse(self, element: _Element, context: ParsingContext) -> Paragraph:
        kwargs = {
            'content': self.get_rich_content(element)
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
            'test': XPath(element.attrib['test']),
            'content': self.get_rich_content(element)
        }

        if 'diagnostics' in element.attrib:
            kwargs['diagnostics'] = element.attrib['diagnostics'].split(' ')

        if 'properties' in element.attrib:
            kwargs['properties'] = element.attrib['properties'].split(' ')

        if 'subject' in element.attrib:
            kwargs['subject'] = XPath(element.attrib['subject'])

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
            <let name="open_item"><data xmlns="http://test.nl">test</data></let>
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
            <extends href="../../../tests/fixtures/extends_example.xml" />
            <include href="../../../tests/fixtures/rule_include_example.xml" />
        </rule>
        <rule context="lions">
            <report id="some_report" test="@alpha">Some alpha test</report>
        </rule>
    </pattern>
</schema>
'''


schematron_xml = load_xml(test)
parsing_context = ParsingContext()

# assert_parser = parsing_context.parser_factory.get_parser('assert')
assert_parser = PatternParser()
element = assert_parser.parse(elementpath.select(schematron_xml, '/schema/pattern')[0], parsing_context)

pprint(element)

# from dataclasses import dataclass, asdict
# print(asdict(element))

print()


# builder = SchemaBuilder()
# schema = builder.build()
