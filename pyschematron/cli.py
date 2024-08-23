__author__ = 'Robbert Harms'
__date__ = '2024-04-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from pathlib import Path

import typer

from pyschematron import validate_documents, validate_document

app = typer.Typer(no_args_is_help=True, pretty_exceptions_enable=False)


@app.command(help='Validate one or more documents using PySchematron.')
def validate(xml_documents: list[Path] = typer.Argument(help='One or more documents to validate.',
                                                        exists=True, file_okay=True, dir_okay=False, resolve_path=True),
             schema: Path = typer.Argument(help='The Schematron Schema to use for the validation.',
                                           exists=True, file_okay=True, dir_okay=False, resolve_path=True),
             phase: str = typer.Option('#DEFAULT', '--phase', '-p', help='The Schematron phase to use.'),
             svrl_out: Path = typer.Option(None, '--svrl-out',
                                           help='The file to write the SVRL to. '
                                                'For multiple documents we append the XML document name to this name.',
                                           file_okay=True, dir_okay=False, writable=True)):

    if svrl_out:
        svrl_out.parent.mkdir(parents=True, exist_ok=True)

    if len(xml_documents) == 1:
        result = validate_document(xml_documents[0], schema, phase=phase)

        print(xml_documents[0], 'VALID' if result.is_valid() else 'INVALID')

        if svrl_out:
            result.get_svrl().write(str(svrl_out), pretty_print=True, xml_declaration=True, encoding="utf-8")
    else:
        results = validate_documents(xml_documents, schema, phase=phase)

        for filename, result in zip(xml_documents, results):
            print(filename, 'VALID' if result.is_valid() else 'INVALID')

            if svrl_out:
                out_fname = svrl_out.with_stem(svrl_out.stem + '_' + Path(filename).stem)
                result.get_svrl().write(str(out_fname), pretty_print=True, xml_declaration=True, encoding="utf-8")
