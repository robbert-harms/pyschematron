__author__ = 'Robbert Harms'
__date__ = '2023-05-20'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from typing import Any

from pyschematron.direct_mode.ast import Variable, QueryVariable, XMLVariable
from pyschematron.direct_mode.validators.queries.base import EvaluationContext, QueryParser


def evaluate_variables(variables: list[Variable],
                       parser: QueryParser,
                       context: EvaluationContext) -> dict[str, Any]:
    """Parse and evaluate a list of Schematron variables.

    This is a convenience method for use in the validators. It parses any query variable and evaluates it using the
    context provided. The end result is a set of objects which function as variable values in Schematron queries.

    Args:
        variables: the AST variables we would like to parse.
        parser: the parser to use for parsing the queries.
        context: the context we need to evaluate the query variables.

    Returns:
        The parsed and evaluated variables.
    """
    results = {}
    for variable in variables:
        if isinstance(variable, QueryVariable):
            results[variable.name] = parser.parse(variable.value.query).evaluate(context)
        elif isinstance(variable, XMLVariable):
            results[variable.name] = variable.value
    return results
