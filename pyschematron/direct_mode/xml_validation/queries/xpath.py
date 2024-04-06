from __future__ import annotations

"""The XPath query bindings.

This uses the adapter pattern around the elementpath library.

The elementpath library is used for the parsing, context and evaluation of all XPath related queries.
"""

__author__ = 'Robbert Harms'
__date__ = '2023-03-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from typing import Any, Type, Self, override
from abc import ABCMeta

from elementpath import XPathToken, XPath1Parser, XPath2Parser, XPathContext
from elementpath.xpath3 import XPath3Parser
from elementpath.xpath31 import XPath31Parser
from elementpath.xpath_context import ItemArgType
from elementpath.tree_builders import RootArgType

from pyschematron.direct_mode.xml_validation.queries.base import QueryParser, Query, EvaluationContext, \
    SimpleQueryProcessor, CustomQueryFunction, SimpleCustomQueryFunction
from pyschematron.direct_mode.xml_validation.queries.exceptions import MissingRootNodeError


class XPathQueryProcessor(SimpleQueryProcessor):

    def __init__(self, query_parser: XPathQueryParser, evaluation_context: EvaluationContext = None):
        """Query processor for XPath queries.

        This is simply a wrapper around the simple query processor, with as default evaluation context the XPath
        evaluation context.

        Args:
            query_parser: the (XPath) query processor to use
            evaluation_context: the evaluation context, defaults to the XPath evaluation context
        """
        super().__init__(query_parser, evaluation_context or XPathEvaluationContext())


class XPathQueryParser(QueryParser, metaclass=ABCMeta):
    """Wrapper around the query parser to indicate specialization for XPath query parsers."""


class ElementPathXPathQueryParser(XPathQueryParser, metaclass=ABCMeta):

    def __init__(self,
                 parser_type: Type[XPath1Parser | XPath2Parser | XPath3Parser | XPath31Parser],
                 namespaces: dict[str, str] | None = None,
                 custom_functions: list[CustomXPathFunction] | None = None):
        """Base class for XPath parsers wrapping the `elementpath` library.

        Args:
            parser_type: the type of XPath parser from the elementpath library we are wrapping
            namespaces: namespaces to use during parsing
            custom_functions: the list of custom functions to load
        """
        self._parser_type = parser_type
        self._namespaces = namespaces or {}
        self._custom_functions = custom_functions or []
        self._parser = self._get_elementpath_parser()

    @override
    def parse(self, source: str) -> Query:
        xpath_token = self._parser.parse(source)
        return XPathQuery(xpath_token)

    def _get_elementpath_parser(self) -> XPath1Parser | XPath2Parser | XPath3Parser | XPath31Parser:
        """Get an elementpath parser using the defined namespaces and custom functions.

        Returns:
            An elementpath parser instance to use during parsing.
        """
        parser = self._parser_type(namespaces=self._namespaces)
        for custom_function in self._custom_functions:
            parser.external_function(custom_function.callback, custom_function.name, custom_function.prefix)
        return parser


class CustomXPathFunction(CustomQueryFunction, metaclass=ABCMeta):
    """Wrapper around the custom query functions to specify functions for use in XPath query parsers."""


class SimpleCustomXPathFunction(CustomXPathFunction, SimpleCustomQueryFunction):
    """Simple definition of an XPath custom function."""


