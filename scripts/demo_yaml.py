"""This script demonstrates how to load a Schematron Schema in the PySchematron direct-mode.

This example shows the use of the direct-mode Abstract Syntax Tree (AST) for PySchematron Schemas. By loading Schematron
schema's in the AST, you can inspect the Schema using Python functionality.

Please note that only Schematron specific XML nodes are loaded from the Schematron Schema. Custom nodes are not loaded.
You can however augment the AST and the parser with your own nodes. This is however not demonstrated (here).
"""

__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

from pathlib import Path

from pyschematron.direct_mode.schematron.ast_visitors import ResolveExtendsVisitor, ResolveAbstractPatternsVisitor, \
    PhaseSelectionVisitor
from pyschematron.direct_mode.schematron.ast_yaml import RuyamlASTYamlConverter
from pyschematron.direct_mode.schematron.parsers.xml.parser import ParsingContext, SchemaParser
from pyschematron.utils import load_xml_document, load_schematron_xml



schematron_xml = load_schematron_xml(
"""
<schema xmlns="http://purl.oclc.org/dsdl/schematron"
        queryBinding="xslt2">
    <pattern>
        <rule context="/*">
            <report test="true()">
              hello world
            </report>
        </rule>
    </pattern>
</schema>
""")

"""
!Schema
patterns:
- !ConcretePattern
  rules:
  - !ConcreteRule
    checks:
    - !Report
      content: ["\n      hello world\n    "]
      test: !Query {query: true()}
    context: !Query {query: /*}
query_binding: xslt2
"""


# Parse the Schema
schematron_parser = SchemaParser()
schema = schematron_parser.parse(schematron_xml.getroot())

# Shows the use of the visitor pattern to modify the Schema
schema = ResolveExtendsVisitor(schema).apply(schema)
schema = ResolveAbstractPatternsVisitor(schema).apply(schema)
schema = PhaseSelectionVisitor(schema, '#ALL').apply(schema)

# Experimental, YAML conversion.
yaml_converter = RuyamlASTYamlConverter()
yaml_shema = yaml_converter.dump(schema)
round_trip = yaml_converter.load(yaml_shema)

print(yaml_shema)
print(round_trip == schema)
