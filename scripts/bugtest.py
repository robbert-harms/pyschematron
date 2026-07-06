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



from pathlib import Path
from pyschematron import validate_document
from lxml import etree

schematron_xml = load_schematron_xml(
"""
<schema
    xmlns="http://purl.oclc.org/dsdl/schematron"
    queryBinding="xslt2">
<pattern>
  <rule context="/*">

    <report test="true()">
      hello world
    </report>

    <assert id="dummy" test="true()">always true</assert>

  </rule>
</pattern>
</schema>
""")

xml = etree.fromstring("<a/>")
result = validate_document(xml, schematron_xml)
print(etree.tostring(result.get_svrl(), pretty_print=True).decode('utf-8'))
