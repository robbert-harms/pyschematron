__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

import sys
from io import StringIO
from pathlib import Path
from pprint import pprint

from pyschematron.direct_mode.lib.ast_visitors import FindIdVisitor, GetIDMappingVisitor, ResolveExtendsVisitor, \
    ResolveAbstractPatternsVisitor, PhaseSelectionVisitor, QueryBindingVisitor

from pyschematron.direct_mode.lib.ast_yaml import ASTYaml
from pyschematron.direct_mode.parsers.xml.parser import ParsingContext, SchemaParser
from pyschematron.direct_mode.validators.queries.factories import DefaultQueryBindingFactory
from pyschematron.direct_mode.validators.validators import SimpleSchematronXMLValidator
from pyschematron.utils import load_xml


'''
java -jar ~/programming/java/schxslt-cli.jar -d cargo.xml -s schema.sch -o /tmp/report.xml
'''

schematron_path = Path('../tests/fixtures/full_example/schema.sch')
schematron_xml = load_xml(schematron_path)
parsing_context = ParsingContext(base_path=schematron_path.parent)

schematron_parser = SchemaParser()
schema = schematron_parser.parse(schematron_xml, parsing_context)
schema = ResolveExtendsVisitor(schema).apply(schema)
schema = ResolveAbstractPatternsVisitor(schema).apply(schema)
schema = PhaseSelectionVisitor(schema, '#ALL').apply(schema)

namespaces = {ns.prefix: ns.uri for ns in schema.namespaces}

query_binding_language = schema.query_binding or 'xslt'
query_processing_factory = DefaultQueryBindingFactory().get_query_processing_factory(query_binding_language)
query_parser = query_processing_factory.get_query_parser()
query_parser = query_parser.with_namespaces(namespaces)

bound_schema = QueryBindingVisitor(query_parser).apply(schema)

# validator = SimpleSchematronXMLValidator(schema, '#DEFAULT', parsing_context.base_path)


print(schema)

# validator = SimpleSchematronXMLValidator.from_schema(schema)



