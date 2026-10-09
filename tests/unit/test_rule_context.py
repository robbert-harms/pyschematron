"""Tests for matching rule contexts to nodes, and for evaluating the checks of a rule."""

__author__ = 'Edward Jiang'
__date__ = '2026-09-30'

import pytest
from lxml import etree

from pyschematron.direct_mode.api import DirectModeSchematronValidatorFactory


def _schema(rules: str, query_binding: str = 'xslt2', lets: str = '') -> etree._ElementTree:
    return etree.ElementTree(etree.fromstring(
        f'<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="{query_binding}">'
        f'{lets}<pattern>{rules}</pattern></schema>'))


def _failed_asserts(validator, xml: str) -> list[str]:
    svrl = validator.validate(etree.ElementTree(etree.fromstring(xml))).get_svrl().getroot()
    return [el.get('location') for el in svrl if etree.QName(el).localname == 'failed-assert']


def _matched_locations(context: str, xml: str, query_binding: str = 'xslt2', lets: str = '') -> list[str]:
    """Get the locations of the nodes matching a rule context, using a rule that always fails."""
    schema = _schema(f'<rule context="{context}"><assert test="false()">matched</assert></rule>',
                     query_binding=query_binding, lets=lets)
    return _failed_asserts(DirectModeSchematronValidatorFactory(schema).build(), xml)


@pytest.mark.parametrize('context, xml, expected', [
    # a single step, which already worked
    ('b', '<root><a><b/></a></root>', ['/Q{}root[1]/Q{}a[1]/Q{}b[1]']),
    # more than one step, at any depth
    ('a/b', '<root><a><b/></a><x><a><b/></a></x><b/></root>',
     ['/Q{}root[1]/Q{}a[1]/Q{}b[1]', '/Q{}root[1]/Q{}x[1]/Q{}a[1]/Q{}b[1]']),
    ('x/a/b', '<root><a><b/></a><x><a><b/></a></x></root>', ['/Q{}root[1]/Q{}x[1]/Q{}a[1]/Q{}b[1]']),
    # a union inside a predicate is not a union of rule contexts
    ('a[b|c]/d', '<root><a><c/><d/></a><a><d/></a></root>', ['/Q{}root[1]/Q{}a[1]/Q{}d[1]']),
    # predicates keep match pattern semantics: the first b child of each parent
    ('b[1]', '<root><a><b/><b/></a><b/></root>', ['/Q{}root[1]/Q{}a[1]/Q{}b[1]', '/Q{}root[1]/Q{}b[1]']),
    # unions, mixing relative and absolute branches
    ('a/b | /root/c', '<root><a><b/></a><c/><x><c/></x></root>',
     ['/Q{}root[1]/Q{}a[1]/Q{}b[1]', '/Q{}root[1]/Q{}c[1]']),
    ('(a|x)/b', '<root><a><b/></a><x><b/></x><y><b/></y></root>',
     ['/Q{}root[1]/Q{}a[1]/Q{}b[1]', '/Q{}root[1]/Q{}x[1]/Q{}b[1]']),
    ('//x/b', '<root><x><b/></x><b/></root>', ['/Q{}root[1]/Q{}x[1]/Q{}b[1]']),
    ('/', '<root/>', ['/']),
    # attributes and function calls
    ('a/@id', '<root><a id="1"/><b id="2"/></root>', ['/Q{}root[1]/Q{}a[1]/@id']),
    ("id('k')", '<root><a xml:id="k"/><a xml:id="j"/></root>', ['/Q{}root[1]/Q{}a[1]']),
])
def test_rule_context_matches_like_an_xslt_pattern(context, xml, expected):
    assert _matched_locations(context, xml) == expected


def test_rule_context_with_variable():
    lets = '<let name="as" value="/root/a"/>'
    assert _matched_locations('$as/b', '<root><a><b/></a><x><b/></x></root>', lets=lets) == [
        '/Q{}root[1]/Q{}a[1]/Q{}b[1]']


def test_rule_context_with_xpath1_binding():
    assert _matched_locations('a/b', '<root><x><a><b/></a></x></root>', query_binding='xslt') == [
        '/Q{}root[1]/Q{}x[1]/Q{}a[1]/Q{}b[1]']


def test_validator_reused_for_another_document():
    schema = _schema('<rule context="a/b"><assert test="false()">matched</assert></rule>')
    validator = DirectModeSchematronValidatorFactory(schema).build()

    assert _failed_asserts(validator, '<root><a><b/></a></root>') == ['/Q{}root[1]/Q{}a[1]/Q{}b[1]']
    assert _failed_asserts(validator, '<root><x/></root>') == []
    assert _failed_asserts(validator, '<other><a><b/><b/></a></other>') == [
        '/Q{}other[1]/Q{}a[1]/Q{}b[1]', '/Q{}other[1]/Q{}a[1]/Q{}b[2]']


def test_checks_in_a_rule_do_not_share_the_context_item():
    schema = _schema('<rule context="a">'
                     '<assert test="exists(b/c)">first</assert>'
                     '<assert test="exists(b/c)">second, identical test</assert>'
                     '<assert test="b/c >= 0">third, compares a number</assert>'
                     '</rule>')
    validator = DirectModeSchematronValidatorFactory(schema).build()

    assert _failed_asserts(validator, '<root><a><b><c>100</c></b></a></root>') == []