class XPathEvaluationContext(EvaluationContext):

    def __init__(self,
                 root: RootArgType | None = None,
                 namespaces: dict[str, str] | None = None,
                 item: ItemArgType | None = None,
                 variables: dict[str, Any] | None = None):
        super().__init__()
        self._context_variables = {
            'root': root,
            'namespaces': namespaces or {},
            'item': item,
            'variables': variables or {}
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

    @override
    def with_context_item(self, xml_item: ItemArgType) -> Self:
        if xml_item is self._context_variables['item']:
            return self
        return self._get_updated({'item': xml_item})

    @override
    def with_xml_root(self, xml_root: RootArgType) -> Self:
        if xml_root is self._context_variables['root']:
            return self
        return self._get_updated({'root': xml_root})

    @override
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        return self._get_updated({'namespaces': namespaces})

    @override
    def with_variables(self, variables: dict[str, Any], overwrite: bool = False) -> Self:
        if overwrite:
            return self._get_updated({'variables': variables})
        else:
            return self._get_updated({'variables': self._context_variables['variables'] | variables})

    @override
    def get_xml_root(self) -> RootArgType | None:
        return self._context_variables['root']

    @override
    def get_context_item(self) -> ItemArgType | None:
        return self._context_variables['item']

    def _get_updated(self, updates: dict[str, Any]) -> Self:
        kwargs = self._context_variables.copy()
        kwargs.update(updates)
        return type(self)(**kwargs)


class XPathQuery(Query):

    def __init__(self, xpath_token: XPathToken):
        """Representation of an XPath query.

        This uses the elementpath library for representing the XPath expressions.

        Args:
            xpath_token: the parsed XPath expression
        """
        self._xpath_token = xpath_token

    @override
    def evaluate(self, context: XPathEvaluationContext | None = None) -> Any:
        xpath_context = None
        if context:
            xpath_context = context.get_xpath_context()

        return self._xpath_token.evaluate(xpath_context)


class XPath1QueryParser(ElementPathXPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None = None):
        """Query parser for XPath 1.0 expressions.

        This uses the XPath 1.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath1Parser, namespaces=namespaces)

    @override
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        return type(self)(self._namespaces | namespaces)

    @override
    def with_custom_function(self, custom_function: CustomXPathFunction) -> Self:
        raise ValueError('Custom functions are not supported for XPath1 parsers.')


class XPath2QueryParser(ElementPathXPathQueryParser):

    def __init__(self,
                 namespaces: dict[str, str] | None = None,
                 custom_functions: list[CustomXPathFunction] | None = None):
        """Query parser for XPath 2.0 expressions.

        This uses the XPath 2.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
             custom_functions: the list of custom functions to load
        """
        super().__init__(XPath2Parser, namespaces=namespaces, custom_functions=custom_functions)

    @override
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        return type(self)(self._namespaces | namespaces,
                          custom_functions=self._custom_functions)

    @override
    def with_custom_function(self, custom_function: CustomXPathFunction) -> Self:
        return type(self)(namespaces=self._namespaces,
                          custom_functions=self._custom_functions + [custom_function])


class XPath3QueryParser(ElementPathXPathQueryParser):

    def __init__(self,
                 namespaces: dict[str, str] | None = None,
                 custom_functions: list[CustomXPathFunction] | None = None):
        """Query parser for XPath 3.0 expressions.

        This uses the XPath 3.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
             custom_functions: the list of custom functions to load
        """
        super().__init__(XPath3Parser, namespaces=namespaces, custom_functions=custom_functions)

    @override
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        return type(self)(self._namespaces | namespaces,
                          custom_functions=self._custom_functions)

    @override
    def with_custom_function(self, custom_function: CustomXPathFunction) -> Self:
        return type(self)(namespaces=self._namespaces,
                          custom_functions=self._custom_functions + [custom_function])


class XPath31QueryParser(ElementPathXPathQueryParser):

    def __init__(self,
                 namespaces: dict[str, str] | None = None,
                 custom_functions: list[CustomXPathFunction] | None = None):
        """Query parser for XPath 3.1 expressions.

        This uses the XPath 3.1 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
             custom_functions: the list of custom functions to load
        """
        super().__init__(XPath31Parser, namespaces=namespaces, custom_functions=custom_functions)

    @override
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        return type(self)(self._namespaces | namespaces,
                          custom_functions=self._custom_functions)

    @override
    def with_custom_function(self, custom_function: CustomXPathFunction) -> Self:
        return type(self)(namespaces=self._namespaces,
                          custom_functions=self._custom_functions + [custom_function])
