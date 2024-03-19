__author__ = 'Robbert Harms'
__date__ = '2023-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod
from typing import override

from lxml.etree import _Element, Element

from datetime import datetime

from pyschematron.direct_mode.ast import Assert, Namespace
from pyschematron.direct_mode.svrl.svrl_ast import ActivePattern, FiredRule, SchematronQuery, FailedAssert, \
    XPathExpression, Text, SchematronOutput, SuccessfulReport, SuppressedRule, NSPrefixInAttributeValues, MetaData

from pyschematron.direct_mode.svrl.xml_writer import LxmlSVRLXMLWriter
from pyschematron.direct_mode.validators.validation_results import XMLDocumentValidationResult


class SVRLReportBuilder(metaclass=ABCMeta):

    @abstractmethod
    def create_svrl_xml(self, validation_result: XMLDocumentValidationResult) -> _Element:
        """Create a Schematron Validation Reporting Language (SVRL) document of the validation results.

        This transforms the validation results into an XML document in the SVRL namespace.

        Args:
            validation_result: the result of validating the document using the validator of this package.

        Returns:
            An XML document in the SVRL namespace.
        """


class DefaultSVRLReportBuilder(SVRLReportBuilder):

    @override
    def create_svrl_xml(self, validation_result: XMLDocumentValidationResult) -> _Element:
        schematron_output_svrl_root = self._construct_svrl_ast(validation_result)

        writer = LxmlSVRLXMLWriter()
        return writer.create_xml(schematron_output_svrl_root)

    def _construct_svrl_ast(self, validation_result: XMLDocumentValidationResult) -> SchematronOutput:
        root_document = None
        if xml_document := validation_result.xml_information.xml_document:
            if docinfo := xml_document.docinfo:
                root_document = docinfo.URL

        processed_patterns = {}
        for node_result in validation_result.node_results:
            for pattern_result in node_result.pattern_results:
                rules_processed = processed_patterns.setdefault(pattern_result.pattern, [])

                if pattern_result.has_fired_rule():
                    for rule_result in pattern_result.rule_results:
                        rules_processed.append(rule_result)

        validation_events = []
        for pattern, rules_processed in processed_patterns.items():
            name = pattern.title.content if pattern.title else None
            validation_events.append(ActivePattern(id=pattern.id, name=name, documents=(root_document,)))

            for rule_processed in rules_processed:
                if rule_processed.is_fired():
                    validation_events.append(FiredRule(SchematronQuery(rule_processed.rule.context.query)))

                    for check_result in rule_processed.check_results:
                        if not check_result.check_result:
                            if isinstance(check_result.check, Assert):
                                validation_events.append(FailedAssert(Text(''), XPathExpression(''), SchematronQuery('')))
                            else:
                                validation_events.append(
                                    SuccessfulReport(Text(''), XPathExpression(''), SchematronQuery('')))

                if rule_processed.is_suppressed():
                    validation_events.append(SuppressedRule(SchematronQuery(rule_processed.rule.context.query)))

        return SchematronOutput(self._get_text_nodes(validation_result),
                                self._get_ns_prefix_nodes(validation_result),
                                tuple(validation_events),
                                metadata=self._get_metadata(validation_result),
                                phase=validation_result.schema_information.phase,
                                schema_version=validation_result.schema_information.schema.schema_version,
                                title=validation_result.schema_information.schema.title.content)

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

        def get_creator():
            creator = Element(f'{{{nsmap["dct"]}}}creator', nsmap=nsmap)
            agent = Element(f'{{{nsmap["dct"]}}}agent', nsmap=nsmap)
            preflabel = Element(f'{{{nsmap["skos"]}}}prefLabel', nsmap=nsmap)
            preflabel.text = 'PySchematron'
            agent.append(preflabel)
            creator.append(agent)
            return creator

        def get_created():
            created = Element(f'{{{nsmap["dct"]}}}created', nsmap=nsmap)
            created.text = create_time.isoformat()
            return created

        def get_source():
            source = Element(f'{{{nsmap["dct"]}}}source', nsmap=nsmap)
            description = Element(f'{{{nsmap["rdf"]}}}Description', nsmap=nsmap)
            creator = Element(f'{{{nsmap["dct"]}}}creator', nsmap=nsmap)
            agent = Element(f'{{{nsmap["dct"]}}}Agent', nsmap=nsmap)
            preflabel = Element(f'{{{nsmap["skos"]}}}prefLabel', nsmap=nsmap)
            preflabel.text = 'PySchematron'
            agent.append(preflabel)
            creator.append(agent)
            description.append(creator)

            created = get_created()
            description.append(created)

            creator.append(agent)
            source.append(description)
            return source

        return MetaData((get_creator(), get_created(), get_source()), namespaces)
