#################
Python Schematron
#################
Schematron validation in Python.
This currently only supports the "direct" mode of Schematron validation by iterating over the
assertions and building a report directly using the Schematron.
This is contrast to XSLT transformations which require a XSLT processor which is not available in Python for XSLT >= 2.0.

The use-case of this library is very similar to `node-schematron <https://github.com/wvbe/node-schematron#readme>`_ which is a similar package for Javascript.
This package borrows some of the ideas and unit tests said package.

For the XPath selectors this package uses the `elementpath <https://github.com/sissaschool/elementpath>`_ library supporting XPath 1.0, 2.0 and 3.0 selectors.

**********
Python API
**********
To use the Python API, install the project like any other Python project, e.g. using `pip install pyschematron`.

After that you can use:

.. code:: python

    from pyschematron import PySchematron


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
Custom XSLT functions in the Schematron (`<xsl:function>`) are not supported.
You can however define your own XPath functions using the Python API:

todo
...


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

