__author__ = 'Robbert Harms'
__date__ = '2024-03-17'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta, abstractmethod
from typing import override

from lxml.etree import Element, _Element
from pyschematron.direct_mode.svrl.ast import SchematronOutput, SVRLNode, NSPrefixInAttributeValues, Text, \
    ActivePattern, MetaData, FiredRule, FailedAssert, SuppressedRule, SuccessfulReport, PropertyReference, \
    DiagnosticReference
from pyschematron.direct_mode.svrl.svrl_visitors import SVRLASTVisitor


class SVRLWriter(metaclass=ABCMeta):
    """Type class for SVRL XML writers."""

    @abstractmethod
    def create_xml(self, schematron_output: SchematronOutput) -> _Element:
        """Transform a Schematron output SVRL root node, to an XML element.

        Args:
            schematron_output: the root node of an SVRL AST.

        Returns:
            An XML representation of the provided SVRL output node.
        """


class LxmlSVRLWriter(SVRLWriter):
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
            case FiredRule():
                return self._process_fired_rule_node(svrl_node)
            case SuppressedRule():
                return self._process_suppressed_rule_node(svrl_node)
            case FailedAssert():
                return self._process_failed_assert(svrl_node)
            case SuccessfulReport():
                return self._process_successful_report(svrl_node)
            case Text():
                return self._process_text_node(svrl_node)
            case PropertyReference():
                return self._process_property_reference(svrl_node)
            case DiagnosticReference():
                return self._process_diagnostic_reference(svrl_node)
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
            The created XML element
        """
        documents = None
        if active_pattern.documents:
            documents = ' '.join([f'file:{doc}' for doc in active_pattern.documents])

        node_attributes = {
            'documents': documents,
            'id': active_pattern.id,
            'name': active_pattern.name,
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        return Element(f'{{{self._nsmap["svrl"]}}}active-pattern', attrib=final_attributes, nsmap=self._nsmap)

    def _process_fired_rule_node(self, fired_rule: FiredRule) -> _Element:
        """Process a fired rule node.

        Args:
            fired_rule: information on the fired rule

        Returns:
            The created XML element
        """
        document = None
        if fired_rule.document:
            document = f'file:{fired_rule.document}'

        node_attributes = {
            'context': fired_rule.context.query,
            'document': document,
            'flag': fired_rule.flag,
            'id': fired_rule.id,
            'name': fired_rule.name,
            'role': fired_rule.role
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        return Element(f'{{{self._nsmap["svrl"]}}}fired-rule', attrib=final_attributes, nsmap=self._nsmap)

    def _process_suppressed_rule_node(self, suppressed_rule: SuppressedRule) -> _Element:
        """Process a suppressed rule node

        Args:
            suppressed_rule: information on the suppressed rule

        Returns:
            The created XML element
        """
        node_attributes = {
            'context': suppressed_rule.context.query,
            'id': suppressed_rule.id,
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        return Element(f'{{{self._nsmap["svrl"]}}}suppressed-rule', attrib=final_attributes, nsmap=self._nsmap)

    def _process_failed_assert(self, failed_assert: FailedAssert) -> _Element:
        """Process a failed assert node.

        Args:
            failed_assert: the failed assert information

        Returns:
            The created XML element
        """
        return self._process_check_result(failed_assert)

    def _process_successful_report(self, successful_report: SuccessfulReport) -> _Element:
        """Process a successful report node.

        Args:
            successful_report: the successful report information

        Returns:
            The created XML element
        """
        return self._process_check_result(successful_report)

    def _process_check_result(self, check_result: FailedAssert | SuccessfulReport):
        """Process a check result.

        Depending on the type of input we return either a `successful-report` or a `failed-assert` element.

        Args:
            check_result: the check result.

        Returns:
            The created XML element
        """
        node_attributes = {
            'flag': check_result.flag,
            'id': check_result.id,
            'location': check_result.location.expression,
            'role': check_result.role,
            'test': check_result.test.query
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        if subject_location := check_result.subject_location:
            final_attributes['location'] = subject_location.expression

        node_name = 'successful-report'
        if isinstance(check_result, FailedAssert):
            node_name = 'failed-assert'

        report_element = Element(f'{{{self._nsmap["svrl"]}}}{node_name}',
                                 attrib=final_attributes, nsmap=self._nsmap)

        if check_result.diagnostic_references:
            for diagnostic_reference in check_result.diagnostic_references:
                report_element.append(self.visit(diagnostic_reference))

        if check_result.property_references:
            for property_reference in check_result.property_references:
                report_element.append(self.visit(property_reference))

        if check_result.text.content:
            report_element.append(self.visit(check_result.text))

        return report_element

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

    def _process_property_reference(self, property_reference: PropertyReference) -> _Element:
        """Process a property reference node.

        Args:
            property_reference: the property reference to convert into a node.

        Returns:
            The created XML element
        """
        node_attributes = {
            'property': property_reference.property,
            'role': property_reference.role,
            'scheme': property_reference.scheme
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        property_reference_element = Element(f'{{{self._nsmap["svrl"]}}}property-reference',
                                             attrib=final_attributes, nsmap=self._nsmap)

        if property_reference.text:
            property_reference_element.append(self.visit(property_reference.text))

        return property_reference_element

    def _process_diagnostic_reference(self, diagnostic_reference: DiagnosticReference) -> _Element:
        """Process a diagnostic reference node.

        Args:
            diagnostic_reference: the diagnostic reference to convert into a node.

        Returns:
            The created XML element
        """
        node_attributes = {
            'diagnostic': diagnostic_reference.diagnostic,
        }
        final_attributes = {k: v for k, v in node_attributes.items() if v is not None}

        diagnostic_reference_element = Element(f'{{{self._nsmap["svrl"]}}}diagnostic-reference',
                                               attrib=final_attributes, nsmap=self._nsmap)

        if diagnostic_reference.text:
            diagnostic_reference_element.append(self.visit(diagnostic_reference.text))

        return diagnostic_reference_element
