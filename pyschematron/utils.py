__author__ = 'Robbert Harms'
__date__ = '2023-02-17'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'


from io import BytesIO, IOBase
from pathlib import Path
from typing import BinaryIO, Union

from lxml import etree
from lxml.etree import _ElementTree


def load_xml_document(xml_data: Union[bytes, str, Path, IOBase, BinaryIO]) -> _ElementTree:
    """Load an XML document from a polymorphic source.

    Args:
        xml_data: the XML data to load. Can be loaded from a string, file, or byte-like object.

    Returns:
        The document node of the loaded XML.
    """
    match xml_data:
        case IOBase():
            parser = etree.XMLParser(ns_clean=True)
            return etree.parse(xml_data, parser)
        case bytes():
            return load_xml_document(BytesIO(xml_data))
        case str():
            return load_xml_document(BytesIO(xml_data.encode('utf-8')))
        case Path():
            with open(xml_data, 'rb') as f:
                return load_xml_document(f)
