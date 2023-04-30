__author__ = 'Robbert Harms'
__date__ = '2023-02-18'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal

from elementpath.tree_builders import RootArgType

from pyschematron.direct_mode.ast import Schema
from pyschematron.direct_mode.lib.ast_visitors import QueryBindingVisitor
from pyschematron.direct_mode.utils import reduce_schema_to_phase
from pyschematron.direct_mode.validators.queries.factories import DefaultQueryBindingFactory
from pyschematron.direct_mode.validators.reports import SchematronValidationReport


class SchematronXMLValidator(metaclass=ABCMeta):
    """Base class for all Schematron XML validators.

    Schematron XML validators must be able to validate an XML and return a validation report.
    """

    @abstractmethod
    def validate_xml(self, xml_root: RootArgType) -> SchematronValidationReport:
        """Validate the provided XML using this Schematron XML validator.

        Args:
            xml_root: the root node of an XML to validate

        Returns:
            A Schematron validation report.
        """


class SimpleSchematronXMLValidator(SchematronXMLValidator):

    def __init__(self,
                 schema: Schema,
                 phase: str | Literal['#ALL', '#DEFAULT'] | None = None,
                 schematron_base_path: Path | None = None):
        """XML validation using a Schematron Schema.

        Args:
            schema: the Schema AST node. We will make the AST concrete if not yet done so.
            phase: the phase we want to evaluate. If None, we evaluate the default phase.
            schematron_base_path: the base path from which we loaded the Schematron file, provided for context.
        """
        self._schema = schema
        self._phase = phase
        self._schematron_base_path = schematron_base_path

        query_binding_language = schema.query_binding or 'xslt'
        query_processing_factory = DefaultQueryBindingFactory().get_query_processing_factory(query_binding_language)
        query_parser = query_processing_factory.get_query_parser()
        query_parser = query_parser.with_namespaces({'test': 'http://test.com'})

        self._evaluation_context = query_processing_factory.get_evaluation_context()

        schema = reduce_schema_to_phase(schema, phase)
        self._bound_schema = QueryBindingVisitor(query_parser).apply(schema)


    def validate_xml(self, xml_root: RootArgType) -> SchematronValidationReport:
        ...

