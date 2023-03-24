from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-03-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from typing import Any


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


class EvaluationContext(metaclass=ABCMeta):
    """Representation of the context required when evaluating a Query."""


class Query(metaclass=ABCMeta):
    """Representation of an executable Schematron query.

    To specialize for a new language, one must implement a specialized Context, Parser and Query.
    """

    @abstractmethod
    def evaluate(self, context: EvaluationContext | None) -> Any:
        """Evaluate this query.

        Args:
            context: optional context to be used during evaluation.
                The exact context and its usage is implementation defined.

        Returns:
            The results of running this query.
        """
