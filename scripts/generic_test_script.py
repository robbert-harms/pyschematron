"""A test script I use when developing PySchematron."""

__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

from pathlib import Path

from lxml import etree

from pyschematron.direct_mode.schematron.ast_visitors import ResolveExtendsVisitor, \
    ResolveAbstractPatternsVisitor, PhaseSelectionVisitor
from pyschematron.direct_mode.schematron.parsers.xml.parser import ParsingContext, SchemaParser
from pyschematron.direct_mode.xml_validation.results.svrl_builder import DefaultSVRLReportBuilder
from pyschematron.direct_mode.xml_validation.validators import SimpleSchematronXMLValidator
from pyschematron.utils import load_xml_document

'''
cd programming/python/pyschematron/tests/fixtures/full_example/
java -jar ~/programming/java/schxslt-cli.jar -d cargo.xml -s schema.sch -o /tmp/report.xml
'''

example_path = Path('../tests/fixtures/full_example/')
schematron_path = example_path / 'schema.sch'
phase = '#ALL'

schematron_xml = load_xml_document(schematron_path)
parsing_context = ParsingContext(base_path=schematron_path.parent)

schematron_parser = SchemaParser()
schema = schematron_parser.parse(schematron_xml.getroot(), parsing_context)
schema = ResolveExtendsVisitor(schema).apply(schema)
schema = ResolveAbstractPatternsVisitor(schema).apply(schema)
schema = PhaseSelectionVisitor(schema, phase).apply(schema)

validator = SimpleSchematronXMLValidator(schema, phase, parsing_context.base_path)

xml_document = load_xml_document(example_path / 'cargo.xml')
validation_results = validator.validate_xml(xml_document)

svrl_report = DefaultSVRLReportBuilder().create_svrl_xml(validation_results)
report_str = etree.tostring(svrl_report, pretty_print=True).decode('utf-8')

with open('/tmp/report_pyschematron.xml', 'w') as f:
    f.write(report_str)

print(report_str)

print()
