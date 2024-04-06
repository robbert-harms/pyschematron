__author__ = 'Robbert Harms'
__date__ = '2023-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod

from lxml.etree import Element, SubElement, ElementTree, _ElementTree

from datetime import datetime

from pyschematron import __version__
from pyschematron.direct_mode.schematron.ast import Assert, Namespace, ConcretePattern
from pyschematron.direct_mode.svrl.ast import ActivePattern, FiredRule, SchematronQuery, FailedAssert, \
    XPathExpression, Text, SchematronOutput, SuccessfulReport, SuppressedRule, NSPrefixInAttributeValues, MetaData, \
    CheckResult, ValidationEvent, PropertyReference, DiagnosticReference

from pyschematron.direct_mode.svrl.xml_writer import LxmlSVRLWriter
from pyschematron.direct_mode.xml_validation.results.validation_results import (XMLDocumentValidationResult, RuleResult,
                                                                                FiredRuleResult, SuppressedRuleResult,
                                                                                PropertyResult, DiagnosticResult)


class SVRLReportBuilder(metaclass=ABCMeta):

    @abstractmethod
    def create_svrl_xml(self, validation_result: XMLDocumentValidationResult) -> _ElementTree:
        """Create a Schematron Validation Reporting Language (SVRL) document of the validation results.

        This transforms the validation results into an XML document in the SVRL namespace.

        Args:
            validation_result: the result of validating the document using the validator of this package.

        Returns:
            An XML document in the SVRL namespace.
        """


