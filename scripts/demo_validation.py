"""This script demonstrates using the direct-mode PySchematron validator to validate your XML documents.

In Schematron validation, we apply a Schematron Schema to an XML resulting in either a pass or a fail. A fail indicates
that the document could not be validated using the Schema, hence the XML may have problems. In addition to this boolean
output, Schematron also defines the Schematron Validation Report Language (SVRL), loosely defining a format in which
more information about the validation results can be represented.

This script shows three different ways of interacting with the PySchematron direct-mode validator. The most simple is
by using the functional interface defined in the main module. Second, you can use a generalized API which might be
extended in the future with an XSLT methodology. Finally, you can use the full-blown direct-mode classes and methods.
The latter is the most complicated but gives the most control.
"""

__author__ = 'Robbert Harms'
__date__ = '2024-04-03'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pathlib import Path

from elementpath import ElementNode
from lxml import etree
from lxml.etree import _ElementTree

from pyschematron import DirectModeSchematronValidatorFactory, validate_document
from pyschematron.direct_mode.schematron.parsers.xml.parser import SchemaParser
from pyschematron.direct_mode.xml_validation.queries.factories import ExtendableQueryProcessorFactory
from pyschematron.direct_mode.xml_validation.queries.xpath import (XPathQueryProcessor, XPath31QueryParser,
                                                                   SimpleCustomXPathFunction)
from pyschematron.direct_mode.xml_validation.results.svrl_builder import DefaultSVRLReportBuilder
from pyschematron.direct_mode.xml_validation.validators import SimpleSchematronXMLValidator
from pyschematron.utils import load_xml_document


# the paths to the example data and Schema
example_base_path = Path('../tests/fixtures/full_example/')
schematron_schema_path = example_base_path / 'schema.sch'
example_xml_document_path = example_base_path / 'cargo.xml'

# the phase we would like to evaluate
phase = '#ALL'


def demo_functional_interface():
    """This example uses the functional interface, the most simple method of interacting with PySchematron. """
    validator_factory = DirectModeSchematronValidatorFactory()
    validator_factory.set_schema(schematron_schema_path)
    validator_factory.set_phase(phase)

    validator = validator_factory.build()
    validation_result = validator.validate(example_xml_document_path)

    svrl = validation_result.get_svrl()
    report_str = etree.tostring(svrl, pretty_print=True).decode('utf-8')

    print(report_str)
    print(validation_result.is_valid())



def demo_generic_api():
    """This demonstrates the use of the generic API."""



def demo_full_api():
    """This demonstrates the inner workings of the direct-mode validator."""


demo_functional_interface()
demo_generic_api()
demo_full_api()

