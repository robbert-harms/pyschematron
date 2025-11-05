__author__ = 'Robbert Harms'
__date__ = '2023-02-17'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'


from io import BytesIO, IOBase
from pathlib import Path
from typing import BinaryIO, Union

from lxml import etree
from lxml.etree import _ElementTree


def load_xml_document(xml_data: Union[bytes, str, Path, IOBase, BinaryIO],
                      parser: etree.XMLParser | None = None) -> _ElementTree:
    """Load an XML document from a polymorphic source.

    Args:
        xml_data: the XML data to load. Can be loaded from a string, file, or byte-like object.
        parser: the XMLParser to use. Can be specialized for your use-case.

    Returns:
        The document node of the loaded XML.
    """
    parser = parser or etree.XMLParser(ns_clean=True)

    match xml_data:
        case IOBase():
            return etree.parse(xml_data, parser)
        case bytes():
            return load_xml_document(BytesIO(xml_data), parser=parser)
        case str():
            return load_xml_document(BytesIO(xml_data.encode('utf-8')), parser=parser)
        case Path():
            with open(xml_data, 'rb') as f:
                return load_xml_document(f, parser=parser)
