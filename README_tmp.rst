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
.. code:: js

   const { Schema } = require('node-schematron');

   const schema = Schema.fromString(`<schema xmlns="http://purl.oclc.org/dsdl/schematron">
       <pattern>
           <rule context="thunder">
               <let name="lightning"/>
               <report test="$lightning/@foo = 'bar'">
                   Skeet boop <value-of select="$lightning/@foo" />
               </report>
           </rule>
       </pattern>
   </schema>`);

   const results = schema.validateString(
       `<xml foo="err">
       <thunder foo="bar" />
   </xml>`,
       { debug: true }
   );

   // results === [
   //   {
   //      isReport: true,
   //      context: <thunder foo="bar" />,
   //      message: '\n\t\t\t\tSkeet boop bar\n\t\t\t'
   //   }
   // ]


**********************
Command Line Interface
**********************

To use as a command in your terminal, install globally like:
``npm install -g node-schematron``. Alternatively, you can use ``npx``
to run it.

The ``node-schematron`` command has two parameters, the last one of
which is optional:

1. ``schematronLocation``, required, an absolute path or relative
   reference to your schematron XML. For example ``my-schema.sch``.
2. ``globPattern``, optional, a globbing pattern for documents. For
   example ``*.{xml,dita}`` (all .xml and .dita files). Defaults to
   ``*.xml`` (all .xml files in the current working directory).

.. code:: sh

   /Users/Wybe/Docs/schematron-test:
     node-schematron my-schema.sch
     # Gives the results for all "*.xml" files in this directory

.. code:: sh

   /Users/Wybe/Docs/schematron-test:
     node-schematron my-schema "docs/**/*.xml"
     # Gives the results for all "*.xml" files in the docs/ directory and all subdirectories

Besides that you can give it a fair amount of options:

+---+---+----------------------------------------------------------------+
| L | S | Description                                                    |
| o | h |                                                                |
| n | o |                                                                |
| g | r |                                                                |
| n | t |                                                                |
| a |   |                                                                |
| m |   |                                                                |
| e |   |                                                                |
+===+===+================================================================+
| ` | ` | The reporter(s) to use. Zero or many of ``npm`` or ``xunit``,  |
| ` | ` | space separated.                                               |
| - | - |                                                                |
| - | r |                                                                |
| r | ` |                                                                |
| e | ` |                                                                |
| p |   |                                                                |
| o |   |                                                                |
| r |   |                                                                |
| t |   |                                                                |
| e |   |                                                                |
| r |   |                                                                |
| s |   |                                                                |
| ` |   |                                                                |
| ` |   |                                                                |
+---+---+----------------------------------------------------------------+
| ` | ` | Do not exit process with an error code if at least one         |
| ` | ` | document fails a schematron assertion.                         |
| - | - |                                                                |
| - | o |                                                                |
| o | ` |                                                                |
| k | ` |                                                                |
| ` |   |                                                                |
| ` |   |                                                                |
+---+---+----------------------------------------------------------------+
| ` | ` | Display extra stack trace information in case of XPath errors  |
| ` | ` |                                                                |
| - | - |                                                                |
| - | D |                                                                |
| d | ` |                                                                |
| e | ` |                                                                |
| b |   |                                                                |
| u |   |                                                                |
| g |   |                                                                |
| ` |   |                                                                |
| ` |   |                                                                |
+---+---+----------------------------------------------------------------+
| ` | ` | A list of files, in case you can’t use the globbing parameter. |
| ` | ` |                                                                |
| - | - |                                                                |
| - | f |                                                                |
| f | ` |                                                                |
| i | ` |                                                                |
| l |   |                                                                |
| e |   |                                                                |
| s |   |                                                                |
| ` |   |                                                                |
| ` |   |                                                                |
+---+---+----------------------------------------------------------------+
| ` | ` | The number of documents to handle before opening the next      |
| ` | ` | child process. Defaults to ``5000``.                           |
| - | - |                                                                |
| - | b |                                                                |
| b | ` |                                                                |
| a | ` |                                                                |
| t |   |                                                                |
| c |   |                                                                |
| h |   |                                                                |
| ` |   |                                                                |
| ` |   |                                                                |
+---+---+----------------------------------------------------------------+
| ` | ` | The schematron phase to run. Defaults to ``#DEFAULT`` (which   |
| ` | ` | means the ``@defaultPhase`` value or ``#ALL``.                 |
| - | - |                                                                |
| - | p |                                                                |
| p | ` |                                                                |
| h | ` |                                                                |
| a |   |                                                                |
| s |   |                                                                |
| e |   |                                                                |
| ` |   |                                                                |
| ` |   |                                                                |
+---+---+----------------------------------------------------------------+
| ` | ` | The amount of stuff to log. Only used if ``-r`` includes       |
| ` | ` | ``npm``. Value must be one of ``silly``, ``info``, ``report``, |
| - | - | ``pass``, ``assert``, ``fail``, ``fileError`` or ``error``.    |
| - | l | Defaults to ``info``.                                          |
| l | ` |                                                                |
| o | ` |                                                                |
| g |   |                                                                |
| - |   |                                                                |
| l |   |                                                                |
| e |   |                                                                |
| v |   |                                                                |
| e |   |                                                                |
| l |   |                                                                |
| ` |   |                                                                |
| ` |   |                                                                |
+---+---+----------------------------------------------------------------+

