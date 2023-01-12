from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-10-09'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

import dataclasses
from abc import ABCMeta, abstractmethod
from copy import copy
from dataclasses import fields
from typing import Any, Type, Callable

import typing
from lxml import etree
from pyschematron.elements import Variable, Phase, Pattern, Namespace, Schema, RuleMessage, Assert, Test, Report, \
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


class ElementBuilderABC(ABCMeta):
    """A metaclass for building Schematron elements.

    This metaclass allows constructing builders directly from the definitions of the elements.
    That is, given a :class:`SchematronElement` this automatically generates all the builder pattern input methods.

    Using this class requires the class attribute "elements" to be set and pointing towards a specific
    :class:`Schematron` element to use.

    This assumes the SchematronElement classes are dataclasses. This metaclass will inspect those fields and
    create builder pattern methods for each of the available init fields. That is, for all variables it will add
    a method named `set_xxx(value)` with as xxx the field name. Additionally, for list and tuple variables it will add
    an `add_xxx(value)` which will add to the construction value, and for dict variables it will add the
    `update_xxx(key, value)` which updates the dictionary construction value.
    """

    def __new__(mcs, name, bases, attributes):
        """Construct a new class by loading the provided elements.

        This uses the attribute "element" to dynamically create the builder methods for that element.
        """
        if not attributes.get('element'):
            @abstractmethod
            def build():
                """Abstract build method"""

            @abstractmethod
            def clear():
                """Abstract build method"""

            attributes['build'] = build
            attributes['clear'] = clear

            return super().__new__(mcs, name, bases, attributes)

        attributes['build'] = mcs.get_build_method(attributes)
        attributes['clear'] = mcs.get_clear_method()
        attributes.update(mcs.get_builder_methods(attributes['element']))

        new_cls = super().__new__(mcs, name, bases, attributes)

        setattr(new_cls, '__init__', mcs.get_new_init(new_cls, attributes))

        return new_cls

    @classmethod
    def get_build_method(cls, cls_attributes):
        """Get the build method constructing our element."""
        def build(self):
            return cls_attributes['element'](**self._build_kwargs)
        return build

    @classmethod
    def get_clear_method(cls):
        """Get the clear method for the builder pattern."""
        def clear(self):
            self._build_kwargs = {}
        return clear

    @classmethod
    def get_new_init(mcs, cls, cls_attributes):
        """Get the new `__init__` method having the `_build_kwargs` as class variable."""
        old_init = cls_attributes.get('__init__')
        post_init = cls_attributes.get('__post__init__')

        element_variables = mcs.get_required_variables(cls_attributes['element'])

        def __init__(self, *args, **kwargs):
            if old_init:
                old_init(self, *args, **kwargs)
            else:
                super(cls, self).__init__(*args, **kwargs)

            self._build_kwargs = element_variables

            if post_init:
                post_init(self)

        return __init__

    @classmethod
    def get_builder_methods(mcs, element: Type[SchematronElement]) -> dict[str, Callable]:
        """Get the builder methods we can use for constructing the Schematron element.

        Suppose we have a schematron element like this::

            class Test(SchematronElement):
                foo: str
                bar: list[str]


        For construction, this schematron element needs two inputs, foo, a string and bar, a list of string.
        This builder metaclass will automatically generate the methods :meth:`set_foo(value: str)` and
        :meth:`add_bar(value: str)` which will set the value for `foo` and add a value to `bar`.

        Args:
            element: the schematron element we want builder methods for.

        Returns:
            A dictionary of builder methods.
        """
        builder_methods = {}

        def generate_add_method(field_name):
            def add_method(self, value):
                self._build_kwargs[field_name].append(value)
            return add_method

        def generate_update_method(field_name):
            def update_method(self, key, value):
                self._build_kwargs[field_name][key] = value
            return update_method

        def generate_set_method(field_name):
            def set_method(self, value):
                self._build_kwargs[field_name] = value
            return set_method

        element_type_hints = typing.get_type_hints(element)
        for field in fields(element):
            if field.init:
                if composite_type := typing.get_origin(element_type_hints[field.name]):
                    if issubclass(composite_type, (list, tuple)):
                        builder_methods[f'add_{field.name}'] = generate_add_method(field.name)
                    if issubclass(composite_type, dict):
                        builder_methods[f'update_{field.name}'] = generate_update_method(field.name)
                builder_methods[f'set_{field.name}'] = generate_set_method(field.name)

        return builder_methods

    @classmethod
    def get_required_variables(mcs, element: Type[SchematronElement]) -> dict[str, Any]:
        """Get the required init variables from the SchematronElement we are creating a builder class for.

        Args:
            element: the element we are creating a builder for

        Returns:
            A dictionary of required init variables.
        """
        element_type_hints = typing.get_type_hints(element)

        variables = {}
        for field in fields(element):
            if field.init:
                if composite_type := typing.get_origin(element_type_hints[field.name]):
                    print(field.name, composite_type)
                    if issubclass(composite_type, (list, tuple)):
                        variables[field.name] = []
                    elif issubclass(composite_type, dict):
                        variables[field.name] = {}
                    else:
                        variables[field.name] = None
                else:
                    if isinstance(field.default, type(dataclasses.MISSING)):
                        variables[field.name] = None
        return variables


