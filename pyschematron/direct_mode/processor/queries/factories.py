__author__ = 'Robbert Harms'
__date__ = '2023-03-25'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod

from pyschematron.direct_mode.processor.queries.base import QueryParser, EvaluationContext
from pyschematron.direct_mode.processor.queries.xpath_elementpath import XPath1QueryParser, XPath2QueryParser, \
    XPath3QueryParser, XPath31QueryParser, XPathEvaluationContext


class QueryParserFactory(metaclass=ABCMeta):
    """Base class for query parser factories.

    In Schematron, the queryBinding attribute determines which query language is used. This factory
    allows you to get the right parser for your query binding language.
    """

    @abstractmethod
    def get_query_parser(self, query_binding: str) -> QueryParser:
        """Get the query parser for the specified query binding.

        Args:
            query_binding: the query binding for which we want to get a parser.

        Raises:
            ValueError: if no parser could be found for the indicated query binding.
        """


class EvaluationContextFactory(metaclass=ABCMeta):
    """Base class for evaluation context factories.

    In Schematron, the queryBinding attribute determines which query language is used. This factory
    allows you to get the right evaluation context matching the query parser.
    """

    @abstractmethod
    def get_evaluation_context(self, query_binding: str) -> EvaluationContext:
        """Get the evaluation context for the specified query binding.

        Args:
            query_binding: the query binding for which we want to get the evaluation context.

        Raises:
            ValueError: if no evaluation context could be found for the indicated query binding.
        """



class DefaultQueryParserFactory(QueryParserFactory):

    def __init__(self):
        """The default query parser factory.

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

    def get_query_parser(self, query_binding: str) -> QueryParser:
        try:
            return self._parsers[query_binding]
        except KeyError:
            raise ValueError(f'No parser could be found for the query binding "{query_binding}".')


class DefaultEvaluationContextFactory(EvaluationContextFactory):

    def __init__(self):
        """The default evaluation context factory.

        The evaluation contexts provided by this class should match those of the :class:`DefaultQueryParserFactory`.
        """
        self._contexts = {
            'xslt': XPathEvaluationContext(),
            'xslt2': XPathEvaluationContext(),
            'xslt3': XPathEvaluationContext(),
            'xpath': XPathEvaluationContext(),
            'xpath2': XPathEvaluationContext(),
            'xpath3': XPathEvaluationContext(),
            'xpath31': XPathEvaluationContext()
        }

    def get_evaluation_context(self, query_binding: str) -> EvaluationContext:
        try:
            return self._contexts[query_binding]
        except KeyError:
            raise ValueError(f'No evaluation context could be found for the query binding "{query_binding}".')
