from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-09'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta, abstractmethod

from pyschematron_old.elements import Variable, Phase, Pattern, Namespace, Schema, Assert, Test, Report, \
    Rule, SchematronElement


class SchematronElementBuilder(metaclass=ABCMeta):
    """Builder pattern for constructing Schematron element classes."""

    @abstractmethod
    def build(self) -> SchematronElement:
        """Build a Schematron element based on the information in this builder.

        Returns:
            The constructed schematron element.
        """

    @abstractmethod
    def clear(self):
        """Clear the content of this builder."""

    @abstractmethod
    def set_attribute(self, name: str, value: str):
        """Set the value of a specific attribute.

        Note that the attributes can contain namespaces such as `xml:lang`.
        The builders will have to make sure to properly parse these attributes.

        Args:
            name: the name of the attribute
            value: the value of the attribute

        Raises:
            ValueError: if an unknown element was provided
        """

    @abstractmethod
    def set_text(self, value: str):
        """Add the text content of a node.

        Mixed content is supported by adding content with the :meth:`add_mixed_content`.

        Args:
            value: the text value of the node.
        """

    @abstractmethod
    def add_mixed_content(self, value: str):
        """Add a mixed content part to this node's content.

        The text nodes in Schematron are allowed to have mixed XML content such as <emph> and <dir> tags.
        During parsing, these are each visited separately. To make it easy to construct the objects, the builders
        offer the :meth:`add_mixed_content` method to allowing iteratively adding the content nodes.

        The added content should all be in string format, and is assumed to be concatenated into one content string.

        Note that the complete content of a node is the text of the node, together with the mixed content provided
        with this method.

        Args:
            value: the text value of the additional mixed content
        """

    @abstractmethod
    def add_child(self, element: SchematronElement):
        """Add a child element to the builder.

        The specific child elements allowed are dependent on the specific element being constructed.

        Args:
            element: the child element to add.

        Raises:
            ValueError: if an unknown element was provided.
        """


class SimpleElementBuilder(SchematronElementBuilder, metaclass=ABCMeta):

    def __init__(self):
        """Simple element builder accepting all kind of elements, processing only when building."""
        self._attributes = {}
        self._content = []
        self._children = []

    def clear(self):
        self._attributes = {}
        self._content = []
        self._children = []

    def set_attribute(self, name: str, value: str):
        self._attributes[name] = value

    def set_text(self, value: str):
        self._content.insert(0, value)

    def add_mixed_content(self, value: str):
        self._content.append(value)

    def add_child(self, element: SchematronElement):
        self._children.append(element)



class PatternBuilder(SimpleElementBuilder):

    def build(self) -> SchematronElement:
        rules = []
        variables = []

        for child in self._children:
            if isinstance(child, Rule):
                rules.append(child)
            elif isinstance(child, Variable):
                variables.append(child)
            else:
                raise ValueError(f'Unknown element presented {child}.')

        return Pattern(rules, variables, id=self._attributes.get('id'))


class RuleBuilder(SimpleElementBuilder):

    def build(self) -> SchematronElement:
        tests = []
        variables = []

        for child in self._children:
            if isinstance(child, Test):
                tests.append(child)
            elif isinstance(child, Variable):
                variables.append(child)
            else:
                raise ValueError(f'Unknown element presented {child}.')

        kwargs = {
            'tests': tests,
            'variables': variables
        }
        if 'context' in self._attributes:
            kwargs['context'] = self._attributes['context']

        return Rule(**kwargs)


class VariableBuilder(SimpleElementBuilder):

    def build(self) -> SchematronElement:
        return Variable(self._attributes['name'], self._attributes['value'])


class TestBuilder(SimpleElementBuilder, metaclass=ABCMeta):

    def build(self) -> SchematronElement:
        kwargs = {keyword: self._attributes.get(attr) for attr, keyword in Test.attributes_to_args.items()}
        return self._build_test(self._attributes['test'], ''.join(self._content), kwargs)

    @abstractmethod
    def _build_test(self, test: str, content: str, kwargs: dict[str, str]) -> Test:
        """Build the specific test (assert of report) based on the assembled data.

        Args:
            test: the test condition
            content: the content of the node
            kwargs: dictionary with constructed keyword arguments
        """


class AssertBuilder(TestBuilder):

    def _build_test(self, test: str, content: str, kwargs: dict[str, str]) -> Test:
        return Assert(test, content, **kwargs)


class ReportBuilder(TestBuilder):

    def _build_test(self, test: str, content: str, kwargs: dict[str, str]) -> Test:
        return Report(test, content, **kwargs)