class BaseSchematronElementBuilder(SchematronElementBuilder, metaclass=ElementBuilderABC):
    element: SchematronElement = None


class TestBuilder(BaseSchematronElementBuilder):
    element = Test


class AssertBuilder(TestBuilder):
    element = Assert
    
    def add_message_part(self, message_part: str | etree.Element):
        """Add a part of the message.

        This allows constructing the message from one or more string and XML elements

        Args:
             message_part: the message part to append
        """
        self._build_kwargs.append(message_part)

    def prepend_message_part(self, message_part: str | etree.Element):
        """Insert a message part at the beginning of the parts.

        Args:
            message_part: the message part to put in front of all the others
        """
        self.message_parts.insert(0, message_part)



class SchemaBuilder:

    def __init__(self):
        """Builder pattern for the Schema element."""
        self.variables: list[Variable] = []
        self.phases: list[Phase] = []
        self.patterns: list[Pattern] = []
        self.namespaces: list[Namespace] = []
        self.title: str | None = None
        self.default_phase: str | None = None

    def build(self) -> Schema:
        """Build the Schema from all the information we have."""
        return Schema(self.variables, self.phases, self.patterns,
                      self.namespaces, self.title, self.default_phase)

    def clear(self):
        """Clear the content of this builder."""
        self.variables = []
        self.phases = []
        self.patterns = []
        self.namespaces = []
        self.title = None
        self.default_phase = None

    def add_variable(self, variable: Variable):
        """Add a variable to this builder.

        Args:
            variable: the variable to add
        """
        self.variables.append(variable)

    def add_phase(self, phase: Phase):
        """Add a phase to this builder.

        Args:
            phase: the phase to add
        """
        self.phases.append(phase)

    def add_pattern(self, pattern: Pattern):
        """Add a pattern to this builder.

        Args:
            pattern: the pattern to add
        """
        self.patterns.append(pattern)

    def add_namespace(self, namespace: Namespace):
        """Add a namespace to this builder.

        Args:
            namespace: the namespace to add
        """
        self.namespaces.append(namespace)

    def set_title(self, title: str | None):
        """Set the title to the provided value.

        Args:
            title: the new title for the Schema element
        """
        self.title = title

    def set_default_phase(self, default_phase: str | None):
        """Set the default phase to the provided value.

        Args:
            default_phase: the new default phase for the Schema element
        """
        self.default_phase = default_phase


class RuleBuilder:

    def __init__(self):
        """Builder class for building Rule tags."""
        self.context: str = ''
        self.rule_elements: list[Test] = []
        self.variables: list[Variable] = []

    def build(self) -> Rule:
        """Build the Rule with all the information we have.

        Returns:
            The build Rule
        """
        return Rule(self.context, self.rule_elements, self.variables)

    def set_context(self, context: str):
        """Set the context attribute.

        Args:
            context: the context string
        """
        self.context = context

    def add_rule_element(self, rule_element: Test):
        """Add a rule element (assert or report).

        Args:
            rule_element: the rule element to add
        """
        self.rule_elements.append(rule_element)


class TestBuilder(metaclass=ABCMeta):

    def __init__(self):
        """Base class for building test elements (assert and report)."""
        self.test: str = ''
        self.message_parts = []
        self.id: str | None = None

    @abstractmethod
    def build(self) -> Test:
        """Build the rule element with all the information we have.

        Returns:
            The specific rule element as dictated by the subclass.
        """

    def clear(self):
        """Clear the content of this builder."""
        self.test = None
        self.message_parts = []
        self.id = None

    def set_test(self, test: str):
        """Set the test condition.

        Args:
            test: the test condition
        """
        self.test = test

    def add_message_part(self, message_part: str | etree.Element):
        """Add a part of the message.

        This allows constructing the message from one or more string and XML elements

        Args:
             message_part: the message part to append
        """
        self.message_parts.append(message_part)

    def prepend_message_part(self, message_part: str | etree.Element):
        """Insert a message part at the beginning of the parts.

        Args:
            message_part: the message part to put in front of all the others
        """
        self.message_parts.insert(0, message_part)

    def set_message_parts(self, message_parts: list[str | etree.Element]):
        """Set the entire message parts to this data.

        This overwrites the current list.

        Args:
            message_parts: the message parts which form this rule element.
        """
        self.message_parts = copy(message_parts)

    def set_id(self, id: str):
        """Set the id of this assertion.

        Args:
            id: the ID of this assertion
        """
        self.id = id


# class AssertBuilder(TestBuilder):
#
#     def build(self) -> Assert:
#         return Assert(self.test, RuleMessage(self.message_parts), self.id)


class ReportBuilder(TestBuilder):

    def build(self) -> Report:
        return Report(self.test, RuleMessage(self.message_parts), self.id)
