############
PySchematron
############
This is a library for Schematron validation in Python.

Schematron is a formal schema language used to validate XML documents.
A Schematron schema is defined as an XML containing various assertions used to validate an XML document.
If the XML you wish to validate passes all the Schematron assertions,
your XML is considered valid according to the Schematron schema.

There are various versions of Schematron available.
This library only supports the latest version of Schematron, `ISO/IEC 19757-3:2020 <https://www.iso.org/standard/74515.html>`_, although with a few limitations (see below).

Currently, this library only supports a pure Python mode of Schematron validation.
In this pure Python mode we load the Schematron into an internal representation and apply that on an XML.
The advantage of direct evaluation is that it offers superior performance compared to an XSLT
transformation based evaluation.
The disadvantage is that it only supports XPath expressions and does not support XSLT functions.

In the future we hope to expand this library with an XSLT transformation based processing.
Unfortunately XSLT transformations require an XSLT processor,
which is currently not available in Python for XSLT >= 2.0.

A few similar packages to this software in other languages are `node-schematron <https://github.com/wvbe/node-schematron#readme>`_ in Javascript, and
`ph-schematron <http://phax.github.io/ph-schematron/>`_ in Java.

For all XPath expressions this package uses the `elementpath <https://github.com/sissaschool/elementpath>`_ library supporting XPath 1.0, 2.0 and 3.0 selectors.

**********
Python API
**********
To use the Python API, install the project like any other Python project, e.g. using `pip install pyschematron`.

After that you can use:

.. code:: python

    from pyschematron import PySchematron

todo
...


**********************
Command Line Interface
**********************

todo
...


*************
Functionality
*************
This library offers a basic implementation of Schematron using a pure Python "direct mode" evaluation method.

Direct mode evaluation
======================
The direct mode evaluation allows for basic validity checks using all XPath functionality of Schematron.

When applied to a document, the direct mode evaluation follows this procedure to validate a document:

#. Read in the Schematron from either a document or a string.
   In this phase the document is loaded into an AST (abstract syntax tree).
   All `<includes />` are resolved and inlined into the AST.
   All `<extends />` are loaded but not fully resolved at this stage.
#. Recreate the AST without abstract patterns and rules.
   In this phase we process the AST to create a concrete set of patterns and rules.
   All `<extends />` are resolved, abstract patterns are instantiated
   and redundant abstract rules and patterns are removed.
#. Determine the query binding language to use.
   This library only supports `xslt`, `xslt2`, `xslt3`, `xpath`, `xpath2`, `xpath3`, and `xpath31`,
   where all `xslt` variations are limited to XPath expressions only.
#. Bind the Schematron to the chosen phase and query binding language.
   We select only the patterns to evaluate and pre-compile the corresponding XPath expressions.
#. Apply the bound schema to an XML document to validate.


Custom functions
----------------
In direct mode evaluation, custom XSLT functions in your Schematron (`<xsl:function>`) are not supported.
Custom Python functions are also not supported due to a lack of support in the elementpath library (as of Jan. 2023).


Compliance
----------
The direct mode evaluation supports most of the `ISO/IEC 19757-3:2020 <https://www.iso.org/standard/74515.html>`_ standard, with a few exceptions.
All Schematron specific elements are supported, except for XSLT elements.

In terms of attributes, the `@documents` attribute of the `<assert />` tag is not supported.
Furthermore, `@icon`, `@see`, `@fpi`, `@flag`, and `@role` are loaded but not used.