class DefaultSVRLReportBuilder(SVRLReportBuilder):
    """Converts the validation results into an SVRL AST.

    In the SVRL report we want to enumerate the processing results in the format:
        <active-pattern/>
        ...
        <rule results>
        ...
        <active-pattern/>
        ...

    The results of using the validator provides results for every XML node, Schematron pattern and Schematron rule
    checked. This is too comprehensive for the SVRL and as such this class simplifies the results.
    """

    def create_svrl_xml(self, validation_result: XMLDocumentValidationResult) -> _ElementTree:
        title = None
        if title_node := validation_result.schema_information.schema.title:
            title = title_node.content

        svrl = SchematronOutput(
            self._get_text_nodes(validation_result),
            self._get_ns_prefix_nodes(validation_result),
            tuple(self.get_validation_events(validation_result)),
            metadata=self._get_metadata(validation_result),
            phase=validation_result.schema_information.phase,
            schema_version=validation_result.schema_information.schema.schema_version,
            title=title)

        writer = LxmlSVRLWriter()
        return ElementTree(writer.create_xml(svrl))

    def get_validation_events(self, validation_result: XMLDocumentValidationResult) -> list[ValidationEvent]:
        """Extract a list of SVRL validation events from the validation results.

        Args:
            validation_result: The validation results from the validator

        Returns:
            A list of SVRL validation events (active pattern, fired rule, failed assert,
            successful report, suppressed rule).
        """
        root_document = None
        if xml_document := validation_result.xml_information.xml_document:
            if docinfo := xml_document.docinfo:
                root_document = docinfo.URL

        processed_patterns = self._get_rule_results_by_pattern(validation_result)
        validation_events = []
        for pattern, rules_processed in processed_patterns.items():
            name = pattern.title.content if pattern.title else None
            validation_events.append(ActivePattern(id=pattern.id, name=name, documents=(root_document,)))

            for rule_processed in rules_processed:
                if isinstance(rule_processed, FiredRuleResult):
                    validation_events.append(FiredRule(SchematronQuery(rule_processed.rule.context.query),
                                                       id=rule_processed.rule.id))
                    validation_events += self._get_svrl_check_results(rule_processed)
                elif isinstance(rule_processed, SuppressedRuleResult):
                    validation_events.append(SuppressedRule(SchematronQuery(rule_processed.rule.context.query)))
        return validation_events

    def _get_svrl_check_results(self, fired_rule: FiredRuleResult) -> list[CheckResult]:
        """Transform the validation checks in the fired rule to a list of SVRL AST check results.

        Args:
            fired_rule: the rule which was fired, from this we will return the checks which did not succeed.

        Returns:
            A list of failed asserts or successful reports.
        """
        subject_location = None
        if fired_rule.subject_node:
            subject_location = XPathExpression(fired_rule.subject_node.xpath_location)

        events = []
        for check_result in fired_rule.check_results:
            if check_result.check_result:
                if check_result.subject_node:
                    subject_location = XPathExpression(check_result.subject_node.xpath_location)

                property_references = self._get_property_references(check_result.property_results)
                diagnostic_references = self._get_diagnostic_reference(check_result.diagnostic_results)

                if isinstance(check_result.check, Assert):
                    event = FailedAssert(Text(check_result.text),
                                         XPathExpression(check_result.xml_node.xpath_location),
                                         SchematronQuery(check_result.check.test.query),
                                         diagnostic_references=tuple(diagnostic_references),
                                         property_references=tuple(property_references),
                                         subject_location=subject_location)
                else:
                    event = SuccessfulReport(Text(check_result.text),
                                             XPathExpression(check_result.xml_node.xpath_location),
                                             SchematronQuery(check_result.check.test.query),
                                             diagnostic_references=tuple(diagnostic_references),
                                             property_references=tuple(property_references),
                                             subject_location=subject_location)
                events.append(event)
        return events

    @staticmethod
    def _get_property_references(property_results: list[PropertyResult] | None) -> list[PropertyReference]:
        """Convert the property results to SVRL property reference nodes.

        Args:
            property_results: the list of property results, may be None, in which case we return an empty list.

        Returns:
            The list of property references.
        """
        property_references = []
        if property_results:
            for property_result in property_results:
                property_references.append(PropertyReference(
                    Text(property_result.text), property_result.property_id,
                    property_result.role, property_result.scheme))
        return property_references

    @staticmethod
    def _get_diagnostic_reference(diagnostic_results: list[DiagnosticResult] | None) -> list[DiagnosticReference]:
        """Convert the diagnostic results to SVRL diagnostic reference nodes.

        Args:
            diagnostic_results: the list of diagnostic results, may be None, in which case we return an empty list.

        Returns:
            The list of diagnostic references.
        """
        diagnostic_references = []
        if diagnostic_results:
            for diagnostic_result in diagnostic_results:
                text = Text(diagnostic_result.text,
                            xml_lang=diagnostic_result.xml_lang,
                            xml_space=diagnostic_result.xml_space)
                diagnostic_references.append(DiagnosticReference(text, diagnostic=diagnostic_result.diagnostic_id))
        return diagnostic_references

    @staticmethod
    def _get_rule_results_by_pattern(
            validation_result: XMLDocumentValidationResult) -> dict[ConcretePattern, list[RuleResult]]:
        """Reduce the validation results into a dictionary indexed by pattern.

        The validation results consist of data for each XML node, Schematron pattern and Schematron rule. This function
        iterates over the validation results and groups them by Schematron pattern.

        Args:
            validation_result: the validation results

        Returns:
            A dictionary which as indices the patterns which had at least one fired rule. As values are the
            rule results taken from the validation results.
        """
        processed_patterns = {}
        for node_result in validation_result.node_results:
            for pattern_result in node_result.pattern_results:
                rules_processed = processed_patterns.setdefault(pattern_result.pattern, [])

                if pattern_result.has_fired_rule():
                    for rule_result in pattern_result.rule_results:
                        rules_processed.append(rule_result)
        return processed_patterns

    @staticmethod
    def _get_text_nodes(validation_result: XMLDocumentValidationResult) -> tuple[Text, ...]:
        """Get the listing of text nodes we will add to the SVRL output.

        For the text nodes we will use all the paragraph nodes present in the Schematron document.

        Args:
            validation_result: all the validation information

        Returns:
            The text nodes, created from the paragraphs of the Schematron document.
        """
        texts = []
        for paragraph in validation_result.schema_information.schema.paragraphs:
            texts.append(Text(paragraph.content, icon=paragraph.icon,
                              xml_lang=paragraph.xml_lang, id=paragraph.id,
                              class_=paragraph.class_))
        return tuple(texts)

    @staticmethod
    def _get_ns_prefix_nodes(validation_result: XMLDocumentValidationResult) -> tuple[NSPrefixInAttributeValues, ...]:
        """Get the listing of the ns prefix nodes.

        Args:
            validation_result: all the validation information

        Returns:
            The NS prefix nodes.
        """
        ns_prefix_in_attribute_values = []
        for schematron_namespace in validation_result.schema_information.schema.namespaces:
            ns_prefix_in_attribute_values.append(NSPrefixInAttributeValues(schematron_namespace.prefix,
                                                                           schematron_namespace.uri))
        return tuple(ns_prefix_in_attribute_values)

    @staticmethod
    def _get_metadata(validation_result: XMLDocumentValidationResult) -> MetaData:
        """Get the metadata node to add to the SVRL.

        Args:
            validation_result: all the validation information

        Returns:
            The metadata node.
        """
        namespaces = (Namespace('dct', 'http://purl.org/dc/terms/'),
                      Namespace('skos', 'http://www.w3.org/2004/02/skos/core#'),
                      Namespace('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
                      Namespace('pysch', 'https://github.com/robbert-harms/pyschematron'))

        nsmap = {ns.prefix: ns.uri for ns in namespaces}
        create_time = datetime.now().astimezone()

        def creator_element():
            creator = Element(f'{{{nsmap["dct"]}}}creator', nsmap=nsmap)
            agent = SubElement(creator, f'{{{nsmap["dct"]}}}agent')
            pref_label = SubElement(agent, f'{{{nsmap["skos"]}}}prefLabel')
            pref_label.text = f'PySchematron {__version__}'
            return creator

        def created_element():
            created = Element(f'{{{nsmap["dct"]}}}created', nsmap=nsmap)
            created.text = create_time.isoformat()
            return created

        def source_element():
            source = Element(f'{{{nsmap["dct"]}}}source', nsmap=nsmap)
            description = SubElement(source, f'{{{nsmap["rdf"]}}}Description')
            creator = SubElement(description, f'{{{nsmap["dct"]}}}creator')
            agent = SubElement(creator, f'{{{nsmap["dct"]}}}Agent')
            pref_label = SubElement(agent, f'{{{nsmap["skos"]}}}prefLabel')
            pref_label.text = f'PySchematron {__version__}'
            description.append(created_element())
            return source

        return MetaData((creator_element(), created_element(), source_element()), namespaces)
