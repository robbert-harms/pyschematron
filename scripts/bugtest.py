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



# schematron_xml = load_xml_document(
# """
# <schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt2">
#   <pattern id="no-comments">
#     <rule context="comment()">
#       <assert test="false()">Comments are not allowed.</assert>
#     </rule>
#   </pattern>
# </schema>
# """)


parsing_context = ParsingContext()

schematron_parser = SchemaParser()
schema = schematron_parser.parse(schematron_xml.getroot(), parsing_context)
schema = ResolveExtendsVisitor(schema).apply(schema)
schema = ResolveAbstractPatternsVisitor(schema).apply(schema)
schema = PhaseSelectionVisitor(schema).apply(schema)

validator = SimpleSchematronXMLValidator(schema)

xml_document = load_xml_document("""
<foo/>
""")
validation_results = validator.validate_xml(xml_document)

svrl_report = DefaultSVRLReportBuilder().create_svrl_xml(validation_results)
report_str = etree.tostring(svrl_report, pretty_print=True).decode('utf-8')

with open('/tmp/report_pyschematron.xml', 'w') as f:
    f.write(report_str)

print(report_str)
print(validation_results.is_valid())
print(validation_results.is_valid(ignore_successful_reports=True))
print(validation_results.has_failed_asserts())
print(validation_results.has_successful_reports())

print()
