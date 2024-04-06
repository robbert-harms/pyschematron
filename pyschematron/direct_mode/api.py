"""Implementation of the common API defined in the pyschematron package."""

__author__ = 'Robbert Harms'
__date__ = '2024-04-01'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pathlib import Path

from lxml.etree import _ElementTree

from pyschematron.api import SchematronValidatorFactory, SchematronValidator, ValidationResult
from pyschematron.direct_mode.schematron.ast import Schema
from pyschematron.direct_mode.schematron.ast_visitors import ResolveExtendsVisitor, ResolveAbstractPatternsVisitor, \
    PhaseSelectionVisitor
from pyschematron.direct_mode.schematron.parsers.xml.parser import SchemaParser, ParsingContext
from pyschematron.direct_mode.xml_validation.queries.base import CustomQueryFunction
from pyschematron.direct_mode.xml_validation.queries.factories import ExtendableQueryProcessorFactory, \
    QueryProcessorFactory
from pyschematron.direct_mode.xml_validation.results.svrl_builder import DefaultSVRLReportBuilder
from pyschematron.direct_mode.xml_validation.results.validation_results import XMLDocumentValidationResult
from pyschematron.direct_mode.xml_validation.validators import SimpleSchematronXMLValidator
from pyschematron.utils import load_xml_document


class DirectModeSchematronValidatorFactory(SchematronValidatorFactory):

    def __init__(self,
                 schematron_xml: Path | _ElementTree | None = None,
                 phase: str | None = None,
                 schematron_base_path: Path | None = None):
        """Validator factory for direct mode Schematron validation.

        Args:
            schematron_xml: the Schematron Schema we want to evaluate. Can also be set using the class methods.
            phase: the phase we would like to evaluate. Can also be set using the class methods. If set to None
                we use the Schema's default phase.
            schematron_base_path: explicitly set the Schematron base path.
        """
        self._schematron_xml = schematron_xml
        self._phase = phase
        self._schematron_base_path = schematron_base_path
        self._custom_query_functions: dict[str, list[CustomQueryFunction]] = {}
        self._custom_query_bases: dict[str, str] = {}

    def set_schema(self, schematron_xml: Path | _ElementTree):
        self._schematron_xml = schematron_xml

    def set_phase(self, phase: str | None):
        self._phase = phase

    def set_base_path(self, schematron_base_path: Path):
        self._schematron_base_path = schematron_base_path

    def add_custom_functions(self,
                             query_binding: str,
                             custom_query_functions: list[CustomQueryFunction],
                             base_query_binding: str | None = None):
        if query_binding in self._custom_query_functions:
            self._custom_query_functions[query_binding] += custom_query_functions
        else:
            self._custom_query_functions[query_binding] = custom_query_functions

        if base_query_binding:
            self._custom_query_bases[query_binding] = base_query_binding

    def build(self) -> SchematronValidator:
        if isinstance(self._schematron_xml, Path):
            schematron = load_xml_document(self._schematron_xml)
        else:
            schematron = self._schematron_xml

        schematron_base_path = self._get_schematron_base_path()

        schematron_parser = SchemaParser()
        parsing_context = ParsingContext(base_path=schematron_base_path)
        schema = schematron_parser.parse(schematron.getroot(), parsing_context)

        query_processor_factory = self._get_query_processor_factory()

        return DirectModeSchematronValidator(schema, self._phase, schematron_base_path, query_processor_factory)

    def _get_query_processor_factory(self) -> QueryProcessorFactory | None:
        """Get the query processor factory we would like to use for the validation.

        Returns:
            The query processor to use, or None if defaults can be used.
        """
        if not len(self._custom_query_functions):
            return None

        custom_processor_factory = ExtendableQueryProcessorFactory()

        for query_binding, custom_functions in self._custom_query_functions.items():
            if query_binding in self._custom_query_bases:
                processor = custom_processor_factory.get_query_processor(self._custom_query_bases[query_binding])
            else:
                if custom_processor_factory.has_query_processor(query_binding):
                    processor = custom_processor_factory.get_query_processor(query_binding)
                else:
                    raise ValueError(f'No query binding base provided for adding '
                                     f'custom functions to query binding "{query_binding}"')

            for custom_function in custom_functions:
                processor = processor.with_custom_function(custom_function)

            custom_processor_factory.set_query_processor(query_binding, processor)
        return custom_processor_factory

    def _get_schematron_base_path(self) -> Path | None:
        """Get the base path we use for the Schematron parsing.

        If set explicitly, we return that. Else we try to infer it from the provided Schematron schema.

        Returns:
            The path we would like to use in the Schematron parsing.
        """
        if self._schematron_base_path is not None:
            return self._schematron_base_path

        if isinstance(self._schematron_xml, Path):
            return self._schematron_xml.parent

        if hasattr(self._schematron_xml, 'docinfo'):
            docinfo = self._schematron_xml.docinfo
            if hasattr(docinfo, 'URL') and docinfo.URL:
                return Path(docinfo.URL).parent

        return None


class DirectModeSchematronValidator(SchematronValidator):

    def __init__(self, schema: Schema,
                 phase: str | None,
                 base_path: Path | None,
                 query_processor_factory: QueryProcessorFactory | None = None):
        """Validator API implementation for the direct mode evaluation.

        Args:
            schema: the Schema we would like to use in the validation
            phase: the phase we would like to use
            base_path: the base path of the Schema, used for loading external Schema parts.
            query_processor_factory: optionally, specify the query processor factory to use.
        """
        self._schema = schema
        self._phase = phase
        self._base_path = base_path

        schema = ResolveExtendsVisitor(schema).apply(schema)
        schema = ResolveAbstractPatternsVisitor(schema).apply(schema)
        schema = PhaseSelectionVisitor(schema, phase).apply(schema)

        self._validator = SimpleSchematronXMLValidator(schema, phase, base_path,
                                                       query_processor_factory=query_processor_factory)

    def validate(self, xml_data: Path | _ElementTree) -> ValidationResult:
        if isinstance(xml_data, Path):
            xml_document = load_xml_document(xml_data)
        else:
            xml_document = xml_data

        validation_results = self._validator.validate_xml(xml_document)
        return DirectModeValidationResult(validation_results)


class DirectModeValidationResult(ValidationResult):

    def __init__(self, validation_results: XMLDocumentValidationResult):
        """Validation results from using the direct mode evaluation.

        Args:
            validation_results: the validation results from the direct mode evaluator.
        """
        self._validation_results = validation_results
        self._svrl_report = DefaultSVRLReportBuilder().create_svrl_xml(validation_results)
        self._is_valid = validation_results.is_valid()

    def get_svrl(self) -> _ElementTree:
        return self._svrl_report

    def is_valid(self) -> bool:
        return self._is_valid
