__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

import sys
from io import StringIO
from pathlib import Path

from pyschematron.direct_mode.lib.ast_visitors import ResolveExtendsVisitor, ResolveAbstractPatternsVisitor
from pyschematron.direct_mode.lib.ast_yaml import ASTYaml
from pyschematron.direct_mode.parsers.xml.parser import ParsingContext, SchemaParser
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


def yaml_stuff():
    yaml = ASTYaml()
    # yaml.dump(schema, sys.stdout)

    yaml.dump({'b': 1, 'a': 2}, sys.stdout)

    with StringIO() as dumped:
        yaml.dump(schema, dumped)
        v = dumped.getvalue()
        print(v)
        loaded = yaml.load(v)
    print(loaded)
    print(loaded == schema)
yaml_stuff()
