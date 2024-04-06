from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-03-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from typing import Any, Self, override, Callable
from elementpath.tree_builders import RootArgType
from elementpath.xpath_context import ItemArgType


class QueryProcessor(metaclass=ABCMeta):
    """Interface class for the query processing classes.

    Successful query parsing requires a query parser and an evaluation context. These need to be matched to each other.
    This class ensures matching parsers and evaluation contexts.
    """

    @abstractmethod
    def get_query_parser(self) -> QueryParser:
        """Get the query parser for parsing the queries in an AST.

        Returns:
            A query parser to parse queries in the Schematron
        """

    @abstractmethod
    def get_evaluation_context(self) -> EvaluationContext:
        """Get the evaluation context for the parsed queries.

        Returns:
            An evaluation context to evaluate the parsed queries.
        """

    @abstractmethod
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        """Create a copy of this query processor with updated namespaces.

        Args:
            namespaces: a dictionary mapping namespace prefixes to URIs.

        Returns:
            An updated Query Processor.
        """

    @abstractmethod
    def with_custom_function(self, custom_function: CustomQueryFunction) -> Self:
        """Create a copy of this query processor with support for the provided custom function.

        Args:
            custom_function: the custom function to add to the parser.

        Returns:
            An updated query processor
        """


class SimpleQueryProcessor(QueryProcessor):

    def __init__(self, query_parser: QueryParser, evaluation_context: EvaluationContext):
        """Simple query processor prepared with a query parser and evaluation context.

        Defined to be immutable.

        Args:
            query_parser: the query parser this instance specialize in
            evaluation_context: the evaluation context this instance specializes in
        """
        self._query_parser = query_parser
        self._evaluation_context = evaluation_context

    @override
    def get_query_parser(self) -> QueryParser:
        return self._query_parser

    @override
    def get_evaluation_context(self) -> EvaluationContext:
        return self._evaluation_context

    @override
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        return type(self)(self._query_parser.with_namespaces(namespaces),
                          self._evaluation_context.with_namespaces(namespaces))

    @override
    def with_custom_function(self, custom_function: CustomQueryFunction) -> Self:
        return type(self)(self._query_parser.with_custom_function(custom_function),
                          self._evaluation_context)


class QueryParser(metaclass=ABCMeta):
    """Representation of a parser for Schematron queries."""

    @abstractmethod
    def parse(self, source: str) -> Query:
        """Parse an expression in the implemented query language.

        Args:
            source: the source code of the expression, in the language supported by this parser.

        Returns:
            A parsed expression in the language supported by this parser.
        """

    @abstractmethod
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        """Create a copy of this query parser with updated namespaces.

        Args:
            namespaces: a dictionary mapping namespace prefixes to URIs.

        Returns:
            An updated Query Parser.
        """

    @abstractmethod
    def with_custom_function(self, custom_function: CustomQueryFunction) -> Self:
        """Create a copy of this query parser with an additional custom query function.

        Args:
            custom_function: the custom function to add to the parser.

        Returns:
            An updated Query Parser.
        """


class CachingQueryParser(QueryParser):

    def __init__(self, query_parser: QueryParser):
        """A wrapper around a query parser enabling caching of compiled queries.

        This keeps a mapping of source strings to Queries and checks this first before compiling a query.

        Args:
            query_parser: the query parser we use for actual parsing
        """
        self._query_parser = query_parser
        self._query_cache = {}

    @override
    def parse(self, source: str) -> Query:
        return self._query_cache.setdefault(source, self._query_parser.parse(source))

    @override
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        return type(self)(self._query_parser.with_namespaces(namespaces))

    @override
    def with_custom_function(self, custom_function: CustomQueryFunction) -> Self:
        return type(self)(self._query_parser.with_custom_function(custom_function))


class CustomQueryFunction(metaclass=ABCMeta):

    @property
    @abstractmethod
    def callback(self) -> Callable[..., Any]:
        """Get the callback of this custom function.

        Returns:
            The (Python) callback function.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of this function.

        Returns:
            The name of the callable function.
        """

    @property
    @abstractmethod
    def prefix(self) -> str | None:
        """The XML prefix of this function.

        Returns:
            The XML prefix of this function
        """


class SimpleCustomQueryFunction(CustomQueryFunction):

    def __init__(self, callback: Callable[..., Any], name: str, prefix: str | None = None):
        """Simple definition of a custom query function.

        Args:
            callback: the function to call when evaluating the parsed expression
            name: the function name for use inside the query language.
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


class EvaluationContext(metaclass=ABCMeta):
    """Representation of the context required when evaluating a Query.

    Each context should be immutable. Every change constructs a new evaluation context.
    """

    @abstractmethod
    def with_xml_root(self, xml_root: RootArgType) -> Self:
        """Create a new evaluation context with the XML root node we can use for dynamic queries.

        For queries like: `xs:integer(42)` no XML root node is needed.
        For dynamic queries like: `xs:integer(/data/@nmr_items)`, a root node is needed.

        Args:
            xml_root: the root node usable for dynamic query evaluations

        Returns:
            A new evaluation context
        """

    @abstractmethod
    def with_context_item(self, xml_item: ItemArgType) -> Self:
        """Create a new evaluation context with the provided xml item (node, comment, attribute) as query base.

        This is needed for asserts and reports queries which assume the context of the rule node.

        Args:
            xml_item: the XML item we use as context node for parser evaluation.

        Returns:
            A new evaluation context
        """

    @abstractmethod
    def with_namespaces(self, namespaces: dict[str, str]) -> Self:
        """Create a new evaluation context with the namespaces used during evaluation.

        Args:
            namespaces: a dictionary mapping namespace prefixes to URIs.
                This is used when namespace information is not available within document and element nodes.

        Returns:
            A new evaluation context
        """

    @abstractmethod
    def with_variables(self, variables: dict[str, Any], overwrite: bool = False) -> Self:
        """Create a new evaluation context with the namespaces used during evaluation.

        Args:
            variables: a dictionary mapping variable names (QNames) to variables. This expects the
                variables to be a parsed and evaluated value.
            overwrite: if set to True, we will overwrite any stored variables. If set to False, we update
                the dictionary of variables.

        Returns:
            A new evaluation context
        """

    @abstractmethod
    def get_xml_root(self) -> RootArgType | None:
        """Get the XML root node current in this context.

        Returns:
            The current root node. May not be set, giving None.
        """

    @abstractmethod
    def get_context_item(self) -> ItemArgType | None:
        """Get the XML node serving as the query base.

        Returns:
            The XML item we use as context node for parser evaluation. May not be set yet.
        """


class Query(metaclass=ABCMeta):
    """Representation of an executable Schematron query.

    To specialize for a new language, one must implement a specialized Context, Parser and Query.
    """

    @abstractmethod
    def evaluate(self, context: EvaluationContext | None = None) -> Any:
        """Evaluate this query.

        Args:
            context: optional context to be used during evaluation.
                The exact context and its usage is implementation defined.

        Returns:
            The results of running this query.
        """
