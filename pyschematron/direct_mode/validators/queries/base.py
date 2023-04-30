from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-03-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from typing import Any

from elementpath.tree_builders import RootArgType


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
    def with_namespaces(self, namespaces: dict[str, str]) -> QueryParser:
        """Create a copy of this query parser with updated namespaces.

        Args:
            namespaces: a dictionary mapping namespace prefixes to URIs.

        Returns:
            An updated Query Parser.
        """


class EvaluationContext(metaclass=ABCMeta):
    """Representation of the context required when evaluating a Query.

    Each context should be immutable. Every change constructs a new evaluation context.
    """

    @abstractmethod
    def with_xml_root(self, xml_root: RootArgType) -> EvaluationContext:
        """Create a new evaluation context with the XML root node we can use for dynamic queries.

        For queries like: `xs:integer(42)` no XML root node is needed.
        For dynamic queries like: `xs:integer(/data/@nmr_items)`, a root node is needed.

        Args:
            xml_root: the root node usable for dynamic query evaluations

        Returns:
            A new evaluation context
        """

    @abstractmethod
    def with_namespaces(self, namespaces: dict[str, str]) -> EvaluationContext:
        """Create a new evaluation context with the namespaces used during evaluation.

        Args:
            namespaces: a dictionary mapping namespace prefixes to URIs.
                This is used when namespace information is not available within document and element nodes.

        Returns:
            A new evaluation context
        """

    @abstractmethod
    def with_variables(self, variables: dict[str, str]) -> EvaluationContext:
        """Create a new evaluation context with the namespaces used during evaluation.

        Args:
            variables: a dictionary mapping variable names (QNames) to variables. This expects the
                variables to be a parsed and evaluated value.

        Returns:
            A new evaluation context
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
