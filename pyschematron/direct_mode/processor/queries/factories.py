from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-03-25'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod

from pyschematron.direct_mode.processor.queries.base import QueryParser, EvaluationContext
from pyschematron.direct_mode.processor.queries.xpath_query_binding import XPath1QueryParser, XPath2QueryParser, \
    XPath3QueryParser, XPath31QueryParser, XPathEvaluationContext


class QueryBindingFactory(metaclass=ABCMeta):
    """Base class for query binding factories.

    In Schematron, the queryBinding attribute determines which query language is used. This factory
    allows you to get the right query factory for your query binding language.

    This is part of the `abstract factory` design pattern. This factory generates factories to create the
    query parser and evaluation context specialized to a specific query binding.
    """

    @abstractmethod
    def get_query_processing_factory(self, query_binding: str) -> QueryProcessingFactory:
        """Get the factory you can use to get the query parser and evaluation context for your query binding.

        The first factory (this one) allows you to generate specialized factories for specific query bindings.

        Args:
            query_binding: the query binding for which we want to get a parser.

        Returns:
            A query processing factory specialized for this query binding language.

        Raises:
            ValueError: if no query processing factory could be found for the indicated query binding.
        """


class DefaultQueryBindingFactory(QueryBindingFactory):

    def __init__(self):
        """The default query binding factory.

        This factory only supports XSLT and XPath query languages. The XSLT query binding is additionally limited
        to XPath expressions.
        """
        self._parsers = {
            'xslt': XPath1QueryParser(),
            'xslt2': XPath2QueryParser(),
            'xslt3': XPath3QueryParser(),
            'xpath': XPath1QueryParser(),
            'xpath2': XPath2QueryParser(),
            'xpath3': XPath3QueryParser(),
            'xpath31': XPath31QueryParser()
        }
        self._contexts = {
            'xslt': XPathEvaluationContext(),
            'xslt2': XPathEvaluationContext(),
            'xslt3': XPathEvaluationContext(),
            'xpath': XPathEvaluationContext(),
            'xpath2': XPathEvaluationContext(),
            'xpath3': XPathEvaluationContext(),
            'xpath31': XPathEvaluationContext()
        }

    def get_query_processing_factory(self, query_binding: str) -> QueryProcessingFactory:
        try:
            parser = self._parsers[query_binding]
            context = self._contexts[query_binding]
            return SimpleQueryProcessingFactory(parser, context)
        except KeyError:
            raise ValueError(f'No parser could be found for the query binding "{query_binding}".')


class QueryProcessingFactory(metaclass=ABCMeta):
    """Specialized query processing factory.

    This provides you with a query parser and evaluation context which match with each other.
    """

    @abstractmethod
    def get_query_parser(self) -> QueryParser:
        """Get the query parser for the bound query binding.

        Returns:
            A query parser to parse queries in the Schematron
        """

    @abstractmethod
    def get_evaluation_context(self) -> EvaluationContext:
        """Get the evaluation context for the bound query binding.

        Returns:
            An evaluation context to evaluate the parsed queries.
        """


class SimpleQueryProcessingFactory(QueryProcessingFactory):

    def __init__(self, query_parser: QueryParser, evaluation_context: EvaluationContext):
        """Simple query processing factory specialized to a specific query parser and evaluation context.

        Args:
            query_parser: the query parser this instance specialize in
            evaluation_context: the evaluation context this instance specializes in
        """
        self._query_parser = query_parser
        self._evaluation_context = evaluation_context

    def get_query_parser(self) -> QueryParser:
        return self._query_parser

    def get_evaluation_context(self) -> EvaluationContext:
        return self._evaluation_context
