__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

from pathlib import Path
from typing import Callable, Any

import lxml
from lxml import etree
from lxml.etree import _Element


def node_to_str(node: _Element, remove_namespaces: bool = True) -> str:
    """Convert an lxml node to string.

    This can be used to convert a node to string without namespaces.

    Args:
        node: the node to convert to string
        remove_namespaces: if we want to string the namespaces

    Returns:
        A string representation of the provided node.
    """
    tag_str = lxml.etree.tostring(node, with_tail=False, encoding='unicode')

    if remove_namespaces:
        new_root = etree.fromstring(tag_str)
        for elem in new_root.getiterator():
            elem.tag = etree.QName(elem).localname
        etree.cleanup_namespaces(new_root)

        return lxml.etree.tostring(new_root, encoding='unicode')
    return tag_str


def resolve_href(href: str, base_path: Path) -> Path:
    """Resolve a href attribute to a file on the filesystem.

    This can be used to resolve the `href` attributes of extend or include tags.

    Args:
        href: an absolute or relative path pointing to a file on the filesystem
        base_path: the base path to resolve relative paths.

    Returns:
        An absolute path to a file on the filesystem.
    """
    file_path = Path(href)
    if file_path.is_absolute():
        return file_path
    return (base_path / file_path).resolve()


def parse_attributes(attributes: dict[str, str],
                     allowed_attributes: list[str],
                     attribute_handlers: dict[str: Callable[[str, str], Any]] | None = None) -> dict[str, Any]:
    """Parse the attributes of the given element.

    By default, it returns all attributes as a string value. By using the attribute handlers it is possible
    to specify for each attribute how it is to be treated.

    Args:
        attributes: the attributes we wish to parse
        allowed_attributes: the set of allowed attributes, we will only parse and return the items in this list
        attribute_handlers: for each attribute name, a callback taking in the name and attribute value to return
            a new modified name and attribute value.

    Returns:
        For each allowed attribute the parsed values.
    """
    attribute_handlers = attribute_handlers or {}

    parsed_attributes = {}
    for item in allowed_attributes:
        if item in attributes:
            handler = attribute_handlers.get(item, lambda k, v: {k: v})
            parsed_attributes.update(handler(item, attributes[item]))
    return parsed_attributes
