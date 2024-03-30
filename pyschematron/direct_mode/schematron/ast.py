"""The abstract syntax tree for representing a Schematron XML file.

Step one of loading a Schematron file is parsing it into the various `SchematronASTNode` instances.
At this step, `<include>` and `<extend href="">` tags are expanded and the referenced XML files are loaded and included.
Other referencing, like ID matching is done in a later stage.
"""
from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Self

from pyschematron.direct_mode.lib.ast import GenericASTNode


@dataclass(slots=True, frozen=True)
class SchematronASTNode(GenericASTNode):
    """Base class for all Schematron AST nodes.

    Since we aim for immutable objects, we do not allow the use of mutable objects in the nodes. Use either
    tuples (instead of lists) or frozendict instead of dict.
    """

    def __post_init__(self):
        for field_name, value in self.get_init_values().items():
            if isinstance(value, list):
                raise ValueError(f'No lists allowed for field "{field_name}", use a tuple instead.')

    def with_updated(self, **updated_items) -> Self:
        """Get a copy of this AST node with updated init values.

        This gets the current set of init values and updates those with the provided items.

        Args:
            updated_items: the keyword elements we wish to update

        Returns:
            A new copy of this node with the relevant items updated.
        """
        return type(self)(**(self.get_init_values() | updated_items))


@dataclass(slots=True, frozen=True)
class Schema(SchematronASTNode):
    """Representation of a `<schema>` tag.

    Although the standard only supports one `<diagnostics>` and `<properties>` element, we support multiple.

    Args:
        patterns: the listing of patterns
        namespaces: the listing of namespaces
        phases: the listing of phases
        diagnostics: the listing of diagnostics
        properties: the listing of properties
        paragraphs: the listing of paragraphs
        variables: the listing of variables
        title: the title of this scheme.
        default_phase: reference to the default phase of this Schema
        fpi: formal public identifier, a system-independent ID of this test
        icon: reference to a graphic file to be used in the error message
        id: the identifier of this element
        query_binding: the query binding for this scheme
        schema_version: an implementation defined version of the user's schema
        see: a URI or URL referencing background information
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.
    """
    patterns: tuple[Pattern, ...] = tuple()
    namespaces: tuple[Namespace, ...] = tuple()
    phases: tuple[Phase, ...] = tuple()
    diagnostics: tuple[Diagnostics, ...] = tuple()
    properties: tuple[Properties, ...] = tuple()
    paragraphs: tuple[Paragraph, ...] = tuple()
    variables: tuple[Variable, ...] = tuple()
    title: Title | None = None

    default_phase: str | None = None
    fpi: str | None = None
    icon: str | None = None
    id: str | None = None
    query_binding: str | None = None
    schema_version: str | None = None
    see: str | None = None
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None


@dataclass(slots=True, frozen=True)
class Namespace(SchematronASTNode):
    """Representation of an `<ns>` tag.

    Args:
        prefix: the prefix for use in the Schematron and the Queries
        uri: the namespace's URI
    """
    prefix: str
    uri: str


@dataclass(slots=True, frozen=True)
class Phase(SchematronASTNode):
    """Representation of a `<phase>` tag.

    Phases define sets of patterns. When a phase is marked as active, only patterns within that phase definition are
    fired.

    Args:
        id: the identifier of this element
        active: listing of identifiers of active patterns
        variables: listing of variables scoped within this execution
        paragraphs: documentation paragraphs
        fpi: formal public identifier, a system-independent ID of this test
        icon: reference to a graphic file to be used in the error message
        see: a URI or URL referencing background information
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.
    """
    id: str
    active: tuple[ActivePhase, ...] = tuple()
    variables: tuple[Variable, ...] = tuple()
    paragraphs: tuple[Paragraph, ...] = tuple()
    fpi: str | None = None
    icon: str | None = None
    see: str | None = None
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None


@dataclass(slots=True, frozen=True)
class ActivePhase(SchematronASTNode):
    """Representation of a `<active>` tag.

    Args:
        pattern_id: the ID of the pattern we should fire if this phase is active
        content: the text content, only used for documentation purposes.
    """
    pattern_id: str
    content: str | None = None


@dataclass(slots=True, frozen=True)
class Diagnostics(SchematronASTNode):
    """Representation of a `<diagnostics>` tag.

    Args:
        diagnostics: the listing of Diagnostic classes
    """
    diagnostics: tuple[Diagnostic, ...]


@dataclass(slots=True, frozen=True)
class Diagnostic(SchematronASTNode):
    """Representation of a `<diagnostic>` tag.

    Officially the `<name>` element is not allowed within a diagnostic. We allow it nonetheless.

    Args:
        content: the rich text content of this diagnostic.
        id: the identifier of this element
        fpi: formal public identifier, a system-independent ID of this test
        icon: reference to a graphic file to be used in the error message
        role: a description of the error message or the rule
        see: a URI or URL referencing background information
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.
    """
    content: tuple[str | ValueOf | Name, ...]
    id: str
    fpi: str | None = None
    icon: str | None = None
    role: str | None = None
    see: str | None = None
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None


