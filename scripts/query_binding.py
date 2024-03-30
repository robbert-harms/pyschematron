__author__ = 'Robbert Harms'
__date__ = '2023-03-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'


import time

import elementpath
import lxml.etree as etree
from elementpath.xpath3 import XPath3Parser

from pyschematron.direct_mode.xml_validation.queries.factories import SimpleQueryProcessorFactory
from pyschematron.direct_mode.xml_validation.queries.xpath import XPathQueryParser, XPath2QueryParser, \
    XPathEvaluationContext, SimpleCustomXPathFunction

xml = etree.fromstring('''
<html>
    <head id="test"></head>
    <body>
        <p>Test</p>
        <p>Test2</p>
    </body>
</html>
''')

query_processing_factory = SimpleQueryProcessorFactory().get_query_processor('xslt3')

parser = query_processing_factory.get_query_parser()
parser = parser.with_namespaces({'test': 'http://test.com'})
parser = parser.with_custom_function(SimpleCustomXPathFunction(lambda el: el * 5, 'mult', 'test'))

evaluation_context = query_processing_factory.get_evaluation_context()
evaluation_context = evaluation_context.with_namespaces({'c': 'http://www.amazing-cargo.com/xml/data/2023'})
evaluation_context = evaluation_context.with_xml_root(xml)
evaluation_context = evaluation_context.with_variables({'test': 100})
evaluation_context = evaluation_context.with_variables(
    {'test2': '<html xmlns="http://www.w3.org/1999/xhtml">info</html>'})

query = parser.parse('test:mult($test * count(//html/*))')
print(query.evaluate(evaluation_context))

print('test2', parser.parse('$test2').evaluate(evaluation_context))

query = parser.parse('@id')
sub_context = evaluation_context.with_xml_root(parser.parse('/html/head').evaluate(evaluation_context)[0])
print(query.evaluate(sub_context))

query = parser.parse('@id')
sub_context = evaluation_context.with_xml_root(parser.parse('/html/body').evaluate(evaluation_context)[0])
print(query.evaluate(sub_context))

query = parser.parse()

# context.add_variables({'max-weight': 'xs:integer(1000)')



def direct():

    class XPathContextCopyable(elementpath.XPathContext):

        def with_item(self, item):
            return XPathContextCopyable(self.root, self.namespaces, item, self.position,
                                        self.size, self.axis, self.variables, self.current_dt, self.timezone,
                                        self.documents, self.collections, self.default_collection, self.text_resources,
                                        self.resource_collections, self.default_resource_collection, self.allow_environment,
                                        self.default_language, self.default_calendar, self.default_place)

    parser = elementpath.XPath2Parser()

    context = XPathContextCopyable(xml, variables={'test': parser.parse('xs:integer(1000)').evaluate()})



    # parser.register_custom_function(namespace='custom', local_name='string-length', inputs=['xs:string'],
    #                                 output='xs:integer', callback=(lambda inputs: len(inputs[0])))
    # parser.parse("custom:string-length('test')")

    node = parser.parse('current-time()')
    time.sleep(1)
    node2 = parser.parse('$test * 5')

    current_node = parser.parse('.')

    print(node.evaluate(context))
    print(node2.evaluate(context))


    p_element = parser.parse('/html/body/p').evaluate(context)[0]
    print(p_element)
    print(current_node.evaluate(context.with_item(p_element)))
    print(node.evaluate(context.with_item(p_element)))

    print(node)

direct()


#
# # elementpath.Selector
#
#
# def lxml_xpath():
#     p_node = xml.xpath('//html/body/p')[0]
#     parent_selector = p_node.xpath('//html')
#     return parent_selector
#
#
# def elementpath_xpath():
#     p_node = elementpath.select(xml, '//html/body/p')[0]
#     parent_selector = elementpath.select(xml, '//html', item=p_node)
#     return parent_selector
#
#
# print(lxml_xpath())
# print(elementpath_xpath())
