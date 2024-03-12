from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2024-03-11'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta
from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class SVRLNode:
    """Base class for the SVRL nodes."""


@dataclass(slots=True, frozen=True)
class SchematronOutput(SVRLNode):
    # texts: list[Text] = field(default_factory=list)
    ns_prefix_in_attribute_values: list[NSPrefixInAttributeValues] = field(default_factory=list)
    validation_events: tuple[ValidationEvent] = tuple()
    # active_patterns: list[ActivePattern] = field(default_factory=list)
    # fired_rules: list[FiredRules] = field(default_factory=list)
    # failed_asserts: list[FailedAsserts] = field(default_factory=list)
    # successful_reports: list[SuccessfulReports] = field(default_factory=list)

    phase: str | None = None
    schemaVersion: str | None = None
    title: str | None = None


@dataclass(slots=True, frozen=True)
class NSPrefixInAttributeValues(SVRLNode):
    """Namespace declaration, representation of the SVRL `<ns-prefix-in-attribute-values>` node.

    Args:
        prefix: the prefix to use for this namespace
        uri: the namespace's URI
    """
    prefix: str
    uri: str


@dataclass(slots=True, frozen=True)
class ValidationEvent(SVRLNode):
    """Base class for the validation events.

    An SVRL is a flat representation of the patterns, rules and assertions / reports visited during validation.
    To represent these in a class hierarchy we group these as validation events.
    """


@dataclass(slots=True, frozen=True)
class ActivePattern(ValidationEvent):
    """Representation of the `<active-pattern>` SVRL node.

    Args:
        documents: list of URIs of datatype `xs:anyURI`, pointing to the documents processed.
        id: the identifier of this pattern, typically a copy of the Schematron pattern id.
        name: some name for this pattern, up to the implementation.
        role: some role indicator for this pattern, up to the implementation.
    """
    documents: tuple[str] = tuple()
    id: str | None = None
    name: str | None = None
    role: str | None = None


@dataclass(slots=True, frozen=True)
class FiredRule(ValidationEvent):
    """Representation of the `<fired-rule>` SVRL node.

    Args:
        context: a copy of the context of the Schematron rule element
        document: Reference of the document to which this rule was defined.
        flag: a flag that was set to true when this rule fired, typically a copy of the flag of the Schematron rule.
        id: the identifier of this rule, typically a copy of the Schematron rule id.
        name: some name for this rule, up to the implementation.
        role: the role for this rule, typically a copy of the role of the rule element.
    """
    context: str
    document: str | None = None
    flag: str | None = None
    id: str | None = None
    name: str | None = None
    role: str | None = None