@dataclass(slots=True, frozen=True)
class Properties(SchematronASTNode):
    """Representation of a `<properties>` tag.

    Args:
        properties: the listing of Property classes
    """
    properties: tuple[Property, ...]


@dataclass(slots=True, frozen=True)
class Property(SchematronASTNode):
    """Representation of a `<property>` tag.

    Args:
        content: the rich text content of this property.
        id: the identifier of this element
        role: a description of the error message or the rule
        scheme: An IRI or public identifier specifying the notation used for the node's value.
    """
    content: tuple[str | ValueOf | Name, ...]
    id: str
    role: str | None = None
    scheme: str | None = None


@dataclass(slots=True, kw_only=True, frozen=True)
class Pattern(SchematronASTNode):
    """Abstract representation of a <pattern> tag.

    This can not be instantiated as is, one needs to load one of the subclasses for concrete or abstract patterns.

    Be reminded that the order of the rules matters. According to the Schematron definition, each node in an XML shall
    never be checked for multiple rules in one pattern. In the case of multiple matching rules, only the first matching
    rule is applied.

    Args:
        documents: xpath expression evaluating into one or more documents which must be checked instead of the
            current document.
        id: the identifier of this test
        fpi: formal public identifier, a system-independent ID of this test
        icon: reference to a graphic file to be used in the error message
        see: a URI or URL referencing background information
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.
    """
    documents: XPathExpression | None = None
    id: str | None = None
    fpi: str | None = None
    icon: str | None = None
    see: str | None = None
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None


@dataclass(slots=True, frozen=True)
class ConcretePattern(Pattern):
    """A concrete pattern, this neither inherits another pattern, nor is an abstract pattern.

    Args:
        rules: the listing of rules
        variables: the listing of variables
        title: the title of this pattern
        paragraphs: the listing of paragraphs
    """
    rules: tuple[Rule, ...] = tuple()
    variables: tuple[Variable, ...] = tuple()
    paragraphs: tuple[Paragraph, ...] = tuple()
    title: Title | None = None


@dataclass(slots=True, frozen=True)
class AbstractPattern(Pattern):
    """An abstract pattern, coming from a pattern with the attribute `@abstract` set to True.

    Args:
        rules: the listing of rules
        variables: the listing of variables
        title: the title of this pattern
        paragraphs: the listing of paragraphs
    """
    rules: tuple[Rule, ...] = tuple()
    variables: tuple[Variable, ...] = tuple()
    paragraphs: tuple[Paragraph, ...] = tuple()
    title: Title | None = None


@dataclass(slots=True, frozen=True)
class InstancePattern(Pattern):
    """A pattern inheriting another pattern, i.e. patterns with the `is-a` attribute set.

    Args:
        params: the listing of pattern parameters
    """
    abstract_id_ref: str
    params: tuple[PatternParameter, ...] = tuple()


@dataclass(slots=True, frozen=True)
class PatternParameter(SchematronASTNode):
    """A parameter inside a pattern with the `is-a` attribute set.

    Args:
        name: the name of this parameter
        value: the value of this parameter
    """
    name: str
    value: str


@dataclass(slots=True, kw_only=True, frozen=True)
class Rule(SchematronASTNode):
    """Abstract representation of a <rule> tag.

    This can not be instantiated as is, rather instantiate one of the subclasses for concrete, abstract,
    or external rules.

    Args:
        checks: the listing of report and assert items in this rule
        variables: the listing of `<let>` variable declarations in this rule
        paragraphs: listing of paragraphs
        flag: name of the flag to which this test belongs, is set to True when this test is fired
        fpi: formal public identifier, a system-independent ID of this test
        icon: reference to a graphic file to be used in the error message
        role: a description of the error message or the rule
        see: a URI or URL referencing background information
        subject: a query referencing the node to which we assign an error message
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.
    """
    checks: tuple[Check, ...] = tuple()
    variables: tuple[Variable, ...] = tuple()
    paragraphs: tuple[Paragraph, ...] = tuple()
    extends: tuple[Extends, ...] = tuple()
    flag: str | None = None
    fpi: str | None = None
    icon: str | None = None
    role: str | None = None
    see: str | None = None
    subject: XPathExpression | None = None
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None


@dataclass(slots=True, frozen=True)
class ConcreteRule(Rule):
    """Representation of a concrete <rule> tag (e.g. not abstract).

    Args:
        context: the attribute with the rule's context
        id: the identifier of this test (optional)
    """
    context: Query
    id: str | None = None


@dataclass(slots=True, frozen=True)
class AbstractRule(Rule):
    """Representation of an abstract <rule> tag.

    Args:
        id: the identifier of this test (required)
    """
    id: str


@dataclass(slots=True, frozen=True)
class ExternalRule(Rule):
    """Representation of an <rule> loaded from an external file using extends."""
    id: str | None = None


@dataclass(slots=True, frozen=True)
class Extends(SchematronASTNode):
    """Base class for <extends> tag representations used to extend a Rule with another rule."""


