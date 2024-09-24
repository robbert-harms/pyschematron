__author__ = 'Robbert Harms'
__date__ = '2022-02-25'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

from pathlib import Path
from typing import Literal

from lxml.etree import _ElementTree

from pyschematron.__version__ import __version__
from pyschematron.api import ValidationResult
from pyschematron.direct_mode.api import DirectModeSchematronValidatorFactory
from pyschematron.direct_mode.xml_validation.queries.base import CustomQueryFunction


def validate_document(xml_document: Path | _ElementTree,
                      schematron_schema: Path | _ElementTree,
                      phase: str | None = None,
                      custom_functions: dict[str, str | list[CustomQueryFunction]] | None = None,
                      mode: Literal['direct-mode'] = 'direct-mode') -> ValidationResult:
    """Validate an XML document using a Schematron schema.

    Args:
        xml_document: the XML document we would like to validate
        schematron_schema: the Schematron Schema we would like to load and use for the validation
        phase: the Schematron phase we would like to use, optional.
        custom_functions: a dictionary defining additional custom functions to add to the parser(s).
            This should at least contain the key 'query_binding' mapping to a query binding name, and the
            key 'custom_query_functions' specifying a list of custom query functions to add.
            For non-standard query binding language, you also need to provide the key 'base_query_binding'
            mapping to a standard query binding. Example usage:
            `{'query_binding': 'xpath31-custom', 'base_query_binding': 'xpath31', 'custom_query_functions': [...]}`.
        mode: which validation mode we would like to use, at the moment this only supports the 'direct-mode'.

    Returns:
        The validation result in an API wrapper.
    """
    validator_factory = DirectModeSchematronValidatorFactory(schematron_xml=schematron_schema, phase=phase)
    if custom_functions:
        validator_factory.add_custom_functions(**custom_functions)
    validator = validator_factory.build()
    return validator.validate(xml_document)


def validate_documents(xml_documents: list[Path | _ElementTree],
                       schematron_schema: Path | _ElementTree,
                       phase: str | None = None,
                       custom_functions: dict[str, str | list[CustomQueryFunction]] | None = None,
                       mode: Literal['direct-mode'] = 'direct-mode') -> list[ValidationResult]:
    """Validate multiple XML documents using the same Schematron schema.

    This assumes we would like to use the same Schematron phase for each validation. As such, we can afford a speed-up
    since we don't need to compile the Schematron every run again.

    Args:
        xml_documents: the XML documents we would like to validate
        schematron_schema: the Schematron Schema we would like to load and use for the validation
        phase: the Schematron phase we would like to use, optional.
        custom_functions: a dictionary defining additional custom functions to add to the parser(s).
            This should at least contain the key 'query_binding' mapping to a query binding name, and the
            key 'custom_query_functions' specifying a list of custom query functions to add.
            For non-standard query binding language, you also need to provide the key 'base_query_binding'
            mapping to a standard query binding. Example usage:
            `{'query_binding': 'xpath31-custom', 'base_query_binding': 'xpath31', 'custom_query_functions': [...]}`.
        mode: which validation mode we would like to use, at the moment this only supports the 'direct-mode'.

    Returns:
        The validation results in an API wrapper.
    """
    validator_factory = DirectModeSchematronValidatorFactory(schematron_xml=schematron_schema, phase=phase)
    if custom_functions:
        validator_factory.add_custom_functions(**custom_functions)
    validator = validator_factory.build()

    validation_results = []
    for document in xml_documents:
        validation_results.append(validator.validate(document))

    return validation_results