.. code:: sh

   /Users/Wybe/Docs/schematron-test:
     node-schematron my-schema.sch "**/*.xml" --phase publication --log-level fail
     # Validates the "publication" phase and logs only the paths of documents that fail

.. code:: sh

   /Users/Wybe/Docs/schematron-test:
     node-schematron my-schema.sch "**/*.xml" -r xunit > test-reports/test-report.xml
     # Validates the "publication" phase and writes an XUnit XML report to file


*************
Functionality
*************

Custom functions
----------------

XSLT functions (``<xsl:function>``) are not supported. There is a
feature branch (``xslt-functions``) with a naive implementation that
unfortunately got stuck. More about that problem in `this closing
comment in a related
ticket <https://github.com/wvbe/node-schematron/issues/1#issuecomment-873554478>`__.

To define custom XPath functions via Javascript, import
``registerCustomXPathFunction``:

.. code:: js

   const { registerCustomXPathFunction } = require('node-schematron');

   registerCustomXPathFunction(
       {
           localName: 'is-foo',
           namespaceURI: 'http://example.com'
       },
       ['xs:string?'],
       'xs:boolean',
       (domFacade, input) => input === 'foo'
   );

The ``registerCustomXPathFunction`` is an alias for the same function in
``fontoxpath``. See the `fontoxpath “global functions”
documentation <https://github.com/FontoXML/fontoxpath#global-functions>`__
for more information.

Compliance
----------

As for features, check out the unit tests in ``test/``. I’ve mirrored
them to the text of `ISO/IEC 19757-3
2016 <./docs/c055982_ISO_IEC_19757-3_2016.pdf>`__ in order to clearly
assert how far ``node-schematron`` is up to spec. I’ve also noticed
there’s different ways you can read that text, so please file an issue
if you feel ``node-schematron`` behaves in a non-standard or buggy way.

======= ================ ==============
Section Thing            Status
======= ================ ==============
5.4.1   ``<active />``   Tests OK
5.4.1   ``<active />``   Tests OK
5.4.2   ``<assert />``   Tests OK
5.4.3   ``<extends />``  Not on roadmap
5.4.4   ``<include />``  Not on roadmap
5.4.5   ``<let />``      Tests OK
5.4.6   ``<name />``     Tests OK
5.4.7   ``<ns />``       Experimental
5.4.8   ``<param />``    Tests OK
5.4.9   ``<pattern />``  Tests OK
5.4.10  ``<phase />``    Tests OK
5.4.11  ``<report />``   Tests OK
5.4.12  ``<rule />``     Tests OK
5.4.13  ``<schema />``   Tests OK
5.4.14  ``<value-of />`` Tests OK
======= ================ ==============

Not supported attributes are ``@abstract``, ``@diagnostics``, ``@icon``,
``@see``, ``@fpi``, ``@flag``, ``@role`` and ``@subject``.

Not supported elements

