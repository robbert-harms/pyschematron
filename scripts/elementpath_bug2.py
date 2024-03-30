import elementpath
import lxml.etree as etree
from elementpath import get_node_tree

xml = etree.fromstring('<root id="test"></root>')
node_tree = get_node_tree(root=xml)

print(elementpath.__version__)

print('Round 1, iterate without accessing attributes:')
for node in node_tree.iter():
    print(node)

print('\nRound 2, same as nmr 1:')
for node in node_tree.iter():
    print(node)

print('\nRound 3, now we access the attributes:')
for node in node_tree.iter():
    node.attributes
    print(node)

print('\nRound 4, iterate again without accessing attributes:')
for node in node_tree.iter():
    print(node)


"""This prints:
4.3.0
Round 1, iterate without accessing attributes:
ElementNode(elem=<Element root at 0x7f118cde6940>)

Round 2, same as nmr 1:
ElementNode(elem=<Element root at 0x7f118cde6940>)

Round 3, now we access the attributes:
ElementNode(elem=<Element root at 0x7f118cde6940>)
AttributeNode(name='id', value='test')

Round 4, iterate again without accessing attributes:
ElementNode(elem=<Element root at 0x7f118cde6940>)
AttributeNode(name='id', value='test')
"""
