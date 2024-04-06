"""This script shows how to use custom Python functions inside your Schematron schema's.

The general idea is that you either overwrite an existing query binding language, or define a new query binding
with your custom functions loaded. Your custom functions will then be attached to the query parser defined for that
specific query language.

As an example. Suppose you have a small custom function named `custom-func()`, and you want to use it in your
Schematron Schema. Your Schema is defined using `queryBinding="xpath31"` and you wish to extend this with your
custom function. For clarity, you want to call your new query binding language "xpath31-custom". In your Schematron
schema you then use `queryBinding="xpath31-custom"`, and in your queries you can use the `custom-func()`. For
PySchematron to know about this function, you must define it and add it to the library. This module shows how.

There are three ways of interacting with the PySchematron direct-mode validator. The most simple is by using the
functional interface defined in the main module. Second, you can use a generalized API which might be extended in the
future with an XSLT methodology. Finally, you can use the full-blown direct-mode classes and methods. The latter is the
most complicated but gives the most control. Either of these though enables adding custom functions.
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


def get_example_schema() -> _ElementTree:
    """Get the example Schema for the examples.

    In this Schema, we defined a new query binding language `queryBinding="xpath31-custom"` which we will
    also need to add in PySchematron. Note also the use of `custom-func()`.

    Returns:
        The loaded Schema.
    """
    schematron = '''
    <schema xmlns="http://purl.oclc.org/dsdl/schematron"
            schemaVersion="iso"
            queryBinding="xpath31-custom"
            xml:lang="en"
            fpi="-//PYSCHEMATRON//DTD XML 1.0//EN">

        <ns prefix="c" uri="http://www.amazing-cargo.com/xml/data/2023"/>

        <pattern id="pa_check-banana">
            <p>Just a check on the banana's.</p>
            <rule subject="/c:cargo[1]" context="c:banana">
                <report test="@type = 'fruit'">Banana is a fruit <value-of select="custom-func(., 10)"/></report>
            </rule>
        </pattern>
    </schema>
    '''
    return load_xml_document(schematron)


def get_example_xml_document() -> _ElementTree:
    """Get the example XML document we wish to validate.

    This returns the XML document from the tests fixtures.

    Returns:
        The XML document we wish to validate.
    """
    return load_xml_document(Path('../tests/fixtures/full_example/cargo.xml'))


def custom_func(el: ElementNode, number: int) -> int:
    """An example of a custom function.

    It can have any number of inputs and outputs. This example takes an elementpath element as input and an integer.
    It returns the XPath node position times the provided number.
    """
    return el.position * number


def demo_functional_interface(xml_document: _ElementTree, schematron_xml: _ElementTree):
    """Showing how to add custom path functions using the functional interface.

    This uses the functional interface, the most simple method of interacting with PySchematron.

    Args:
        xml_document: the document we wish to validate
        schematron_xml: the Schematron Schema
    """
    custom_functions = {
        'query_binding': 'xpath31-custom',
        'base_query_binding': 'xpath31',
        'custom_query_functions': [SimpleCustomXPathFunction(custom_func, 'custom-func')]
    }

    result = validate_document(xml_document, schematron_xml, custom_functions=custom_functions)

    svrl = result.get_svrl()
    print(etree.tostring(svrl, pretty_print=True).decode('utf-8'))
    print(result.is_valid())


def demo_generic_api(xml_document: _ElementTree, schematron_xml: _ElementTree):
    """Showing how to add custom path functions using the general API.

    This uses the generic API which in the future might be extended using the XSLT method.

    Args:
        xml_document: the document we wish to validate
        schematron_xml: the Schematron Schema
    """
    validator_factory = DirectModeSchematronValidatorFactory(schematron_xml=schematron_xml)

    validator_factory.add_custom_functions('xpath31-custom',
                                           [SimpleCustomXPathFunction(custom_func, 'custom-func')], 'xpath31')

    validator = validator_factory.build()
    validation_result = validator.validate(xml_document)

    svrl = validation_result.get_svrl()
    print(etree.tostring(svrl, pretty_print=True).decode('utf-8'))
    print(validation_result.is_valid())


def demo_full_api(xml_document: _ElementTree, schematron_xml: _ElementTree):
    """Showing how to add custom path functions using the full direct-mode API.

    This is the most complex method, but shows how the direct-mode method operates.

    Args:
        xml_document: the document we wish to validate
        schematron_xml: the Schematron Schema

    """
    custom_xpath_function = SimpleCustomXPathFunction(custom_func, 'custom-func')

    custom_parser = XPath31QueryParser()
    custom_parser = custom_parser.with_custom_function(custom_xpath_function)

    custom_query_processor = XPathQueryProcessor(custom_parser)

    custom_processor_factory = ExtendableQueryProcessorFactory()
    custom_processor_factory.set_query_processor('xpath31-custom', custom_query_processor)

    schema = SchemaParser().parse(schematron_xml.getroot())

    validator = SimpleSchematronXMLValidator(schema, query_processor_factory=custom_processor_factory)
    validation_results = validator.validate_xml(xml_document)

    svrl = DefaultSVRLReportBuilder().create_svrl_xml(validation_results)

    print(etree.tostring(svrl, pretty_print=True).decode('utf-8'))
    print(validation_results.is_valid())


demo_functional_interface(get_example_xml_document(), get_example_schema())
demo_generic_api(get_example_xml_document(), get_example_schema())
demo_full_api(get_example_xml_document(), get_example_schema())

