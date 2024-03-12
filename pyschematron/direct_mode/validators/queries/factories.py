from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-03-25'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from typing import override

from pyschematron.direct_mode.ast import Schema
from pyschematron.direct_mode.validators.queries.base import QueryProcessor, SimpleQueryProcessor
from pyschematron.direct_mode.validators.queries.xpath import XPath1QueryParser, XPath2QueryParser, \
    XPath3QueryParser, XPath31QueryParser, XPathEvaluationContext


class QueryProcessorFactory(metaclass=ABCMeta):
    """Query processor factories can construct QueryProcessor classes specific to your query binding language.

    In Schematron, the queryBinding attribute determines which query language is used. This factory
    allows you to get the right query processor for your query binding language.
    """

    @abstractmethod
    def get_query_processor(self, query_binding: str) -> QueryProcessor:
        """Get the processor you can use for this query binding language.

        Args:
            query_binding: the query binding for which we want to get a parser.

        Returns:
            A query processor specialized for this query binding language.

        Raises:
            ValueError: if no query processor could be found for the indicated query binding.
        """

    @abstractmethod
    def get_schema_query_processor(self, schema: Schema) -> QueryProcessor:
        """Get the processor you can use for this schema.

        Not only will this select the right query binding, it will also load the namespaces.

        Args:
            schema: the Schema for which we want to get a query processor.

        Returns:
            A query processor specialized for this Schema, with the right query binding language and
                the namespaces loaded.

        Raises:
            ValueError: if no query processor could be found for this Schema.
        """


class SimpleQueryProcessorFactory(QueryProcessorFactory):

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

    @override
    def get_query_processor(self, query_binding: str) -> QueryProcessor:
        try:
            parser = self._parsers[query_binding]
            context = self._contexts[query_binding]
            return SimpleQueryProcessor(parser, context)
        except KeyError:
            raise ValueError(f'No parser could be found for the query binding "{query_binding}".')

    @override
    def get_schema_query_processor(self, schema: Schema) -> QueryProcessor:
        query_binding = schema.query_binding or 'xslt'
        namespaces = {ns.prefix: ns.uri for ns in schema.namespaces}

        processor = self.get_query_processor(query_binding)
        return processor.with_namespaces(namespaces)
