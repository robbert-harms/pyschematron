from __future__ import annotations

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
from elementpath.xpath_context import ItemArgType
from elementpath.xpath_nodes import RootArgType

from pyschematron.direct_mode.processor.queries.base import QueryParser, Query, EvaluationContext
from pyschematron.direct_mode.processor.queries.exceptions import MissingRootNodeError


class XPathQueryParser(QueryParser):

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

    def __init__(self,
                 root: RootArgType | None = None,
                 namespaces: dict[str, str] | None = None,
                 item: ItemArgType | None = None,
                 variables: dict[str, Any] | None = None):
        super().__init__()
        self._context_variables = {
            'root': root,
            'namespaces': namespaces,
            'item': item,
            'variables': variables
        }

        self._xpath_context = None
        if root is not None:
            self._xpath_context = XPathContext(**self._context_variables)

    def get_xpath_context(self) -> XPathContext | None:
        """Get the XPath context we can use for evaluation of a query.

        If no root node is set yet, we return None. Else, we return an XPathContext from the elementpath library.

        Returns:
             The XPath context if a root node is set, else None.

        Raises:
            MissingRootNodeError: if the XPath node could not be
        """
        if self._xpath_context is None:
            raise MissingRootNodeError('Missing root node in XPath context, please set a root node first.')
        return self._xpath_context

    def with_xml_root(self, xml_root: RootArgType) -> XPathEvaluationContext:
        return self._get_updated({'root': xml_root})

    def with_namespaces(self, namespaces: dict[str, str]) -> XPathEvaluationContext:
        return self._get_updated({'namespaces': namespaces})

    def with_variables(self, variables: dict[str, str]) -> XPathEvaluationContext:
        return self._get_updated({'variables': variables})

    def _get_updated(self, updates: dict[str, Any]) -> XPathEvaluationContext:
        kwargs = self._context_variables.copy()
        kwargs.update(updates)
        return XPathEvaluationContext(**kwargs)


class XPathQuery(Query):

    def __init__(self, xpath_token: XPathToken):
        """Representation of an XPath query.

        This uses the elementpath library for representing the XPath expressions.

        Args:
            xpath_token: the parsed XPath expression
        """
        self._xpath_token = xpath_token

    def evaluate(self, context: XPathEvaluationContext | None = None) -> Any:
        xpath_context = None
        if context:
            xpath_context = context.get_xpath_context()

        return self._xpath_token.evaluate(xpath_context)


class XPath1QueryParser(XPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None = None):
        """Query parser for XPath 1.0 expressions.

        This uses the XPath 1.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath1Parser(namespaces=namespaces))


class XPath2QueryParser(XPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None = None):
        """Query parser for XPath 2.0 expressions.

        This uses the XPath 2.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath2Parser(namespaces=namespaces))


class XPath3QueryParser(XPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None = None):
        """Query parser for XPath 3.0 expressions.

        This uses the XPath 3.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath3Parser(namespaces=namespaces))


class XPath31QueryParser(XPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None = None):
        """Query parser for XPath 3.1 expressions.

        This uses the XPath 3.1 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath31Parser(namespaces=namespaces))


