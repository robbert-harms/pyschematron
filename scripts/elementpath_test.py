__author__ = 'Robbert Harms'
__date__ = '2024-12-22'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pathlib import Path

from elementpath import XPathContext, get_node_tree, TextNode
from elementpath.xpath31 import XPath31Parser

from pyschematron.utils import load_xml_document

schematron_xml = load_xml_document(Path('/home/robbert/programming/python/githubtests/pyschematron/bug_6/test.xml'))
xml_tree = get_node_tree(root=schematron_xml.getroot())

xpath_context = {'root': xml_tree}

context = XPathContext(**xpath_context)
parser = XPath31Parser()
context_query = parser.parse("item[term[matches(., '^[a-z]+\)$')]][position() gt 1]")
test_query = parser.parse("let $index := term => substring-before(')') => string-to-codepoints(), $index2 := preceding-sibling::item[1]/term => substring-before(')') => string-to-codepoints() return every $bool in for-each-pair($index, $index2, function($a, $b) { $a = $b + 1 }) satisfies $bool")


def node_matches_context(xml_node) -> bool:
    parent_context = XPathContext(**(xpath_context | {'item': xml_node.parent}))

    if matches := context_query.evaluate(parent_context):
        if xml_node in matches:
            return True
    return False


def evaluate_node(node, context):
    if not node_matches_context(node):
        return
    assert_context = XPathContext(**(xpath_context | {'item': node}))
    test_result = test_query.evaluate(context=assert_context)
    print(test_result)


node_results = []
for node in xml_tree.iter_lazy():
    if not node.parent:
        continue

    if not isinstance(node, TextNode):
        if node_result := evaluate_node(node, context):
            node_results.append(node_result)

print(node_results)
