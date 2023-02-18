from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

import warnings
from dataclasses import dataclass, field
from typing import ClassVar


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
        id: the identifier of this test
        diagnostics: whitespace-separated list of IDs referencing a diagnostic elements
        subject: an xpath string referencing the node to which we assign an error message
        role: a description of the error message or the rule
        flag: name of the flag to which this test belongs, is set to True when this test is fired
        see: a URI or URL referencing background information
        fpi: formal public identifier, a system-independent ID of this test
        icon: reference to a graphic file to be used in the error message
        properties: whitespace-separated list of identifiers of property items
        xml_lang: the default natural language for this node
        xml_space: defines how whitespace must be handled for this element.

    Attributes:
        attributes_to_args: a class variable with a mapping of the XML attributes to the names of the keyword
            variables in the initialization function.
    """
    test: str
    content: str
    id: str | None = None
    diagnostics: str | None = None
    subject: str | None = None
    role: str | None = None
    flag: str | None = None
    see: str | None = None
    fpi: str | None = None
    icon: str | None = None
    properties: str | None = None
    xml_lang: str | None = None
    xml_space: str | None = None

    attributes_to_args: ClassVar[dict[str, str]] = {
        'id': 'id',
        'diagnostics': 'diagnostics',
        'subject': 'subject',
        'role': 'role',
        'flag': 'flag',
        'see': 'see',
        'fpi': 'fpi',
        'icon': 'icon',
        'properties': 'properties',
        'xml:lang': 'xml_lang',
        'xml:space': 'xml_space'
    }

    def __post_init__(self):
        unsupported = ['diagnostics', 'subject', 'role', 'flag', 'see', 'fpi', 'icon']
        active = [el for el in unsupported if getattr(self, el) is not None]
        if len(active) > 0:
            # todo move warnings to processor class
            warnings.warn(f'The attributes {active} are currently unsupported in processing.')


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

