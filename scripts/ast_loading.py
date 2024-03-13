__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from pathlib import Path

from pyschematron.direct_mode.lib.ast_visitors import ResolveExtendsVisitor, ResolveAbstractPatternsVisitor
from pyschematron.direct_mode.lib.ast_yaml import RuyamlASTYamlConverter
from pyschematron.direct_mode.parsers.xml.parser import ParsingContext, SchemaParser
from pyschematron.utils import load_xml_document


schematron_path = Path('../tests/fixtures/full_example/schema.sch')
schematron_xml = load_xml_document(schematron_path)
parsing_context = ParsingContext(base_path=schematron_path.parent)

schematron_parser = SchemaParser()
schema = schematron_parser.parse(schematron_xml.getroot(), parsing_context)
schema = ResolveExtendsVisitor(schema).apply(schema)
schema = ResolveAbstractPatternsVisitor(schema).apply(schema)


def yaml_stuff():
    yaml_converter = RuyamlASTYamlConverter()

    yaml_shema = yaml_converter.dump(schema)
    print(yaml_shema)
    round_trip = yaml_converter.load(yaml_shema)
    print(schema)
    print(round_trip)
    print(round_trip == schema)


yaml_stuff()
