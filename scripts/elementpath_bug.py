import elementpath
import lxml.etree as etree
from elementpath import XPathContext, get_node_tree
from elementpath.xpath3 import XPath3Parser

"""
Dear ...

I am currently developing a Schematron parser which uses this `elementpath` library for all XPath expressions.
At the moment, I ran into an issue with the XPathContext `item` attribute.

Schematron consists of rules and checks. The rules provide for a `context` attribute which defines
the context for all checks within that rule.
My thought was to use this context node as `item` attribute in the XPathContext.
Unfortunately it does not work that way since the context defined by the `item` attribute does not include itself.

As a mini example. Suppose we have the following XML code:

```
<root id="id_test"></root>
```

Some Schematron code may wish to test if the ID attribute starts with the prefix "id_".
A valid Schematron file may be:

```
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt3">
    <pattern>
        <rule id="id_test" context="@id">
            <assert test="starts-with(., 'id_')">
                This id attribute does not start with "id_".
            </assert>
        </rule>
    </pattern>
</schema>
```

The processing order of a Schematron is:

1. for every node in the XML, test if it matches a context node
2. if so, load that node as the context
3. process the assert nodes given that context.

In Python code, something like:

```
xml = etree.fromstring('<root id="id_test"></root>')

parser = XPath3Parser()
context_query = parser.parse('root')
test_query = parser.parse("starts-with(@id, 'id_')")

for node in xml.iter():
    print('Evaluating node:', node)

    print('Setting XPath context to node')
    xpath_context = XPathContext(xml, item=node)

    print('Checking if the current node matches the Schematron context')
    if context_query.evaluate(xpath_context):
        print('Evaluating the test query')
        print(test_query.evaluate(xpath_context))
```

Unfortunately the part where it says "Evaluating the test query" never gets executed.

As a smaller version of the above, I expect this to work:

```
xml = etree.fromstring('<root id="id_test"></root>')
parser = XPath3Parser()
assert len(parser.parse('root').evaluate(XPathContext(xml, item=xml.xpath('//root')[0])))
```

I suspect that when you set the `item` attribute, it only searches downwards from there, excluding the
current node from all evaluations.

This is unfortunately a major blocker for me to finish my work on PySchematron.
Is there something you can do?
Could you redefine the `item` setting of the XPathContext to also take into account the current node
as part of the evaluation?

Thanks a lot,

Robbert
"""


xml = etree.fromstring('''
<root id="id_test">
    <!-- Comment: This is a comment -->
    <test></test>
</root>
''')


def small_example():
    xml = etree.fromstring('<test><root id="id_test"></root></test>')
    document_node = get_node_tree(root=etree.ElementTree(xml))

    parser = XPath3Parser()
    # context_query = parser.parse('root')
    # test_query = parser.parse("starts-with(@id, 'id_')")
    context_query = parser.parse('@id')
    test_query = parser.parse('starts-with(., "id_")')

    def evaluate_node(node):
        print('Evaluating node:', node)
        if node.parent:
            print(f'Setting XPath context to node {node}')

            if context_query.evaluate(XPathContext(document_node, item=node.parent)):
                test_result = test_query.evaluate(XPathContext(document_node, item=node))
                print('Test result node', test_result)

        if node.attributes:
            for attribute in node.attributes:
                if context_query.evaluate(XPathContext(attribute.parent)):
                    test_result = test_query.evaluate(XPathContext(document_node, item=attribute))
                    print('Test result attribute', test_result)

    for node in document_node.iter():
        evaluate_node(node)


small_example()
exit()


schematron = etree.fromstring('''
<schema xmlns="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt3">
<pattern>
        <rule id="ru_comments-test" context="comment()">
            <assert test="starts-with(., ' Comment: ')">
                This comment does not start with "Comment: ".
            </assert>
        </rule>
    </pattern>
</schema>
''')


xml = etree.fromstring('<root id="id_test"></root>')
parser = XPath3Parser()
context = XPathContext(xml, item=xml.xpath('//root')[0])
assert len(parser.parse('root').evaluate(context))


def check_comment():
    context_item = xml.xpath('//comment()')[0].getparent()
    xpath_context = XPathContext(xml, item=context_item)

    context_query = parser.parse('comment()')
    test_query = parser.parse("starts-with(., ' Comment: ')")

    print(context_query.evaluate(xpath_context))
    print(test_query.evaluate(xpath_context))


def check_attribute():
    context = XPathContext(xml, item=xml.xpath('@id')[0])
    context_query = parser.parse('@id')
    test_query = parser.parse("starts-with(., 'id_')")

    print(context_query.evaluate(context))
    print(test_query.evaluate(context))


check_comment()
check_attribute()
