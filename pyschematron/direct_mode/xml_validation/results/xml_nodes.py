"""This module contains class representations for XML nodes.

For the purpose of storing the validation results, we would like to reference the XML node at
which a check was performed. The ISO Schematron applies rules to:

- Elements (*)
- Attributes (@*)
- Root node (/)
- Comments (comment())
- Processing instructions (processing-instruction())

As such, when we list the results, we need a way to represent these different kind of nodes in a uniform manner.
This module aids by having objects to represent each visited XML node.
"""
from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2024-03-25'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta
from dataclasses import dataclass
from lxml.etree import _Element, _ProcessingInstruction, _Comment


@dataclass(frozen=True, slots=True)
class XMLNode(metaclass=ABCMeta):
    """The base class for all XML nodes in this module.

    Args:
        xpath_location: The location of the provided element in XPath 3.1 notation, using the `BracedURILiteral`
            style for the qualified names.
    """
    xpath_location: str


@dataclass(frozen=True, slots=True)
class AttributeNode(XMLNode):
    """Represents attributes of XML elements.

    Args:
        name: the attribute name.
        value: a string value for the attribute
        parent: the parent element node
    """
    name: str
    value: str
    parent: _Element


@dataclass(frozen=True, slots=True)
class CommentNode(XMLNode):
    """Represents XML comments

    Args:
        element: the XML element
    """
    element: _Comment


@dataclass(frozen=True, slots=True)
class ProcessingInstructionNode(XMLNode):
    """Represents XML processing instructions nodes.

    Args:
        element: the wrapped Processing Instruction Element.
    """
    element: _ProcessingInstruction


@dataclass(frozen=True, slots=True)
class ElementNode(XMLNode):
    """Representation of an XML element

    Args:
        element: the wrapper XML element.
    """
    element: _Element
