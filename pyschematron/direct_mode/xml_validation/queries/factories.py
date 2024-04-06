from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-03-25'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from typing import override

from pyschematron.direct_mode.schematron.ast import Schema
from pyschematron.direct_mode.xml_validation.queries.base import QueryProcessor
from pyschematron.direct_mode.xml_validation.queries.xpath import XPath1QueryParser, XPath2QueryParser, \
    XPath3QueryParser, XPath31QueryParser, XPathQueryProcessor


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
    def has_query_processor(self, query_binding: str) -> bool:
        """Check if we have a processor for the specific query binding language.

        Args:
            query_binding: the query binding for which we want to check if a processor is available.

        Returns:
            True if we have a processor, False otherwise.
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


class DefaultQueryProcessorFactory(QueryProcessorFactory):

    def __init__(self):
        """The default query processor factory.

        This factory only supports XSLT and XPath query languages. The XSLT query binding is additionally limited
        to XPath expressions.
        """
        self._query_processors = {
            'xslt': XPathQueryProcessor(XPath1QueryParser()),
            'xslt2': XPathQueryProcessor(XPath2QueryParser()),
            'xslt3': XPathQueryProcessor(XPath3QueryParser()),
            'xpath': XPathQueryProcessor(XPath1QueryParser()),
            'xpath2': XPathQueryProcessor(XPath2QueryParser()),
            'xpath3': XPathQueryProcessor(XPath3QueryParser()),
            'xpath31': XPathQueryProcessor(XPath31QueryParser()),
        }

    @override
    def get_query_processor(self, query_binding: str) -> QueryProcessor:
        try:
            return self._query_processors[query_binding]
        except KeyError:
            raise ValueError(f'No parser could be found for the query binding "{query_binding}".')

    @override
    def has_query_processor(self, query_binding: str) -> bool:
        return query_binding in self._query_processors

    @override
    def get_schema_query_processor(self, schema: Schema) -> QueryProcessor:
        query_binding = schema.query_binding or 'xslt'
        namespaces = {ns.prefix: ns.uri for ns in schema.namespaces}

        processor = self.get_query_processor(query_binding)
        return processor.with_namespaces(namespaces)


class ExtendableQueryProcessorFactory(DefaultQueryProcessorFactory):

    def __init__(self):
        """An extendable query processor factory.

        This has all the processors from the default query processor factory, but allows extending and/or overwriting
        these using getters and setters.
        """
        super().__init__()

    def set_query_processor(self, query_binding: str, query_processor: QueryProcessor):
        """Set the query processor to use for a specific query binding language.

        Args:
            query_binding: the query binding we wish to add / overwrite.
            query_processor: the query processor we would like to use for this query binding.
        """
        self._query_processors[query_binding] = query_processor
