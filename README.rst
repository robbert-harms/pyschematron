############
PySchematron
############
This is a library for Schematron validation in Python.

Currently, this library only supports a pure Python mode of Schematron validation.
In this pure Python mode we load the Schematron into an internal representation and apply that on an XML.
This pure Python mode unfortunately only support XPath expressions and does not support XSLT functions.

In the future we hope to expand this library with an XSLT transformation based processing.
Unfortunately XSLT transformations require an XSLT processor, which is currently not available in Python for XSLT >= 2.0.

At the moment, this library implements the `ISO/IEC 19757-3:2020 <https://www.iso.org/standard/74515.html>`_ version of Schematron.

The use-case of this library is very similar to `node-schematron <https://github.com/wvbe/node-schematron#readme>`_ which is a similar package for Javascript.

For the XPath selectors this package uses the `elementpath <https://github.com/sissaschool/elementpath>`_ library supporting XPath 1.0, 2.0 and 3.0 selectors.

**********
Python API
**********
To use the Python API, install the project like any other Python project, e.g. using `pip install pyschematron`.

After that you can use:

.. code:: python

    from pyschematron import PySchematron

todo
....


**********************
Command Line Interface
**********************

todo
...


*************
Functionality
*************

Custom functions
================
Custom XSLT functions in your Schematron (`<xsl:function>`) are currently not supported.
In addition, custom Python functions are also not supported due to a lack of support in the elementpath library.


Compliance
==========
For all other features, please check out the table below.
This table follows the order of the `ISO/IEC 19757-3 2016 <./docs/c055982_ISO_IEC_19757-3_2016.pdf>`_
allowing you to assert which of the specifications you can expect in this package.
If anything does not behave in the way it should, please file an issue or support request.

======= ================ ==============
Section Element            Status
======= ================ ==============
5.4.1   `<active />`   Tests OK
5.4.2   `<assert />`   Tests OK
5.4.3   `<extends />`  Not on roadmap
5.4.4   `<include />`  Not on roadmap
5.4.5   `<let />`      Tests OK
5.4.6   `<name />`     Tests OK
5.4.7   `<ns />`       Experimental
5.4.8   `<param />`    Tests OK
5.4.9   `<pattern />`  Tests OK
5.4.10  `<phase />`    Tests OK
5.4.11  `<report />`   Tests OK
5.4.12  `<rule />`     Tests OK
5.4.13  `<schema />`   Tests OK
5.4.14  `<value-of />` Tests OK
======= ================ ==============

For the other elements, unsupported are the `title`, `p` and `emph` elements.

For the attributes, unsupported are `@abstract`, `@diagnostics`, `@icon`,
`@see`, `@fpi`, `@flag`, `@role` and `@subject`.

