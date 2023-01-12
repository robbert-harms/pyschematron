from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from dataclasses import dataclass, field
from lxml import etree


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
class Pattern(SchematronElement):
    """Representation of the content of a <pattern> tag."""
    rules: list[Rule]
    variables: list[Variable]
    id: str | None = None


@dataclass(slots=True)
class Rule(SchematronElement):
    """Representation of the content of a <rule> tag."""
    context: str
    tests: list[Test]
    variables: list[Variable] = field(default_factory=list)


@dataclass(slots=True)
class Test(SchematronElement):
    """Base class for assert and report elements."""
    test: str
    message: RuleMessage
    id: str | None = None


@dataclass(slots=True)
class Assert(Test):
    """Representation of an <assert> tag."""


@dataclass(slots=True)
class Report(Test):
    """Representation of a <report> tag."""


@dataclass(slots=True)
class RuleMessage(SchematronElement):
    """Representation of the content of a rule element."""
    message_parts: list[str | etree.Element]


@dataclass(slots=True)
class Namespace(SchematronElement):
    """Representation of the content of an <ns> tag."""
    prefix: str
    uri: str


@dataclass(slots=True)
class Phase(SchematronElement):
    """Representation of the content of a <phase> tag."""
    id: str
    active: list[str]
    variables: list[Variable]


@dataclass(slots=True)
class Variable(SchematronElement):
    """Representation of the content of a <let> tag."""
    name: str
    value: str


@dataclass(slots=True)
class Result(SchematronElement):
    # todo
    ...

