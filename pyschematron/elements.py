from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from dataclasses import dataclass, field


class SchematronElement:
    """Base class for all Schematron elements."""


@dataclass(slots=True)
class Schema(SchematronElement):
    """Representation of a <schema> tag."""
    variables: list[Variable]
    phases: list[Phase]
    patterns: list[Pattern]
    namespaces: list[Namespace]
    title: str | None = None
    default_phase: str | None = None
    query_binding: str | None = None


@dataclass(slots=True)
class Namespace(SchematronElement):
    """Representation of an `<ns>` tag."""
    prefix: str
    uri: str


@dataclass(slots=True)
class Phase(SchematronElement):
    """Representation of a `<phase>` tag."""
    id: str
    active: list[str]
    variables: list[Variable]




@dataclass(slots=True)
class Pattern(SchematronElement):
    """Representation of a <pattern> tag.

    Note that the order of the rules matters. According to the Schematron definition, each node in an XML shall
    never be checked for multiple rules in one pattern. In the case of multiple matching rules, only the first matching
    rule is applied.
    """
    rules: list[Rule] = field(default_factory=list)
    variables: list[Variable] = field(default_factory=list)
    id: str | None = None


@dataclass(slots=True)
class Rule(SchematronElement):
    """Representation of a <rule> tag.

    Args:
        context: the attribute with the rule's context
        tests: the list of report and assert items in this rule
        variables: the list of `<let>` variable declarations in this rule
    """
    context: str | None = None
    tests: list[Test] = field(default_factory=list)
    variables: list[Variable] = field(default_factory=list)


@dataclass(slots=True)
class Test(SchematronElement):
    """Base class for `<assert>` and `<report>` elements.

    Args:
        test: the attribute with the test condition
        content: the mixed text content, can contain `<emph>`, `<span>`, `<dir>`,
            `<value-of>`, and `<name>` as flat text.
        id: the optional id attribute content
    """
    test: str
    content: str
    id: str | None = None


@dataclass(slots=True)
class Assert(Test):
    """Representation of an `<assert>` tag."""


@dataclass(slots=True)
class Report(Test):
    """Representation of a `<report>` tag."""


@dataclass(slots=True)
class Variable(SchematronElement):
    """Representation of a `<let>` tag.

    Args:
        name: the name attribute
        value: the value attribute
    """
    name: str
    value: str

