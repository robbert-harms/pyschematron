__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from pathlib import Path

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
