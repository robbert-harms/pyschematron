"""A test script I use when developing PySchematron."""

__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

from pathlib import Path

import elementpath
from lxml import etree

from pyschematron.direct_mode.schematron.ast_visitors import ResolveExtendsVisitor, \
    ResolveAbstractPatternsVisitor, PhaseSelectionVisitor
from pyschematron.direct_mode.schematron.parsers.xml.parser import ParsingContext, SchemaParser
from pyschematron.direct_mode.xml_validation.results.svrl_builder import DefaultSVRLReportBuilder
from pyschematron.direct_mode.xml_validation.validators import SimpleSchematronXMLValidator
from pyschematron.utils import load_xml_document, load_schematron_xml

import time

start = time.perf_counter()

from lxml import etree
from pyschematron.direct_mode.api import DirectModeSchematronValidatorFactory

schema_str = """<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">"""
for ind in range(1):
    schema_str += """"<pattern>
        <rule context="a/b">
          <assert id="A1" test="false()">always fails</assert>
        </rule>
      </pattern>"""
schema_str += """</schema>"""

schema = etree.ElementTree(etree.fromstring(schema_str))
doc = etree.ElementTree(etree.fromstring("<root><a><b/></a></root>"))

svrl = DirectModeSchematronValidatorFactory(schema).build().validate(doc).get_svrl().getroot()
print([e.get("id") for e in svrl if etree.QName(e).localname == "failed-assert"])

# Expected ['A1'], got [].

elapsed = time.perf_counter() - start

print(f"Execution time: {elapsed:.6f} seconds")
