__author__ = 'Robbert Harms'
__date__ = '2023-01-19'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from abc import ABCMeta, abstractmethod
from typing import Type

import jinja2 as jinja2

from pyschematron.elements import SchematronElement, Report, RuleMessage


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

        self.xml_templates: dict[Type[SchematronElement], str] = {
            Report: 'report.xml.jinja2',
            RuleMessage: 'rule_message.xml.jinja2'
        }
        self.xml_variables: dict[Type[SchematronElement], str] = {
            Report: 'report',
            RuleMessage: 'rule_message'
        }

        default_kwargs = dict(
            trim_blocks=True,
            lstrip_blocks=True,
            loader=jinja2.PackageLoader('pyschematron', 'data/templates/xml'))

        env = jinja2.Environment(**default_kwargs)
        self.jinja2_env = env

    def to_string(self, element: SchematronElement) -> str:
        template_name = self.xml_templates[type(element)]
        template = self.jinja2_env.get_template(template_name)
        variable_name = self.xml_variables[type(element)]
        return template.render({variable_name: element})
