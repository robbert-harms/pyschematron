from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from dataclasses import dataclass, field

from pyschematron.direct_mode.ast import Schema, Pattern, Variable, ConcreteRule


@dataclass(slots=True, frozen=True)
class BoundSchemaNode:
    """Base class for all Bound Schema nodes.

    Nodes of this type reflect an AST node bound to a specific Query Binding Language (QBL) and phase.
    """


@dataclass(slots=True, frozen=True)
class BoundSchema(BoundSchemaNode):
    """A collection of patterns which must be executed.

    Args:
        schema: the Schema AST node from which we are derived
        patterns: the patterns to execute, this can be all patterns or a subset of them in the case
            of a specific phase.
    """
    schema: Schema
    patterns: list[BoundPattern]


@dataclass(slots=True, frozen=True)
class BoundPattern(BoundSchemaNode):
    """A pattern to apply to an XML.

    Args:
        pattern: the Pattern AST node from which we are derived
        rules: the list of rules to apply
        variables: the list of context variables in this pattern
    """
    pattern: Pattern
    rules: list[BoundRule] = field(default_factory=list)
    variables: list[BoundVariable] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class BoundRule(BoundSchemaNode):
    """Representation of a rule bound to a QBL.

    Args:
        rule: the Rule AST node to which we are bound
        context: the context of this rule
        checks: the list of bound report and assert items in this rule
        variables: the context variables to apply in this rule
        subject: a query referencing the node to which we assign an error message
    """
    rule: ConcreteRule
    context: BoundQuery
    checks: list[Check] = field(default_factory=list)
    variables: list[Variable] = field(default_factory=list)
    subject: BoundQuery | None = None



@dataclass(slots=True, frozen=True)
class BoundVariable(BoundSchemaNode):
    """Representation of a bound context variable.

    Let tags can be defined in two ways, one like `<let name="..." value="..."/>` and another like
    `<let name="..."><some-xml xmlns="...">...</some-xml></let>`. That is, in the second case the value of the
    variable is a separate XML tree.

    Args:
        variable: the Variable AST node from which we are derived
    """
    variable: Variable


@dataclass(slots=True, frozen=True)
class BoundQueryVariable(BoundVariable):
    """Representation of a Variable with a Query attribute.

    Args:
        value: the value attribute
    """
    value: BoundQuery


@dataclass(slots=True, frozen=True)
class BoundXMLVariable(BoundVariable):
    """Representation of a `<let>` tag with the value loaded from the node's content.

    In this case the `<let>` looks like: `<let name="..."><some-xml xmlns="...">...</some-xml></let>` and the
    value would be `<some-xml xmlns="...">...</some-xml>`, i.e. some XML in some namespace not Schematron's.

    Args:
        name: the name attribute
        value: the content of the `<let>` element.
    """
    value: str


# todo how to represent a query
# @dataclass(slots=True, frozen=True)
# class BoundQuery(BoundSchemaNode):
#     """Representation of a Query used in the bound nodes"""
#     query: str
