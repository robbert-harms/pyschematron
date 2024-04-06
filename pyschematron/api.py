"""Definition of the common API for validating an XML using Schematron.

This defines a common interface for Schematron validators to implement.

At the moment this is only implemented by direct mode evaluation, but in the future it might also support
the XSLT evaluation.
"""
from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2024-04-01'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta, abstractmethod
from pathlib import Path

from lxml.etree import _ElementTree

from pyschematron.direct_mode.xml_validation.queries.base import CustomQueryFunction


class SchematronValidatorFactory(metaclass=ABCMeta):
    """Factory class for generating Schematron validators.

    The Schematron validators do the hard work of validating an XML document. To ensure that a single validator can
    process multiple XML documents once set on a phase, we make the validators immutable and built them using this
    factory.
    """

    @abstractmethod
    def set_schema(self, schematron_xml: Path | _ElementTree):
        """Set the Schematron schema.

        Args:
            schematron_xml: the Schematron Schema we would like to use in the validation.
        """

    @abstractmethod
    def set_base_path(self, schematron_base_path: Path):
        """Set the Schematron base path.

        Some Schematron schemas include files from other locations. If you would like explicit control over the
        Schematron base path, or if the path could not be inferred from the provided schema, set it here explicitly.

        Args:
            schematron_base_path: the base path for the Schematron definition
        """

    @abstractmethod
    def set_phase(self, phase: str | None):
        """Set the phase we would like the Schematron validator to validate.

        By setting this before we load the Schematron validator, we can prepare the phase for evaluation, giving
        us some speed benefit.

        Args:
            phase: the phase we would like to validate. If set to None we use the '#DEFAULT' phase.
        """

    @abstractmethod
    def build(self) -> SchematronValidator:
        """Construct the configured Schematron validator.

        Returns:
            An implementation of the Schematron validator.
        """

    @abstractmethod
    def add_custom_functions(self,
                             query_binding: str,
                             custom_query_functions: list[CustomQueryFunction],
                             base_query_binding: str | None = None):
        """Add custom functions to the parser we would like to use.

        The custom query functions are added to the parser for a specific query binding language. Repeated calls
        accumulate the additional functions. If you create a new query binding specifier, you need to specify the base
        query binding language to use as basis for the new query binding language.

        Args:
            query_binding: the query binding language for which we are adding the custom query functions
            custom_query_functions: a list of custom query function objects
            base_query_binding: the basis to use for any new query binding language
        """


class SchematronValidator(metaclass=ABCMeta):
    """The Schematron validator, validating an XML document using the init injected Schematron definition."""

    @abstractmethod
    def validate(self, xml_data: Path | _ElementTree) -> ValidationResult:
        """Validate an XML document and return an SVRL XML document.

        Args:
            xml_data: the XML data we would like to validate

        Returns:
            The validation results.
        """


class ValidationResult(metaclass=ABCMeta):
    """Results from Schematron validation.

    This should be able to produce an SVRL XML document, and should be able to tell if the document was valid or not.
    """

    @abstractmethod
    def get_svrl(self) -> _ElementTree:
        """Get the SVRL as an XML element tree.

        Returns:
            The SVRL as an element tree.
        """

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if the document we validated was valid.

        A document is considered valid if all the reports were successful and none of the assertions were raised.

        Returns:
            If the document was valid return True, else False.
        """
