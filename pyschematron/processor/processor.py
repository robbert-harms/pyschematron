__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from pyschematron.parsers.ast import Schema


class SchematronProcessor:

    ...


class SimpleSchematronProcessor(SchematronProcessor):

    def process_schema(self, ast: Schema):
        ...
