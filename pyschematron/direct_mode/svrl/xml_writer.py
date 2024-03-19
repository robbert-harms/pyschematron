__author__ = 'Robbert Harms'
__date__ = '2024-03-17'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta, abstractmethod
from typing import override

from lxml.etree import Element, _Element
from pyschematron.direct_mode.svrl.svrl_ast import SchematronOutput, SVRLNode, NSPrefixInAttributeValues, Text, \
    ActivePattern, MetaData
from pyschematron.direct_mode.svrl.svrl_visitors import SVRLASTVisitor


class SVRLXMLWriter(metaclass=ABCMeta):
    """Type class for SVRL XML writers."""

    @abstractmethod
    def create_xml(self, schematron_output: SchematronOutput) -> _Element:
        """Transform a Schematron output SVRL root node, to an XML element.

        Args:
            schematron_output: the root node of an SVRL AST.

        Returns:
            An XML representation of the provided SVRL output node.
        """


class LxmlSVRLXMLWriter(SVRLXMLWriter):
    """SVRL writer using the Lxml library."""

    @override
    def create_xml(self, schematron_output: SchematronOutput) -> _Element:
        nsmap = {
            'svrl': 'http://purl.oclc.org/dsdl/svrl',
            'sch': 'http://purl.oclc.org/dsdl/schematron',
            'xs': 'http://www.w3.org/2001/XMLSchema'
        }
        writer_visitor = _SVRLWriterVisitor(nsmap)
        return writer_visitor.visit(schematron_output)


class _SVRLWriterVisitor(SVRLASTVisitor):

    def __init__(self, nsmap: dict[str, str]):
        """SVRL XML writer using the visitor pattern.

        Args:
            nsmap: the default namespaces to apply in the SVRL.
        """
        self._nsmap = nsmap

    @override
    def visit(self, svrl_node: SVRLNode) -> _Element | None:
        match svrl_node:
            case SchematronOutput():
                return self._process_schematron_output(svrl_node)
            case NSPrefixInAttributeValues():
                return self._process_ns_prefix_node(svrl_node)
            case MetaData():
                return self._process_metadata(svrl_node)
            case ActivePattern():
                return self._process_active_pattern_node(svrl_node)
            case Text():
                return self._process_text_node(svrl_node)
        return None

    def _process_schematron_output(self, schematron_output: SchematronOutput) -> _Element:
        """Process the SchematronOutput node, the root of the SVRL.

        Args:
            schematron_output: the SVRL root node

        Returns:
            An element representing the SVRL report.
        """
        for ns_prefix in schematron_output.ns_prefix_in_attribute_values:
            if ns_prefix.prefix in self._nsmap:
                raise ValueError(f'Provided namespace "{ns_prefix.prefix}" is not allowed in the Schematron, '
                                 f'it overlaps with the default SVRL namespaces.')
            else:
                self._nsmap[ns_prefix.prefix] = ns_prefix.uri

        node_attributes = {
            'phase': schematron_output.phase,
            'schemaVersion': schematron_output.schema_version,
            'title': schematron_output.title
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        root = Element(f'{{{self._nsmap["svrl"]}}}schematron-output', attrib=final_attributes, nsmap=self._nsmap)

        for text_node in schematron_output.texts:
            root.append(self.visit(text_node))

        for ns_prefix in schematron_output.ns_prefix_in_attribute_values:
            root.append(self.visit(ns_prefix))

        if schematron_output.metadata:
            root.append(self.visit(schematron_output.metadata))

        for validation_event in schematron_output.validation_events:
            el = self.visit(validation_event)
            if el is not None:
                root.append(el)

        return root

    def _process_ns_prefix_node(self, ns_prefix: NSPrefixInAttributeValues) -> _Element:
        """Process the namespace prefix node.

        Args:
            ns_prefix: the prefix node to render into an XML element

        Returns:
            The created XML element
        """
        return Element(f'{{{self._nsmap["svrl"]}}}ns-prefix-in-attribute-values',
                       attrib={'prefix': ns_prefix.prefix, 'uri': ns_prefix.uri},
                       nsmap=self._nsmap)

    def _process_metadata(self, metadata: MetaData) -> _Element:
        """Process the metadata node.

        Args:
            metadata: the metadata node

        Returns:
            The created XML node
        """
        additional_namespaces = {}
        for namespace in metadata.namespaces:
            additional_namespaces[namespace.prefix] = namespace.uri

        metadata_root = Element(f'{{{self._nsmap["svrl"]}}}metadata', nsmap=self._nsmap | additional_namespaces)
        for element in metadata.xml_elements:
            metadata_root.append(element)

        return metadata_root

    def _process_active_pattern_node(self, active_pattern: ActivePattern) -> _Element:
        """Process an active pattern node.

        Args:
            active_pattern: The active pattern node

        Returns:
            The created XML document
        """
        node_attributes = {
            'documents': ' '.join(active_pattern.documents) if active_pattern.documents else None,
            'id': active_pattern.id,
            'name': active_pattern.name,
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        return Element(f'{{{self._nsmap["svrl"]}}}active-pattern', attrib=final_attributes, nsmap=self._nsmap)

    def _process_text_node(self, text: Text) -> _Element:
        """Process a text node.

        Args:
            text: the text node to convert into an element.

        Returns:
            The created XML element
        """
        node_attributes = {
            'fpi': text.fpi,
            'icon': text.icon,
            'see': text.see,
            'class': text.class_,
            'id': text.id,
            '{http://www.w3.org/XML/1998/namespace}lang': text.xml_lang,
            '{http://www.w3.org/XML/1998/namespace}space': text.xml_space,
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        text_element = Element(f'{{{self._nsmap["svrl"]}}}text', attrib=final_attributes, nsmap=self._nsmap)
        text_element.text = text.content
        return text_element
