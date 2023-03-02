__author__ = 'Robbert Harms'
__date__ = '2023-02-17'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'


from io import BytesIO, IOBase
from pathlib import Path
from typing import BinaryIO, Union

from lxml import etree
from lxml.etree import _Element


def load_xml(xml_data: Union[bytes, str, Path, IOBase, BinaryIO, _Element]) -> _Element:
    """Load an XML from a variety of sources.

    Args:
        xml_data: the XML data to load. Can be loaded from a string, file, or byte-like object.

    Returns:
        The root node of the loaded XML as an lxml element.
    """
    match xml_data:
        case _Element():
            return xml_data
        case IOBase():
            parser = etree.XMLParser(ns_clean=True)
            return etree.parse(xml_data, parser).getroot()
        case bytes():
            return load_xml(BytesIO(xml_data))
        case str():
            return load_xml(BytesIO(xml_data.encode('utf-8')))
        case Path():
            with open(xml_data, 'rb') as f:
                return load_xml(f)
