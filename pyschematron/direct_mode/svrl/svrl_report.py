__author__ = 'Robbert Harms'
__date__ = '2023-04-24'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'

from abc import ABCMeta, abstractmethod

from lxml import etree
from lxml.etree import ElementTree, Element

from pyschematron.direct_mode.validators.validation_results import XMLDocumentValidationResult


class SVRLReportBuilder(metaclass=ABCMeta):

    @abstractmethod
    def create_svrl(self, validation_result: XMLDocumentValidationResult) -> ElementTree:
        """Create a Schematron Validation Reporting Language (SVRL) document of the validation results.

        This transforms the validation results into an XML document in the SVRL namespace.

        Args:
            validation_result: the result of validating the document using the validator of this package.

        Returns:
            An XML document in the SVRL namespace.
        """


class DefaultSVRLReportBuilder(SVRLReportBuilder):

    def create_svrl(self, validation_result: XMLDocumentValidationResult) -> ElementTree:
        processed_patterns = {}
        for node_result in validation_result.node_results:
            for pattern_result in node_result.pattern_results:
                rules_processed = processed_patterns.setdefault(pattern_result.pattern, [])

                if pattern_result.has_fired_rule():
                    for rule_result in pattern_result.rule_results:
                        rules_processed.append(rule_result)
                        # rule_results = rules_processed.setdefault(rule_result.rule, [])
                        # rule_results.append((node_result, pattern_result, rule_result))

        nsmap = {
            'svrl': 'http://purl.oclc.org/dsdl/svrl',
            'sch': 'http://purl.oclc.org/dsdl/schematron',
            'xs': 'http://www.w3.org/2001/XMLSchema'
        }

        # xmlns: svrl = "http://purl.oclc.org/dsdl/svrl"
        # xmlns: c = "http://www.amazing-cargo.com/xml/data/2023"
        # xmlns: error = "https://doi.org/10.5281/zenodo.1495494#error"
        # xmlns: rdf = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        # xmlns: sch = "http://purl.oclc.org/dsdl/schematron"
        # xmlns: schxslt = "https://doi.org/10.5281/zenodo.1495494"
        # xmlns: schxslt - api = "https://doi.org/10.5281/zenodo.1495494#api"
        # xmlns: xs = "http://www.w3.org/2001/XMLSchema"
        # schemaVersion = "iso"
        # title = "Cargo checking"

        # element = etree.Element(etree.QName("http://purl.oclc.org/dsdl/svrl", "duration"))
        # print(etree.tostring(element).decode("utf-8"))

        root = etree.Element(f'{{{nsmap["svrl"]}}}schematron-output', attrib={'schemaVersion': 'iso'}, nsmap=nsmap)
        root.append(etree.Element("child1", nsmap=nsmap))
        child2 = etree.SubElement(root, "{http://purl.oclc.org/dsdl/schematron}child2", nsmap=nsmap)
        child3 = etree.SubElement(root, "{http://purl.oclc.org/dsdl/svrl}child3", nsmap=nsmap)
        print(etree.tostring(root).decode())

        return

        for pattern, rules_processed in processed_patterns.items():
            print(f'Active pattern: {pattern.id}')

            for rule_processed in rules_processed:
                if rule_processed.is_fired():
                    print('Fired', rule_processed.rule.context)
                    for check_result in rule_processed.check_results:
                        if not check_result.check_result:
                            print('Failed check')

                if rule_processed.is_suppressed():
                    print('Suppressed', rule_processed.rule.context)

            # for rule, info in rules_processed.items():
            #     print(rule.context)

