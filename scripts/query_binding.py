__author__ = 'Robbert Harms'
__date__ = '2023-03-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'


import time

import elementpath
import lxml.etree as etree



xml = etree.fromstring('''
<html>
    <body>
        <p>Test</p>
    </body>
</html>
''')


class XPathContextCopyable(elementpath.XPathContext):

    def with_item(self, item):
        return XPathContextCopyable(self.root, self.namespaces, item, self.position,
                                    self.size, self.axis, self.variables, self.current_dt, self.timezone,
                                    self.documents, self.collections, self.default_collection, self.text_resources,
                                    self.resource_collections, self.default_resource_collection, self.allow_environment,
                                    self.default_language, self.default_calendar, self.default_place)


context = XPathContextCopyable(xml, variables={'test': 1})

parser = elementpath.XPath2Parser()

# parser.register_custom_function(namespace='custom', local_name='string-length', inputs=['xs:string'],
#                                 output='xs:integer', callback=(lambda inputs: len(inputs[0])))
# parser.parse("custom:string-length('test')")

node = parser.parse('current-time()')
time.sleep(1)
node2 = parser.parse('$test * current-time()')

current_node = parser.parse('.')

print(node.evaluate(context))
print(node2.evaluate(context))


p_element = parser.parse('/html/body/p').evaluate(context)[0]
print(p_element)
print(current_node.evaluate(context.with_item(p_element)))
print(node.evaluate(context.with_item(p_element)))

print(node)



# elementpath.Selector


def lxml_xpath():
    p_node = xml.xpath('//html/body/p')[0]
    parent_selector = p_node.xpath('//html')
    return parent_selector


def elementpath_xpath():
    p_node = elementpath.select(xml, '//html/body/p')[0]
    parent_selector = elementpath.select(xml, '//html', item=p_node)
    return parent_selector


print(lxml_xpath())
print(elementpath_xpath())
