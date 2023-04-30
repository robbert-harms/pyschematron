__author__ = 'Robbert Harms'
__date__ = '2023-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from typing import Literal

from pyschematron.direct_mode.lib.ast_visitors import ResolveExtendsVisitor, ResolveAbstractPatternsVisitor, \
    PhaseSelectionVisitor
from pyschematron.direct_mode.ast import Schema


def resolve_ast_abstractions(schema: Schema) -> Schema:
    """Resolve all abstractions in a provided AST Schema node and return a Schema node without abstractions.

    This resolves the `extends` in the Rules, and resolves the abstract patterns.

    Args:
         schema: the Schema to resolve all abstractions in

    Returns:
        The Schema with the abstractions resolved.
    """
    schema = ResolveExtendsVisitor(schema).apply(schema)
    schema = ResolveAbstractPatternsVisitor(schema).apply(schema)
    return schema


def reduce_schema_to_phase(schema: Schema, phase: str | Literal['#ALL', '#DEFAULT'] | None = None) -> Schema:
    """Reduce an AST to only those patterns and phases referenced by a specific phase.

    This will first resolve all AST abstractions and afterward reduce the Schema to the phase selected.

    Reducing a Schema means selecting only those patterns and phases which fall within the selected phase.

    Args:
        schema: the Schema to resolve and reduce
        phase: the selected phase

    Returns:
        The resolved and reduced Schema
    """
    schema = resolve_ast_abstractions(schema)
    return PhaseSelectionVisitor(schema, phase=phase).apply(schema)
