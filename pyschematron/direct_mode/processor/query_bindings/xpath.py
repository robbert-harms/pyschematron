"""The XPath query bindings use the adapter pattern around the elementpath library.

The elementpath library is used for the parsing, context and evaluation of all XPath related queries.
"""

__author__ = 'Robbert Harms'
__date__ = '2023-03-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from typing import Any

from elementpath import XPathToken, XPath1Parser, XPath2Parser, XPathContext
from elementpath.xpath3 import XPath3Parser
from elementpath.xpath31 import XPath31Parser
from elementpath.tdop import Parser
from elementpath.xpath_nodes import RootArgType

from pyschematron.direct_mode.processor.query_bindings.base import QueryParser, Query, EvaluationContext


class ElementPathXPathQueryParser(QueryParser):

    def __init__(self, parser: Parser[XPathToken]):
        """Base class for all XPath parsers in this package.

        Args:
            parser: the XPath parser from the elementpath library we are wrapping
        """
        self._parser = parser

    def parse(self, source: str) -> Query:
        xpath_token = self._parser.parse(source)
        return XPathQuery(xpath_token)


class XPathEvaluationContext(EvaluationContext):

    def __init__(self, root_node: RootArgType):
        self._xpath_context = XPathContext(root_node)

    def get_xpath_context(self):
        return self._xpath_context


class XPathQuery(Query):

    def __init__(self, xpath_token: XPathToken):
        """Representation of an XPath query.

        This uses the elementpath library for representing the XPath expressions.

        Args:
            xpath_token: the parsed XPath expression
        """
        self._xpath_token = xpath_token

    def evaluate(self, context: XPathEvaluationContext | None) -> Any:
        return self._xpath_token.evaluate(context.get_xpath_context())


class XPath1QueryParser(ElementPathXPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None):
        """Query parser for XPath 1.0 expressions.

        This uses the XPath 1.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath1Parser(namespaces=namespaces))


class XPath2QueryParser(ElementPathXPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None):
        """Query parser for XPath 2.0 expressions.

        This uses the XPath 2.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath2Parser(namespaces=namespaces))


class XPath3QueryParser(ElementPathXPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None):
        """Query parser for XPath 3.0 expressions.

        This uses the XPath 3.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath3Parser(namespaces=namespaces))


class XPath31QueryParser(ElementPathXPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None):
        """Query parser for XPath 3.1 expressions.

        This uses the XPath 3.1 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath31Parser(namespaces=namespaces))


