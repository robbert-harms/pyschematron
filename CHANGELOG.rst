*********
Changelog
*********


Version 1.1.17 (2026-05-19)
===========================

Other
-----
- Adds warnings when the input Schematron files are invalid. Fixes issue #17.
- Fixes issue #18 in which expressions in let bindings are evaluated in wrong context.



Version 1.1.16 (2026-05-19)
===========================

Other
-----
- Fixes issue #16 in which comments at the end of the Schematron XML led to incorrect loading of the Schematron XML.



Version 1.1.15 (2026-05-15)
===========================

Bug Fixes
---------
- Enable Schematron evaluation on the document node. This should address pyschematron #15 in which the context '/' was not properly activated.



Version 1.1.14 (2026-05-06)
===========================

Other
-----
- Adds the id tag to failed-assert and successfull-report nodes in the SVRL output.



Version 1.1.13 (2025-11-05)
===========================

Other
-----
- Updated default parser in load_xml_document, this improves parallel processing speed according to the documentation of XMLParser.



Version 1.1.12 (2025-11-04)
===========================

Features
--------
- The function load_xml_document now accepts a parser instance for flexibility.
- The XML Schematron writer now allows overriding the default nsmap namespace.



Version 1.1.11 (2025-09-24)
===========================

Other
-----
- Updated typer dependency and removed the all limiter.



Version 1.1.10 (2025-09-21)
===========================

Other
-----
- Relaxed the version constraint on lxml.



Version 1.1.9 (2025-09-18)
==========================

Other
-----
- Updated xmlschema, elementpath and lxml dependencies.



Version 1.1.8 (2025-03-26)
==========================

Features
--------
- Adds Schematron base path to the function API interface.

Documentation
-------------
- Updated editorconfig



Version 1.1.7 (2025-02-19)
==========================

Miscellaneous Tasks
-------------------
- *(deps\)* Updated all the dependencies.


Version 1.1.6 (2025-01-31)
==========================

Other
-----
- Replaced gitchangelog with git-cliff.


Version 1.1.5 (2025-01-22)
==========================

Added
-----
- Adds PyPi Homepage url.

Fixed
-----
- Fixes bug #7.


Version 1.1.4 (2024-12-23)
==========================

Other
-----
- Made the assert and report checks more robust for queries not returning a single boolean. This fixes the second part of issue #6.

Version 1.1.3 (2024-12-21)
==========================

Other
-----
- Made rich text evaluation more robust for complex results.


Version 1.1.2 (2024-12-20)
==========================

Other
-----
- Bumped required elementpath version to fix bug #6.


Version 1.1.1 (2024-11-27)
==========================

Other
-----
- Updated is_valid comment in the API.


Version 1.1.0 (2024-11-27)
==========================

Other
-----
- Fixes github bug #5. The reporting of the is_valid method was reversed with regard to assert/report.
- Fixed the documentation regarding the is_valid function.


Version 1.0.3 (2024-10-29)
==========================

Other
-----
- Updated elementpath dependency version.


Version 1.0.2 (2024-10-18)
==========================

Other
-----
- Updated readme to include supported Python version and other textual changes.
- Updated lxml dependency from 5.1.0 to 5.2.1


Version 1.0.1 (2024-09-24)
==========================

Other
-----
- Upgraded to elementpath==4.5.0
- Fixed email address in info blocks.


Version 1.0.0 (2024-08-23)
==========================

Other
-----
First complete version of PySchematron. See the readme for the functionality and limitations.


Version 0.1.0 (2022-09-12)
==========================

Other
-----
- First version



