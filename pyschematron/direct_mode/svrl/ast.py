"""The abstract syntax tree for representing an SVRL report.

This is primarily used to write out an SVRL report after Schematron validation of an XML.
"""
from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2024-03-11'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from dataclasses import dataclass
from typing import Literal

from lxml.etree import _Element

from pyschematron.direct_mode.lib.ast import GenericASTNode


@dataclass(slots=True, frozen=True)
class SVRLNode(GenericASTNode):
    """Base class for the Schematron Validation Report Language (SVRL) nodes."""


@dataclass(slots=True, frozen=True)
class SchematronOutput(SVRLNode):
    """Representation of the `<schematron-output>` SVRL node.

    Args:
        texts: zero or more text nodes containing some text about the schema and/or validation.
        ns_prefix_in_attribute_values: namespace and prefix declarations.
        validation_events: schematron validation events, in order of proceeding
        phase: the Schematron phase this SVRL is a result of
        schema_version: copy of the Schematron's schemaVersion attribute
        title: some title for this validation report.
    """
    texts: tuple[Text, ...] = tuple()
    ns_prefix_in_attribute_values: tuple[NSPrefixInAttributeValues, ...] = tuple()
    validation_events: tuple[ValidationEvent, ...] = tuple()
    metadata: MetaData | None = None
    phase: str | None = None
    schema_version: str | None = None
    title: str | None = None


@dataclass(slots=True, frozen=True)
class MetaData(SVRLNode):
    """Metadata for this SVRL report.

    A non-standard defined node containing metadata. We use it to add metadata about PySchematron.

    Args:
        xml_elements: listing of the XML elements contained in this metadata
        namespaces: the namespaces to be used in the attributes of this metadata node.
    """
    xml_elements: tuple[_Element, ...] = tuple()
    namespaces: tuple[Namespace, ...] = tuple()

    @dataclass(slots=True, frozen=True)
    class MetaDataNode:
        """Base class for metadata nodes."""

    @dataclass(slots=True, frozen=True)
    class Namespace(MetaDataNode):
        """Representation of a namespace attribute in the metadata node.

        Args:
            prefix: the prefix
            uri: the namespace's URI
        """
        prefix: str
        uri: str


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
    documents: tuple[str, ...] | None = None
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
    context: SchematronQuery
    document: str | None = None
    flag: str | None = None
    id: str | None = None
    name: str | None = None
    role: str | None = None


@dataclass(slots=True, frozen=True)
class SuppressedRule(ValidationEvent):
    """Representation of the `<suppressed-rule>` SVRL node.

    This node type is officially not in the standard, but it is added by some packages, and so do we.

    Args:
        context: a copy of the context of the Schematron rule element
        id: the identifier of this rule, typically a copy of the Schematron rule id.
    """
    context: SchematronQuery
    id: str | None = None


@dataclass(slots=True, frozen=True)
class CheckResult(ValidationEvent):
    """Base class for the `<failed-assert>` and `<successful-report>` SVRL nodes.

    Args:
        text: result description of this check.
        location: the location of this failed assert as an XPath expression
        test: the test expression for this assert, copied from the Schematron assert node.
        diagnostic_references: listing of the diagnostic references by this check
        property_references: properties referenced by this check
        subject_location: the location referenced by the subject of either the check or the parent rule.
        flag: a flag that was set to true when this assertion fired, typically a copy of the Schematron's flag rule.
        id: the identifier of this rule, typically a copy of the Schematron assert id.
        role: the role for this assert, typically a copy of the role of the assert element.
    """
    text: Text
    location: XPathExpression
    test: SchematronQuery
    diagnostic_references: tuple[DiagnosticReference, ...] = tuple()
    property_references: tuple[PropertyReference, ...] = tuple()
    subject_location: XPathExpression | None = None
    flag: str | None = None
    id: str | None = None
    role: str | None = None


@dataclass(slots=True, frozen=True)
class FailedAssert(CheckResult):
    """Representation of the `<failed-assert>` SVRL node."""


@dataclass(slots=True, frozen=True)
class SuccessfulReport(CheckResult):
    """Representation of the `<successful-report>` SVRL node."""


@dataclass(slots=True, frozen=True)
class DiagnosticReference(SVRLNode):
    """Representation of the `<diagnostic-reference>` node.

    These nodes reference a diagnostic connected to an assert/report node.

    Args:
        text: resulting text
        diagnostic: identifier of this diagnostic, copied from the diagnostic element's id attribute
    """
    text: Text
    diagnostic: str


@dataclass(slots=True, frozen=True)
class PropertyReference(SVRLNode):
    """Representation of the `<property-reference>` node.

    These nodes reference a property connected to an assert/report node.

    Args:
        text: resulting text
        property: identifier of this property
        role: the role attribute for this property, copied from the properties' role attribute
        scheme: the scheme attribute for this property, copied from the properties' scheme attribute
    """
    text: Text
    property: str
    role: str | None = None
    scheme: str | None = None


@dataclass(slots=True, frozen=True)
class XPathExpression(SVRLNode):
    """Representation of an XPath expression  used in the SVRL nodes."""
    expression: str


@dataclass(slots=True, frozen=True)
class SchematronQuery(SVRLNode):
    """Representation of a Schematron Query, as used in the SVRL nodes."""
    query: str


@dataclass(slots=True, frozen=True)
class Text(SVRLNode):
    """Representation of a `<text>` tag.

    Although the attributes `class` and `id` are not specified in the SVRL specification, we add them nonetheless since
    they can be forwarded from Schematron nodes.

    Args:
        content: the text content of this text element, all loaded as one string
        fpi: formal public identifier, may be copied from the relevant Schematron FPI attribute.
        icon: the icon attribute
        see: A URI pointing to some external information of this element.
        class_: some class attribute
        id: unique identifier
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.
    """
    content: str
    fpi: str | None = None
    icon: str | None = None
    see: str | None = None
    class_: str | None = None
    id: str | None = None
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None
