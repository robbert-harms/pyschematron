from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from dataclasses import dataclass
from lxml import etree


class SchematronElement:
    """Base class for all Schematron elements"""


@dataclass(slots=True)
class Schema(SchematronElement):
    variables: list[Variable]
    phases: list[Phase]
    patterns: list[Pattern]
    namespaces: list[Namespace]
    title: str | None = None
    default_phase: str | None = None


@dataclass(slots=True)
class Assert(SchematronElement):
    test: str
    message: AssertMessage
    is_report: bool
    id: str | None = None


@dataclass(slots=True)
class AssertMessage(SchematronElement):
    message_parts: list[str | etree.Element]


@dataclass(slots=True)
class Namespace(SchematronElement):
    prefix: str
    uri: str


@dataclass(slots=True)
class Pattern(SchematronElement):
    rules: list[Rule]
    variables: list[Variable]
    id: str | None = None


@dataclass(slots=True)
class Phase(SchematronElement):
    id: str
    active: list[str]
    variables: list[Variable]


@dataclass(slots=True)
class Rule(SchematronElement):
    context: str
    asserts: list[Assert]
    variables: list[Variable]


@dataclass(slots=True)
class Variable(SchematronElement):
    """Stores a variable.

    Variables are defined using the element `<let />`.
    """
    name: str
    value: str


@dataclass(slots=True)
class Result(SchematronElement):
    ...