@dataclass(slots=True, frozen=True)
class ExtendsById(Extends):
    """Represents an <extends> tag which points to an abstract rule in this Schema.

    Args:
        id_ref: the identifier of a Rule inside the Schematron to which we refer
    """
    id_ref: str


@dataclass(slots=True, frozen=True)
class ExtendsExternal(Extends):
    """Represents an <extends> tag which has an AbstractRule loaded from another file.

    Args:
        rule: an ExternalRule loaded from another file.
        file_path: the path from which the rule was loaded
    """
    rule: ExternalRule
    file_path: Path


@dataclass(slots=True, frozen=True)
class Check(SchematronASTNode):
    """Base class for `<assert>` and `<report>` elements.

    Args:
        test: the attribute with the test condition
        content: the mixed text content, can contain `<emph>`, `<span>`, `<dir>`,
            `<value-of>`, and `<name>` as flat text.
        diagnostics: listing of IDs referencing a diagnostic elements
        flag: name of the flag to which this test belongs, is set to True when this test is fired
        fpi: formal public identifier, a system-independent ID of this test
        icon: reference to a graphic file to be used in the error message
        id: the identifier of this test
        properties: listing of identifiers of property items
        role: a description of the error message or the rule
        see: a URI or URL referencing background information
        subject: an XPath expression referencing the node to which we assign an error message
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.
    """
    test: Query
    content: tuple[str | ValueOf | Name, ...]
    diagnostics: tuple[str, ...] | None = None
    flag: str | None = None
    fpi: str | None = None
    icon: str | None = None
    id: str | None = None
    properties: tuple[str, ...] | None = None
    role: str | None = None
    see: str | None = None
    subject: XPathExpression | None = None
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None


@dataclass(slots=True, frozen=True)
class Assert(Check):
    """Representation of an `<assert>` tag."""


@dataclass(slots=True, frozen=True)
class Report(Check):
    """Representation of a `<report>` tag."""


@dataclass(slots=True, frozen=True)
class Variable(SchematronASTNode):
    """Abstract representation of a `<let>` tag.

    Let tags can be defined in two ways, one like `<let name="..." value="..."/>` and another like
    `<let name="..."><some-xml xmlns="...">...</some-xml></let>`. That is, in the second case the value of the
    variable is a separate XML tree.

    Args:
        name: the name attribute
    """
    name: str


@dataclass(slots=True, frozen=True)
class QueryVariable(Variable):
    """Representation of a `<let>` tag with a Query attribute.

    Args:
        value: the value attribute
    """
    value: Query


@dataclass(slots=True, frozen=True)
class XMLVariable(Variable):
    """Representation of a `<let>` tag with the value loaded from the node's content.

    In this case the `<let>` looks like: `<let name="..."><some-xml xmlns="...">...</some-xml></let>` and the
    value would be `<some-xml xmlns="...">...</some-xml>`, i.e. some XML in some namespace not Schematron's.

    Args:
        value: the content of the `<let>` element.
    """
    value: str


@dataclass(slots=True, frozen=True)
class Paragraph(SchematronASTNode):
    """Representation of a `<p>` tag.

    Although the Schematron ISO standard does not prescribe the `xml:lang` and `xml:space` attribute for paragraphs, we
    add them nonetheless.

    Args:
        content: the text content of this paragraph
        class_: the class attribute
        icon: the icon attribute
        id: the identifier
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.
    """
    content: str
    class_: str | None = None
    icon: str | None = None
    id: str | None = None
    xml_lang: str | None = None
    xml_space: Literal['default', 'preserve'] | None = None


@dataclass(slots=True, frozen=True)
class Title(SchematronASTNode):
    """Representation of a `<title>` tag.

    Args:
        content: the text content of this title
    """
    content: str


@dataclass(slots=True, frozen=True)
class Query(SchematronASTNode):
    """Representation of a Query used in the Schematron AST nodes."""
    query: str


@dataclass(slots=True, frozen=True)
class XPathExpression(SchematronASTNode):
    """Representation of an XPath expression.

    Since Schematron queries are abstract entities defined by the query binding in the Schematron root, we also need
    an XPath expression object for elements which may only be XPath expressions.
    """
    expression: str


@dataclass(slots=True, frozen=True)
class RichTextContent(SchematronASTNode):
    """Specific subclass for rich text content.

    Rich text in Schematron allows for `<dir>`, `<emph>`, `<span>`, `<value-of>` and sometimes `<name>` elements.
    In this package we allow `<name>` in all rich text content.

    The non-Schematron specific elements dir, emph and span are handled as text content by the parser. The name and
    value-of are specified by the AST nodes.

    By subclassing these nodes we allow to group them.
    """


@dataclass(slots=True, frozen=True)
class ValueOf(RichTextContent):
    """Representation of a `<value-of>` node."""
    select: Query


@dataclass(slots=True, frozen=True)
class Name(RichTextContent):
    """Representation of a `<name>` node."""
    path: Query | None = None
