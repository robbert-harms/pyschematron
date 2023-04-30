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

from typing import Any, Callable, Type
from abc import abstractmethod, ABCMeta

from elementpath import XPathToken, XPath1Parser, XPath2Parser, XPathContext
from elementpath.xpath3 import XPath3Parser
from elementpath.xpath31 import XPath31Parser
from elementpath.xpath_context import ItemArgType
from elementpath.tree_builders import RootArgType

from pyschematron.direct_mode.validators.queries.base import QueryParser, Query, EvaluationContext
from pyschematron.direct_mode.validators.queries.exceptions import MissingRootNodeError


class XPathQueryParser(QueryParser, metaclass=ABCMeta):

    @abstractmethod
    def with_custom_function(self, custom_function: CustomXPathFunction) -> XPathQueryParser:
        """Create a copy of this XPath query parser with an additional custom function.

        Args:
            custom_function: the custom function to add to the parser.

        Returns:
            An updated XPath Query Parser
        """


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
        self._parser = self._get_updated_parser()

    def parse(self, source: str) -> Query:
        xpath_token = self._parser.parse(source)
        return XPathQuery(xpath_token)

    def _get_updated_parser(self) -> XPath1Parser | XPath2Parser | XPath3Parser | XPath31Parser:
        """Get an updated parser using the defined namespaces and custom functions.

        Returns:
            An elementpath parser instance to use during parsing.
        """
        parser = self._parser_type(namespaces=self._namespaces)
        for custom_function in self._custom_functions:
            parser.external_function(custom_function.callback, custom_function.name, custom_function.prefix)
        return parser


class CustomXPathFunction(metaclass=ABCMeta):

    @property
    @abstractmethod
    def callback(self) -> Callable[..., Any]:
        """Get the callback of this custom XPath function.

        Returns:
            The (Python) callback function.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of this function.

        Returns:
            The name of the XPath callable function.
        """

    @property
    @abstractmethod
    def prefix(self) -> str | None:
        """The XPath prefix of this function.

        Returns:
            The prefix of this function
        """


class SimpleCustomXPathFunction(CustomXPathFunction):

    def __init__(self, callback: Callable[..., Any], name: str, prefix: str | None = None):
        """Simple definition of an XPath custom function.

        Args:
            callback: the function to call when evaluating the parsed expression
            name: the XPath function name
            prefix: the function's name prefix, if not provided it is set to the XPath default
                function namespace (`fn:`). This means, it may overwrite library functions.
        """
        self._callback = callback
        self._name = name
        self._prefix = prefix

    @property
    def callback(self) -> Callable[..., Any]:
        return self._callback

    @property
    def name(self) -> str:
        return self._name

    @property
    def prefix(self) -> str | None:
        return self._prefix


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


class XPath1QueryParser(ElementPathXPathQueryParser):

    def __init__(self, namespaces: dict[str, str] | None = None):
        """Query parser for XPath 1.0 expressions.

        This uses the XPath 1.0 parser of the `elementpath` library.

        Args:
             namespaces: a dictionary with namespaces to use while parsing.
        """
        super().__init__(XPath1Parser, namespaces=namespaces)

    def with_namespaces(self, namespaces: dict[str, str]) -> XPathQueryParser:
        return type(self)(self._namespaces | namespaces)

    def with_custom_function(self, custom_function: CustomXPathFunction) -> XPathQueryParser:
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

    def with_namespaces(self, namespaces: dict[str, str]) -> XPathQueryParser:
        return type(self)(self._namespaces | namespaces)

    def with_custom_function(self, custom_function: CustomXPathFunction) -> XPathQueryParser:
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

    def with_namespaces(self, namespaces: dict[str, str]) -> XPathQueryParser:
        return type(self)(self._namespaces | namespaces)

    def with_custom_function(self, custom_function: CustomXPathFunction) -> XPathQueryParser:
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

    def with_namespaces(self, namespaces: dict[str, str]) -> XPathQueryParser:
        return type(self)(self._namespaces | namespaces)

    def with_custom_function(self, custom_function: CustomXPathFunction) -> XPathQueryParser:
        return type(self)(namespaces=self._namespaces,
                          custom_functions=self._custom_functions + [custom_function])
