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
from pyschematron.utils import load_xml_document


schematron_path = Path('../tests/fixtures/full_example/schema.sch')
schematron_xml = load_xml_document(schematron_path)
parsing_context = ParsingContext(base_path=schematron_path.parent)

# Parse the Schema
schematron_parser = SchemaParser()
schema = schematron_parser.parse(schematron_xml.getroot(), parsing_context)

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
