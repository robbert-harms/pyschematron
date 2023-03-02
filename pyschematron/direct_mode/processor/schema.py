__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from dataclasses import dataclass


class SchematronElement:
    """Base class for all Schematron AST nodes."""


@dataclass(slots=True)
class Schema(SchematronElement):
    ...
