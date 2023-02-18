__author__ = 'Robbert Harms'
__date__ = '2023-01-19'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from abc import ABCMeta, abstractmethod
from typing import Type

import jinja2 as jinja2

from pyschematron_old.elements import SchematronElement, Report, Assert, Variable, Rule, Pattern


class XMLWriter(metaclass=ABCMeta):

    @abstractmethod
    def to_string(self, element: SchematronElement) -> str:
        """Write a Schematron element to an XML string.

        Args:
            element: the element to write, we will write it recursively.

        Returns:
            A string with the XML content of the Schematron element(s).
        """


class JinjaXMLWriter(XMLWriter):

    def __init__(self):
        """Write the XML using Jinja2 templates."""

        self.macro_files: dict[Type[SchematronElement], str] = {
            Report: 'report.xml.jinja2',
            Assert: 'assert.xml.jinja2',
            Variable: 'let.xml.jinja2',
            Rule: 'rule.xml.jinja2',
            Pattern: 'pattern.xml.jinja2'
        }

        self.macro_names: dict[Type[SchematronElement], str] = {
            Report: 'render_report',
            Assert: 'render_assert',
            Variable: 'render_let',
            Rule: 'render_rule',
            Pattern: 'render_pattern'
        }

        default_kwargs = dict(
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=['jinja2.ext.do'],
            loader=jinja2.PackageLoader('pyschematron', 'data/templates/xml'))

        env = jinja2.Environment(**default_kwargs)
        env.globals['render_element'] = lambda element: self.to_string(element)
        env.globals['get_render_attributes'] = self.get_render_attributes
        env.globals['render_attributes'] = self.render_attributes
        self.jinja2_env = env

    def to_string(self, element: SchematronElement) -> str:
        template_name = self.macro_files[type(element)]
        template = self.jinja2_env.get_template(template_name)
        macro = getattr(template.module, self.macro_names[type(element)])
        return macro(element)

    @staticmethod
    def get_render_attributes(element: SchematronElement, items: list[str]) -> dict[str, str]:
        """Get the available render attributes from the given element.

        Args:
            element: the element from which we want to get the renderable attributes
            items: the list of attributes we would like to print if not None

        Returns:
            A dictionary with renderable attributes (attributes of the element which are not None).
        """
        attributes = {}
        for item in items:
            if (value := getattr(element, item)) is not None:
                attributes[item] = value
        return attributes

    @staticmethod
    def render_attributes(element: SchematronElement, items: list[str]) -> str:
        """Render the available attributes.

        This will render all the attributes which are not None.
        Internally this uses the function :func:`self.get_render_attributes` to get all the renderable attributes.

        If the string is not empty, it is prefixed with a single space to allow printing in the XML attributes.

        Args:
            element: the element from which we want to get the renderable attributes
            items: the list of attributes we would like to print if not None

        Returns:
            The rendered attributes prefixed with a space, or the empty string.
        """
        attributes = JinjaXMLWriter.get_render_attributes(element, items)
        rendered = ' '.join({f'{key}="{value}"' for key, value in attributes.items()})
        if rendered:
            return ' ' + rendered
        return ''

