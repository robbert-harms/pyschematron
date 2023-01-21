__author__ = 'Robbert Harms'
__date__ = '2023-01-19'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from abc import ABCMeta, abstractmethod

from elements import SchematronElement


class XMLWriter(metaclass=ABCMeta):

    @abstractmethod
    def to_string(self, element: SchematronElement) -> str:
        """Write a Schematron element to an XML string.

        Args:
            element: the element to write, we will write it recursively.

        Returns:
            A string with the XML content of the Schematron element(s).
        """


class SimpleXMLWriter(XMLWriter):

    def to_string(self, element: SchematronElement) -> str:
        ...
