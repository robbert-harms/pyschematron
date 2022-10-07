__author__ = 'Robbert Harms'
__date__ = '2022-10-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from pyschematron.elements import Schema


class PySchematron:

    def __init__(self, schema: Schema):
        ...




# import elementpath
# import lxml.etree as etree
#
# xml = etree.fromstring('''
# <html>
#     <body>
#         <p>Test</p>
#     </body>
# </html>
# ''')
#
# variables = {'node': 'html'}
#
# p_node = elementpath.select(xml, '//html/body/p')[0]
# parent_selector = elementpath.select(xml, '//*[name()=$node]', item=p_node, variables=variables)
# print(parent_selector)
